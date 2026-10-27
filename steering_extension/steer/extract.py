"""Extract diff-of-means steering vectors from contrast prompts, with three readouts per layer.

Input: contrast jsonl rows {"contrast": "E", "arm": "pos"|"neg", "cid": ..., "prompt": ..., "system_prompt": ""}.
For each row we sample a response (thinking off), then run one forward pass over prompt+response
and record, at every decoder-block output:
  * rmean  : mean residual over response tokens (Persona Vectors readout; the pilot's recipe)
  * astart : residual at the last prompt token (the assistant-start position, whose output predicts
             the first response token; deterministic given the prompt)
  * pmean  : mean residual over the prompt tokens (user prompt incl. chat template; deterministic)
  * tailK  : residual at the K-th token from the end of the prompt, K = 2..TAIL_K (astart is K = 1);
             which template token each K is (newline, <|im_start|>, "assistant", </think>, ...) is listed in
             vectors_report.json["prompt_tail_tokens"] so the readouts can be named after the fact
  * gen1   : residual at the first generated token (sampled; the first position that is "in the answer")
Per-response readouts are stored (fp16) so the merge step can compute split-half reliability and
held-out projection AUC per layer and readout (layer_profile.csv), as well as the vectors.

Vector per layer = mean(pos) - mean(neg). Keys in vectors.safetensors:
  `{contrast}/layer{L}`         rmean vector (backward compatible with the pilot)
  `{contrast}_astart/layer{L}`, `{contrast}_pmean/layer{L}`
  `rand{k}/layer{L}`            random directions norm-matched to the first contrast's rmean vector
  `norm/layer{L}`               RMS residual norm over response tokens (dose unit)
Shardable like generate.py; merge with --merge --out-dir <dir>.
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

TAIL_K = 6
READOUTS = ("rmean", "astart", "pmean", *[f"tail{k}" for k in range(2, TAIL_K + 1)], "gen1")


@torch.inference_mode()
def respond_and_capture(loaded, rows: list[dict], *, max_new_tokens: int, temperature: float):
    """Return per-layer readouts (L, batch, d) for each of rmean/astart/pmean, plus sq norms and texts."""
    tok = loaded.tokenizer
    ids = [chat_input_ids(loaded, r.get("system_prompt", ""), r["prompt"]) for r in rows]
    enc = tok.pad({"input_ids": ids}, padding=True, return_tensors="pt").to(loaded.device)
    prompt_len = enc["input_ids"].shape[1]
    out = loaded.model.generate(**enc, do_sample=temperature > 0, temperature=temperature if temperature > 0 else None, top_p=1.0, top_k=0, max_new_tokens=max_new_tokens, pad_token_id=tok.pad_token_id)
    gen = out[:, prompt_len:]
    resp_mask = gen != tok.pad_token_id
    prompt_mask = enc["attention_mask"].bool()
    full_mask = torch.cat([prompt_mask, resp_mask], dim=1)
    B = out.shape[0]
    # three masks: response tokens, last prompt token (left padding => index prompt_len-1 for all), prompt tokens
    m_resp = torch.cat([torch.zeros_like(prompt_mask, dtype=torch.float), resp_mask.float()], dim=1)
    m_astart = torch.zeros_like(full_mask, dtype=torch.float)
    m_astart[:, prompt_len - 1] = 1.0
    m_pmean = torch.cat([prompt_mask.float(), torch.zeros_like(resp_mask, dtype=torch.float)], dim=1)
    backbone = getattr(loaded.model, "model", loaded.model)
    masks = {"rmean": m_resp, "astart": m_astart, "pmean": m_pmean}
    for k in range(2, TAIL_K + 1):
        m = torch.zeros_like(full_mask, dtype=torch.float)
        m[:, prompt_len - k] = 1.0
        masks[f"tail{k}"] = m
    m_gen1 = torch.zeros_like(full_mask, dtype=torch.float)
    m_gen1[:, prompt_len] = resp_mask[:, 0].float()
    masks["gen1"] = m_gen1
    with ResidualCapture(loaded.layers) as cap:
        cap.masks = masks
        backbone(input_ids=out, attention_mask=full_mask.long())
    L = len(cap.sq_norm_sums)
    readouts = {}
    for name, mask in masks.items():
        counts = mask.sum(dim=1).clamp(min=1.0)
        stack = torch.stack([cap.multi[name][l] for l in range(L)], dim=0)  # (L, B, d) float32
        readouts[name] = (stack / counts[None, :, None]).cpu()
    sq = torch.stack([cap.sq_norm_sums[l] for l in range(L)], dim=0).cpu()  # (L, B)
    n_resp = resp_mask.sum(dim=1).float().cpu()
    texts = [strip_think(tok.decode(g, skip_special_tokens=True)) for g in gen]
    return readouts, sq, n_resp, texts


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
    ap.add_argument("--n-splits", type=int, default=20, help="random split-half repetitions in --merge")
    ap.add_argument("--k-folds", type=int, default=5, help="folds for held-out projection AUC in --merge")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.merge:
        merge(args)
        return
    rows = read_jsonl(args.contrasts)
    rows = [r for i, r in enumerate(rows) if i % args.num_shards == args.shard]
    loaded = load_model(args.model)
    resp_log = args.out_dir / f"responses.shard{args.shard}.jsonl"
    rows.sort(key=lambda r: len(r["prompt"]))
    per_resp: dict[str, list[torch.Tensor]] = {k: [] for k in READOUTS}
    sq_all: list[torch.Tensor] = []
    n_tok_all: list[torch.Tensor] = []
    meta_rows: list[dict] = []
    tail_tokens = None
    for i in range(0, len(rows), args.batch_size):
        batch = rows[i : i + args.batch_size]
        readouts, sq, n_resp, texts = respond_and_capture(loaded, batch, max_new_tokens=args.max_new_tokens, temperature=args.temperature)
        if tail_tokens is None:
            ids0 = chat_input_ids(loaded, batch[0].get("system_prompt", ""), batch[0]["prompt"])
            tail_tokens = {f"tail{k}" if k > 1 else "astart": loaded.tokenizer.decode([ids0[-k]]) for k in range(1, TAIL_K + 1)}
        for k in READOUTS:
            per_resp[k].append(readouts[k].to(torch.float16))  # (L, b, d)
        sq_all.append(sq)
        n_tok_all.append(n_resp)
        for r, t, c in zip(batch, texts, n_resp.tolist()):
            meta_rows.append({"contrast": r["contrast"], "arm": r["arm"], "cid": r["cid"], "response_tokens": int(c)})
        append_jsonl(resp_log, [{**r, "response": t, "response_tokens": int(c)} for r, t, c in zip(batch, texts, n_resp.tolist())])
        print(f"{i+len(batch)}/{len(rows)}", flush=True)
    tensors = {k: torch.cat(per_resp[k], dim=1).contiguous() for k in READOUTS}  # (L, N, d) fp16
    tensors["sq_norm_sum"] = torch.cat(sq_all, dim=1).contiguous()  # (L, N)
    tensors["n_resp_tokens"] = torch.cat(n_tok_all, dim=0).contiguous()  # (N,)
    save_file(tensors, str(args.out_dir / f"perresp.shard{args.shard}.safetensors"))
    (args.out_dir / f"perresp.shard{args.shard}.json").write_text(json.dumps({"rows": meta_rows, "prompt_tail_tokens": tail_tokens}))
    print("done")


def _auc(pos: torch.Tensor, neg: torch.Tensor) -> float:
    # Mann-Whitney AUC
    scores = torch.cat([pos, neg])
    ranks = scores.argsort().argsort().float() + 1
    r_pos = ranks[: len(pos)].sum()
    n1, n0 = len(pos), len(neg)
    return float((r_pos - n1 * (n1 + 1) / 2) / (n1 * n0))


def merge(args) -> None:
    parts = sorted(args.out_dir.glob("perresp.shard*.safetensors"))
    if not parts:
        raise SystemExit(f"no perresp shards in {args.out_dir}")
    data = {k: [] for k in (*READOUTS, "sq_norm_sum", "n_resp_tokens")}
    meta: list[dict] = []
    for p in parts:
        t = load_file(str(p))
        for k in data:
            data[k].append(t[k])
        mj = json.loads(p.with_suffix(".json").read_text())
        if isinstance(mj, dict):
            meta.extend(mj["rows"]); tail_tokens = mj.get("prompt_tail_tokens")
        else:
            meta.extend(mj); tail_tokens = None
    X = {k: torch.cat(data[k], dim=1).float() for k in READOUTS}  # (L, N, d)
    sq = torch.cat(data["sq_norm_sum"], dim=1).float()  # (L, N)
    ntok = torch.cat(data["n_resp_tokens"], dim=0).float()  # (N,)
    L, N, d = X["rmean"].shape
    contrasts = sorted({m["contrast"] for m in meta})
    idx = {(c, a): torch.tensor([i for i, m in enumerate(meta) if m["contrast"] == c and m["arm"] == a]) for c in contrasts for a in ("pos", "neg")}
    # dose unit: RMS residual over response tokens, neg arm of the first contrast
    ref = idx[(contrasts[0], "neg")]
    rms = torch.sqrt(sq[:, ref].sum(dim=1) / ntok[ref].sum())  # (L,)
    out: dict[str, torch.Tensor] = {f"norm/layer{l}": rms[l].reshape(1) for l in range(L)}
    report: dict = {"n_responses": N, "contrasts": {}, "rms_norm_by_layer": [round(float(x), 3) for x in rms], "readouts": list(READOUTS), "prompt_tail_tokens": tail_tokens}
    gen = torch.Generator().manual_seed(args.seed)
    profile_rows: list[dict] = []
    for c in contrasts:
        ip, ineg = idx[(c, "pos")], idx[(c, "neg")]
        report["contrasts"][c] = {"n_pos": len(ip), "n_neg": len(ineg)}
        for ro in READOUTS:
            Xp, Xn = X[ro][:, ip], X[ro][:, ineg]  # (L, np, d), (L, nn, d)
            vec = Xp.mean(dim=1) - Xn.mean(dim=1)  # (L, d)
            key = c if ro == "rmean" else f"{c}_{ro}"
            for l in range(L):
                out[f"{key}/layer{l}"] = vec[l].contiguous()
            # split-half reliability
            sh = torch.zeros(args.n_splits, L)
            for s in range(args.n_splits):
                pp = ip[torch.randperm(len(ip), generator=gen)]
                nn_ = ineg[torch.randperm(len(ineg), generator=gen)]
                a = X[ro][:, pp[: len(pp) // 2]].mean(1) - X[ro][:, nn_[: len(nn_) // 2]].mean(1)
                b = X[ro][:, pp[len(pp) // 2 :]].mean(1) - X[ro][:, nn_[len(nn_) // 2 :]].mean(1)
                sh[s] = torch.nn.functional.cosine_similarity(a, b, dim=1)
            sh_mean = sh.mean(0)
            sb = 2 * sh_mean / (1 + sh_mean)  # Spearman-Brown for the full-sample vector
            # k-fold held-out projection AUC (direction fit on k-1 folds, projections on the held-out fold)
            aucs = torch.zeros(L)
            fp = ip[torch.randperm(len(ip), generator=gen)]
            fn = ineg[torch.randperm(len(ineg), generator=gen)]
            fold_p = [fp[k :: args.k_folds] for k in range(args.k_folds)]
            fold_n = [fn[k :: args.k_folds] for k in range(args.k_folds)]
            for l in range(L):
                vals = []
                for k in range(args.k_folds):
                    tr_p = torch.cat([fold_p[j] for j in range(args.k_folds) if j != k])
                    tr_n = torch.cat([fold_n[j] for j in range(args.k_folds) if j != k])
                    v = X[ro][l, tr_p].mean(0) - X[ro][l, tr_n].mean(0)
                    v = v / (v.norm() + 1e-8)
                    vals.append(_auc(X[ro][l, fold_p[k]] @ v, X[ro][l, fold_n[k]] @ v))
                aucs[l] = sum(vals) / len(vals)
            vnorm = vec.norm(dim=1)
            # relative norm against the residual RMS of the same readout's tokens is not stored; use response RMS
            for l in range(L):
                profile_rows.append({"contrast": c, "readout": ro, "layer": l, "split_half_cos": round(float(sh_mean[l]), 4), "spearman_brown": round(float(sb[l]), 4), "heldout_auc": round(float(aucs[l]), 4), "vector_norm": round(float(vnorm[l]), 4), "rel_norm_vs_resp_rms": round(float(vnorm[l] / rms[l]), 5)})
    # random directions, norm-matched to the first contrast's rmean vector
    base = contrasts[0]
    for k in range(args.n_random):
        dirs = torch.randn(L, d, generator=gen)
        for l in range(L):
            out[f"rand{k}/layer{l}"] = (dirs[l] / dirs[l].norm() * out[f"{base}/layer{l}"].norm()).contiguous()
    # cosines between contrasts (rmean) and between readouts of the same contrast
    cos: dict[str, list[float]] = {}
    for i, a in enumerate(contrasts):
        for b in contrasts[i + 1 :]:
            cos[f"{a}|{b}"] = [round(float(torch.nn.functional.cosine_similarity(out[f"{a}/layer{l}"], out[f"{b}/layer{l}"], dim=0)), 3) for l in range(L)]
    for c in contrasts:
        for ro in READOUTS[1:]:
            cos[f"{c}|{c}_{ro}"] = [round(float(torch.nn.functional.cosine_similarity(out[f"{c}/layer{l}"], out[f"{c}_{ro}/layer{l}"], dim=0)), 3) for l in range(L)]
    report["cosines"] = cos
    save_file(out, str(args.out_dir / "vectors.safetensors"))
    (args.out_dir / "vectors_report.json").write_text(json.dumps(report, indent=1))
    import csv
    with (args.out_dir / "layer_profile.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(profile_rows[0].keys()))
        w.writeheader()
        w.writerows(profile_rows)
    print(f"wrote {args.out_dir / 'vectors.safetensors'} ({len(out)} keys), layer_profile.csv ({len(profile_rows)} rows); contrasts={contrasts}")


if __name__ == "__main__":
    main()
