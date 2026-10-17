"""Project texts onto steering vectors (monitoring / "arrival" readout).

For each output in a run's generations.jsonl (or any jsonl with prompt/response fields), re-encode
prompt + response WITHOUT steering and record, at the requested layers, the projection of the
response-token-mean residual (and the assistant-start residual) onto the requested unit vectors.
Used for: the Hidden Valence "arrival" hurdle (does steered text, re-read, shift along E?), the
Pain Axis monitoring layer, and the proposal's Phase 3 prompt-projection experiment.

Output: <out> jsonl rows {output_id, condition, layer, key, proj_rmean, proj_astart, resid_rms_rmean}.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from safetensors.torch import load_file

from steering_extension.steer.generate import ROOT, append_jsonl, read_jsonl
from steering_extension.steer.hooks import ResidualCapture
from steering_extension.steer.model import chat_input_ids, load_model


@torch.inference_mode()
def encode_and_capture(loaded, items: list[dict]):
    """items: {system_prompt, prompt, response}. Returns dict layer -> (rmean (b,d), astart (b,d), rms (b,))."""
    tok = loaded.tokenizer
    p_ids = [chat_input_ids(loaded, it.get("system_prompt", ""), it["prompt"]) for it in items]
    r_ids = [tok(it["response"], add_special_tokens=False)["input_ids"] for it in items]
    # left-pad prompts to a common length, then append responses right-padded
    P = max(len(p) for p in p_ids)
    R = max(max(len(r) for r in r_ids), 1)
    pad = tok.pad_token_id
    ids = torch.full((len(items), P + R), pad, dtype=torch.long)
    att = torch.zeros((len(items), P + R), dtype=torch.long)
    m_resp = torch.zeros((len(items), P + R))
    m_astart = torch.zeros((len(items), P + R))
    for i, (p, r) in enumerate(zip(p_ids, r_ids)):
        ids[i, P - len(p) : P] = torch.tensor(p)
        att[i, P - len(p) : P] = 1
        ids[i, P : P + len(r)] = torch.tensor(r)
        att[i, P : P + len(r)] = 1
        m_resp[i, P : P + len(r)] = 1.0
        m_astart[i, P - 1] = 1.0
    ids, att = ids.to(loaded.device), att.to(loaded.device)
    backbone = getattr(loaded.model, "model", loaded.model)
    res = {}
    masks = {"rmean": m_resp.to(loaded.device), "astart": m_astart.to(loaded.device)}
    with ResidualCapture(loaded.layers) as cap:
        cap.masks = masks
        backbone(input_ids=ids, attention_mask=att)
    counts = {n: m.sum(1).clamp(min=1.0) for n, m in masks.items()}
    for l in cap.sq_norm_sums:
        res[l] = {n: (cap.multi[n][l] / counts[n][:, None]).cpu() for n in masks}
        res[l]["rms"] = torch.sqrt(cap.sq_norm_sums[l] / counts["rmean"]).cpu()
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, help="run dir with generation_jobs.jsonl + generations.jsonl")
    ap.add_argument("--inputs", type=Path, help="alternative: jsonl with prompt/response(/system_prompt) fields and an output_id")
    ap.add_argument("--vectors", type=Path, required=True)
    ap.add_argument("--keys", default="E", help="comma list of vector keys (e.g. E,E_astart,rand0)")
    ap.add_argument("--layers", default="8,10,12,14,16,18,20,22,24", help="comma list of layers")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--model", default=os.environ.get("STEER_MODEL", "Qwen/Qwen3.5-9B"))
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--num-shards", type=int, default=1)
    ap.add_argument("--conditions", default=None, help="comma list of conditions to keep (run-dir mode)")
    args = ap.parse_args()
    keys = args.keys.split(",")
    layers = [int(x) for x in args.layers.split(",")]
    if args.run_dir:
        jobs = {j["pair_uid"]: j for j in read_jsonl(args.run_dir / "generation_jobs.jsonl")}
        items = []
        for g in read_jsonl(args.run_dir / "generations.jsonl"):
            if g.get("alias_of") or not g.get("output_text"):
                continue
            if args.conditions and g["condition"] not in args.conditions.split(","):
                continue
            side = g["output_id"].rsplit("::", 1)[1]
            job = jobs[g["pair_uid"]]
            items.append({"output_id": g["output_id"], "condition": g["condition"], "system_prompt": job.get(f"system_prompt_{side}", ""), "prompt": job[f"prompt_{side}"], "response": g["output_text"]})
        out = args.out or (args.run_dir / f"projections.shard{args.shard}.jsonl")
    else:
        items = [{"output_id": r.get("output_id", str(i)), "condition": r.get("condition", r.get("arm", "")), "system_prompt": r.get("system_prompt", ""), "prompt": r["prompt"], "response": r["response"]} for i, r in enumerate(read_jsonl(args.inputs))]
        out = args.out or args.inputs.with_suffix(f".projections.shard{args.shard}.jsonl")
    done = {(r["output_id"], r["layer"], r["key"]) for r in read_jsonl(out)}
    items = [it for i, it in enumerate(items) if i % args.num_shards == args.shard]
    items = [it for it in items if any((it["output_id"], l, k) not in done for l in layers for k in keys)]
    print(f"shard {args.shard}/{args.num_shards}: {len(items)} items -> {out}", flush=True)
    if not items:
        return
    tensors = load_file(str(args.vectors if args.vectors.is_absolute() else ROOT / args.vectors))
    units = {(k, l): (tensors[f"{k}/layer{l}"].float() / tensors[f"{k}/layer{l}"].float().norm()) for k in keys for l in layers}
    loaded = load_model(args.model)
    items.sort(key=lambda it: len(it["prompt"]) + len(it["response"]))
    for i in range(0, len(items), args.batch_size):
        batch = items[i : i + args.batch_size]
        res = encode_and_capture(loaded, batch)
        rows = []
        for l in layers:
            for k in keys:
                u = units[(k, l)]
                pr = res[l]["rmean"] @ u
                pa = res[l]["astart"] @ u
                for j, it in enumerate(batch):
                    rows.append({"output_id": it["output_id"], "condition": it["condition"], "layer": l, "key": k, "proj_rmean": round(float(pr[j]), 4), "proj_astart": round(float(pa[j]), 4), "resid_rms_rmean": round(float(res[l]["rms"][j]), 3)})
        append_jsonl(out, rows)
        print(f"{i+len(batch)}/{len(items)}", flush=True)


if __name__ == "__main__":
    main()
