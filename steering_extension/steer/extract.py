"""Extract diff-of-means steering vectors from contrast prompts.

Input: contrast jsonl rows {"contrast": "E", "arm": "pos"|"neg", "cid": ..., "prompt": ..., "system_prompt": ""}.
For each row we generate a response (sampled, thinking off), then run one forward pass over
prompt+response and record the per-layer mean residual over response tokens (Persona Vectors
readout). Vector per layer = mean(pos) - mean(neg). Also stores per-layer RMS residual norm
(computed on the neg arm) for dose units, and K random directions with matched norm per layer.
Output: safetensors with keys `{contrast}/layer{L}`, `rand{k}/layer{L}`, `norm/layer{L}`,
plus a sidecar json with cosines and counts. Shardable like generate.py; merge with --merge.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

from steering_extension.steer.generate import append_jsonl, read_jsonl
from steering_extension.steer.hooks import ResidualCapture
from steering_extension.steer.model import chat_input_ids, load_model, strip_think


@torch.inference_mode()
def respond_and_capture(loaded, rows: list[dict], *, max_new_tokens: int, temperature: float):
    tok = loaded.tokenizer
    ids = [chat_input_ids(loaded, r.get("system_prompt", ""), r["prompt"]) for r in rows]
    enc = tok.pad({"input_ids": ids}, padding=True, return_tensors="pt").to(loaded.device)
    prompt_len = enc["input_ids"].shape[1]
    out = loaded.model.generate(**enc, do_sample=temperature > 0, temperature=temperature if temperature > 0 else None, top_p=1.0, top_k=0, max_new_tokens=max_new_tokens, pad_token_id=tok.pad_token_id)
    # response mask: generated, non-pad tokens
    gen = out[:, prompt_len:]
    resp_mask = (gen != tok.pad_token_id)
    full_mask = torch.cat([enc["attention_mask"].bool(), resp_mask], dim=1)
    cap_mask = torch.cat([torch.zeros_like(enc["attention_mask"], dtype=torch.float), resp_mask.float()], dim=1)
    with ResidualCapture(loaded.layers) as cap:
        cap.mask = cap_mask
        loaded.model(input_ids=out, attention_mask=full_mask.long())
    counts = resp_mask.sum(dim=1).float()
    texts = [strip_think(tok.decode(g, skip_special_tokens=True)) for g in gen]
    return cap, counts, texts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--contrasts", type=Path)
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--model", default=os.environ.get("STEER_MODEL", "Qwen/Qwen3.5-9B"))
    ap.add_argument("--max-new-tokens", type=int, default=300)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--num-shards", type=int, default=1)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--n-random", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20261010)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.merge:
        merge(args)
        return
    rows = read_jsonl(args.contrasts)
    rows = [r for i, r in enumerate(rows) if i % args.num_shards == args.shard]
    loaded = load_model(args.model)
    L, d = loaded.num_layers, loaded.hidden_size
    acc: dict[tuple[str, str], torch.Tensor] = {}
    sq: dict[tuple[str, str], torch.Tensor] = {}
    n_tok: dict[tuple[str, str], float] = {}
    n_resp: dict[tuple[str, str], int] = {}
    resp_log = args.out_dir / f"responses.shard{args.shard}.jsonl"
    rows.sort(key=lambda r: len(r["prompt"]))
    for i in range(0, len(rows), args.batch_size):
        batch = rows[i : i + args.batch_size]
        cap, counts, texts = respond_and_capture(loaded, batch, max_new_tokens=args.max_new_tokens, temperature=args.temperature)
        for j, r in enumerate(batch):
            key = (r["contrast"], r["arm"])
            if key not in acc:
                acc[key] = torch.zeros(L, d)
                sq[key] = torch.zeros(L)
                n_tok[key] = 0.0
                n_resp[key] = 0
            for l in range(L):
                acc[key][l] += cap.sums[l][j].cpu()
                sq[key][l] += cap.sq_norm_sums[l][j].cpu()
            n_tok[key] += float(counts[j].item())
            n_resp[key] += 1
        append_jsonl(resp_log, [{**r, "response": t, "response_tokens": int(c)} for r, t, c in zip(batch, texts, counts)])
        print(f"{i+len(batch)}/{len(rows)}", flush=True)
    tensors = {}
    meta = {}
    for key in acc:
        c, a = key
        tensors[f"sum/{c}/{a}"] = acc[key]
        tensors[f"sq/{c}/{a}"] = sq[key]
        meta[f"{c}/{a}"] = {"n_tokens": n_tok[key], "n_responses": n_resp[key]}
    save_file(tensors, str(args.out_dir / f"partial.shard{args.shard}.safetensors"))
    (args.out_dir / f"partial.shard{args.shard}.json").write_text(json.dumps(meta, indent=1))
    print("done")


def merge(args) -> None:
    sums: dict[str, torch.Tensor] = {}
    sqs: dict[str, torch.Tensor] = {}
    meta: dict[str, dict] = {}
    for p in sorted(args.out_dir.glob("partial.shard*.safetensors")):
        t = load_file(str(p))
        m = json.loads(p.with_suffix(".json").read_text())
        for k, v in t.items():
            kind, c, a = k.split("/")
            tgt = sums if kind == "sum" else sqs
            tgt[f"{c}/{a}"] = tgt.get(f"{c}/{a}", 0) + v
        for k, v in m.items():
            if k not in meta:
                meta[k] = {"n_tokens": 0.0, "n_responses": 0}
            meta[k]["n_tokens"] += v["n_tokens"]
            meta[k]["n_responses"] += v["n_responses"]
    contrasts = sorted({k.split("/")[0] for k in sums})
    out: dict[str, torch.Tensor] = {}
    report: dict = {"contrasts": {}, "layers": {}}
    gen = torch.Generator().manual_seed(args.seed)
    L = next(iter(sums.values())).shape[0]
    # per-layer RMS residual norm from the first contrast's neg arm
    ref = f"{contrasts[0]}/neg"
    rms = torch.sqrt(sqs[ref] / meta[ref]["n_tokens"])
    for l in range(L):
        out[f"norm/layer{l}"] = rms[l].reshape(1)
    rand_dirs = {k: torch.randn(L, next(iter(sums.values())).shape[1], generator=gen) for k in range(args.n_random)}
    for c in contrasts:
        pos = sums[f"{c}/pos"] / meta[f"{c}/pos"]["n_tokens"]
        neg = sums[f"{c}/neg"] / meta[f"{c}/neg"]["n_tokens"]
        vec = pos - neg
        report["contrasts"][c] = {"n_pos": meta[f"{c}/pos"]["n_responses"], "n_neg": meta[f"{c}/neg"]["n_responses"], "norm_by_layer": [round(float(x), 3) for x in vec.norm(dim=1)], "rel_norm_by_layer": [round(float(x), 4) for x in vec.norm(dim=1) / rms]}
        for l in range(L):
            out[f"{c}/layer{l}"] = vec[l].contiguous()
    # random matched-norm directions (matched to first contrast)
    base = contrasts[0]
    for k, dirs in rand_dirs.items():
        for l in range(L):
            v = dirs[l] / dirs[l].norm() * out[f"{base}/layer{l}"].norm()
            out[f"rand{k}/layer{l}"] = v.contiguous()
    if len(contrasts) > 1:
        cos = {}
        for i, a in enumerate(contrasts):
            for b in contrasts[i + 1 :]:
                cos[f"{a}|{b}"] = [round(float(torch.nn.functional.cosine_similarity(out[f"{a}/layer{l}"], out[f"{b}/layer{l}"], dim=0)), 3) for l in range(L)]
        report["cosines"] = cos
    report["rms_norm_by_layer"] = [round(float(x), 3) for x in rms]
    save_file(out, str(args.out_dir / "vectors.safetensors"))
    (args.out_dir / "vectors_report.json").write_text(json.dumps(report, indent=1))
    print(f"wrote {args.out_dir / 'vectors.safetensors'}; contrasts={contrasts}")


if __name__ == "__main__":
    main()
