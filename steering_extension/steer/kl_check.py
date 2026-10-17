"""KL damage check for candidate (layer, dose) steering settings (Arditi-style).

For each unsteered baseline output in a run, teacher-force the first --n-tokens response tokens
and compute, at each position, KL(p_unsteered || p_steered) over the vocabulary, with steering applied
in "response" mode (the hook also fires on teacher-forced response positions here because we run the
prompt prefill separately from the response positions). Reports per (key, layer, r) the mean and median
KL over positions and prompts. Low KL = the steered model still speaks like itself; Arditi used < 0.1.

Output: <run_dir>/kl_check.jsonl rows {key, layer, r, coef, n_prompts, kl_mean, kl_median, kl_p90}.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from safetensors.torch import load_file

from steering_extension.steer.generate import ROOT, append_jsonl, read_jsonl
from steering_extension.steer.hooks import AdditiveSteer, steering
from steering_extension.steer.model import chat_input_ids, load_model


@torch.inference_mode()
def logprobs_response(loaded, p_ids: list[list[int]], r_ids: list[list[int]], hook, layer_idx):
    """Two-stage forward: prefill prompts (no steering), then response tokens with the hook (seq chunks of 1)."""
    tok = loaded.tokenizer
    pad = tok.pad_token_id
    P = max(len(p) for p in p_ids)
    B = len(p_ids)
    ids = torch.full((B, P), pad, dtype=torch.long)
    att = torch.zeros((B, P), dtype=torch.long)
    for i, p in enumerate(p_ids):
        ids[i, P - len(p) :] = torch.tensor(p)
        att[i, P - len(p) :] = 1
    ids, att = ids.to(loaded.device), att.to(loaded.device)
    out = loaded.model(input_ids=ids, attention_mask=att, use_cache=True)
    past = out.past_key_values
    logits_next = out.logits[:, -1]
    R = max(len(r) for r in r_ids)
    lps = torch.zeros(B, R, device=loaded.device)
    valid = torch.zeros(B, R, dtype=torch.bool, device=loaded.device)
    with steering(loaded.layers, layer_idx, hook):
        for t in range(R):
            step = torch.tensor([r[t] if t < len(r) else pad for r in r_ids], device=loaded.device)[:, None]
            lp = torch.log_softmax(logits_next.float(), dim=-1)
            lps[:, t] = lp.gather(1, step).squeeze(1)
            for i, r in enumerate(r_ids):
                valid[i, t] = t < len(r)
            att = torch.cat([att, torch.ones((B, 1), dtype=torch.long, device=loaded.device)], dim=1)
            out = loaded.model(input_ids=step, attention_mask=att, past_key_values=past, use_cache=True)
            past = out.past_key_values
            logits_next = out.logits[:, -1]
            if t == 0:
                full_lp = [lp]
            else:
                full_lp.append(lp)
    return torch.stack(full_lp, dim=1), valid  # (B, R, V) log-probs under this condition, mask


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, required=True, help="run with unsteered 'baseline' outputs (condition_b of steer_baseline)")
    ap.add_argument("--vectors", type=Path, required=True)
    ap.add_argument("--settings", required=True, help="comma list KEY:LAYER:R, e.g. E:12:0.05,E:16:0.05")
    ap.add_argument("--n-prompts", type=int, default=24)
    ap.add_argument("--n-tokens", type=int, default=32)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--model", default=os.environ.get("STEER_MODEL", "Qwen/Qwen3.5-9B"))
    ap.add_argument("--shard", type=int, default=0, help="shard over settings")
    ap.add_argument("--num-shards", type=int, default=1)
    args = ap.parse_args()
    jobs = {j["pair_uid"]: j for j in read_jsonl(args.run_dir / "generation_jobs.jsonl")}
    gens = [g for g in read_jsonl(args.run_dir / "generations.jsonl") if g["condition"] == "baseline" and g.get("output_text") and not g.get("alias_of")]
    gens = gens[: args.n_prompts]
    tensors = load_file(str(args.vectors if args.vectors.is_absolute() else ROOT / args.vectors))
    loaded = load_model(args.model)
    tok = loaded.tokenizer
    p_ids = [chat_input_ids(loaded, jobs[g["pair_uid"]].get("system_prompt_b", ""), jobs[g["pair_uid"]]["prompt_b"]) for g in gens]
    r_ids = [tok(g["output_text"], add_special_tokens=False)["input_ids"][: args.n_tokens] for g in gens]
    out_path = args.run_dir / (f"kl_check.shard{args.shard}.jsonl" if args.num_shards > 1 else "kl_check.jsonl")
    # unsteered reference
    ref = []
    for i in range(0, len(gens), args.batch_size):
        lp, valid = logprobs_response(loaded, p_ids[i : i + args.batch_size], r_ids[i : i + args.batch_size], None, None)
        ref.append((lp.cpu(), valid.cpu()))
    settings = [s for i, s in enumerate(args.settings.split(",")) if i % args.num_shards == args.shard]
    for spec in settings:
        key, layer, r = spec.split(":")
        layer, r = int(layer), float(r)
        vec = tensors[f"{key}/layer{layer}"].float().to(loaded.device)
        rms = float(tensors[f"norm/layer{layer}"][0])
        coef = r * rms / float(vec.norm())
        kls = []
        for bi, i in enumerate(range(0, len(gens), args.batch_size)):
            bsz = len(p_ids[i : i + args.batch_size])
            hook = AdditiveSteer(vec, torch.full((bsz,), coef, device=loaded.device), "response")
            lp_s, valid = logprobs_response(loaded, p_ids[i : i + args.batch_size], r_ids[i : i + args.batch_size], hook, layer)
            lp_u, _ = ref[bi]
            lp_u = lp_u.to(loaded.device)
            kl = (lp_u.exp() * (lp_u - lp_s)).sum(-1)  # (B, R)
            kls.append(kl[valid.to(kl.device)].cpu())
        kl_all = torch.cat(kls)
        row = {"key": key, "layer": layer, "r": r, "coef": round(coef, 5), "n_prompts": len(gens), "n_positions": int(kl_all.numel()), "kl_mean": round(float(kl_all.mean()), 5), "kl_median": round(float(kl_all.median()), 5), "kl_p90": round(float(kl_all.quantile(0.9)), 5)}
        append_jsonl(out_path, [row])
        print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
