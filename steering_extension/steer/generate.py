"""Generate paper-schema `generations.jsonl` rows from a `generation_jobs.jsonl` manifest with
optional per-side steering.

Each job may carry `steering_a` / `steering_b` blocks:
    {"vector": "<path.safetensors>", "key": "E", "layer": 16, "coef": 12.5, "mode": "response"}
    {"ablate": "<path.safetensors>", "key": "E"}            # directional ablation, all layers
    null / missing                                           # unsteered
A side may also carry `alias_a` / `alias_b`: an output_id already in the generations file whose
text is copied (shared baseline across dose cells).

Rows use the field set of `run_generation.generation_success_row` so the repo's
`run_judging.py --manifest ...` works unchanged. Sharding: --shard i --num-shards n splits
requests deterministically; each shard writes `generations.shard{i}.jsonl`; merge with
`python -m steering_extension.steer.generate --merge <run_dir>`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import torch
from safetensors.torch import load_file

from steering_extension.steer.hooks import AdditiveSteer, DirectionalAblation, steering
from steering_extension.steer.model import LoadedModel, chat_input_ids, load_model, strip_think

ROOT = Path(__file__).resolve().parents[2]


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def requests_from_jobs(jobs: list[dict]) -> list[dict]:
    reqs = []
    for job in jobs:
        for side in ("a", "b"):
            reqs.append(
                {
                    "output_id": f"{job['pair_uid']}::{side}",
                    "pair_uid": job["pair_uid"],
                    "condition": job[f"condition_{side}"],
                    "system_prompt": job.get(f"system_prompt_{side}", ""),
                    "prompt": job[f"prompt_{side}"],
                    "steering": job.get(f"steering_{side}"),
                    "alias": job.get(f"alias_{side}"),
                    "max_tokens": int(job.get("max_tokens", 900)),
                    "actor": job.get("actor", ""),
                    "model": job.get("model", ""),
                    "run_id": job.get("run_id", ""),
                }
            )
    return reqs


def steering_group_key(st: dict | None) -> tuple:
    if not st:
        return ("none",)
    if "ablate" in st:
        return ("ablate", st["ablate"], st.get("key", "E"))
    return ("add", st["vector"], st.get("key", "E"), int(st["layer"]), st.get("mode", "response"))


_vector_cache: dict[tuple[str, str, int | None], torch.Tensor] = {}


def load_vector(path: str, key: str, layer: int | None, device) -> torch.Tensor:
    ck = (path, key, layer)
    if ck not in _vector_cache:
        tensors = load_file(str(ROOT / path) if not os.path.isabs(path) else path)
        name = f"{key}/layer{layer}" if layer is not None else key
        if name not in tensors:
            raise KeyError(f"{name} not in {path}; keys: {sorted(tensors)[:10]}...")
        _vector_cache[ck] = tensors[name].to(device=device, dtype=torch.float32)
    return _vector_cache[ck]


@torch.inference_mode()
def generate_batch(loaded: LoadedModel, batch: list[dict], *, temperature: float, max_tokens: int, hook, layer_idx) -> list[dict]:
    tok = loaded.tokenizer
    ids = [chat_input_ids(loaded, r["system_prompt"], r["prompt"]) for r in batch]
    enc = tok.pad({"input_ids": ids}, padding=True, return_tensors="pt").to(loaded.device)
    prompt_len = enc["input_ids"].shape[1]
    with steering(loaded.layers, layer_idx, hook):
        out = loaded.model.generate(
            **enc,
            do_sample=temperature > 0,
            temperature=temperature if temperature > 0 else None,
            top_p=1.0,
            top_k=0,
            max_new_tokens=max_tokens,
            pad_token_id=tok.pad_token_id,
        )
    rows = []
    for i, req in enumerate(batch):
        gen = out[i, prompt_len:]
        n_new = int((gen != tok.pad_token_id).sum().item())
        text = tok.decode(gen, skip_special_tokens=True)
        text = strip_think(text)
        finished = bool((gen == tok.eos_token_id).any().item()) or n_new < max_tokens
        rows.append({"text": text, "completion_tokens": n_new, "prompt_tokens": int(enc["attention_mask"][i].sum().item()), "finish_reason": "stop" if finished else "length"})
    return rows


def success_row(req: dict, gen: dict, *, model_name: str, temperature: float, latency_s: float, max_tokens: int) -> dict:
    return {
        "output_id": req["output_id"],
        "pair_uid": req["pair_uid"],
        "actor": req["actor"],
        "model": model_name,
        "condition": req["condition"],
        "output_text": gen["text"],
        "success": True,
        "latency_s": round(latency_s, 3),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "reasoning": {"effort": "none", "backend": "hf_transformers", "enable_thinking": False},
        "provider": {"backend": "hf_transformers", "device": "cuda", "steering": req.get("steering")},
        "finish_reason": gen["finish_reason"],
        "usage": {"prompt_tokens": gen["prompt_tokens"], "completion_tokens": gen["completion_tokens"]},
        "run_id": req.get("run_id", ""),
    }


def merge(run_dir: Path) -> None:
    rows: dict[str, dict] = {}
    for path in sorted(run_dir.glob("generations.shard*.jsonl")):
        for row in read_jsonl(path):
            rows[row["output_id"]] = row
    # resolve aliases written as pointers
    for row in list(rows.values()):
        alias = row.get("alias_of")
        if alias and alias in rows:
            src = rows[alias]
            row["output_text"] = src["output_text"]
            row["finish_reason"] = src["finish_reason"]
            row["usage"] = src["usage"]
            row["latency_s"] = src["latency_s"]
    out = run_dir / "generations.jsonl"
    with out.open("w") as fh:
        for row in rows.values():
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"merged {len(rows)} rows -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--model", default=os.environ.get("STEER_MODEL", "Qwen/Qwen3.5-9B"))
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--num-shards", type=int, default=1)
    ap.add_argument("--merge", type=Path, default=None, help="Run dir: merge shard files and exit.")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    if args.merge:
        merge(args.merge)
        return
    jobs = read_jsonl(args.manifest)
    run_dir = Path(jobs[0]["run_dir"]) if jobs and jobs[0].get("run_dir") else args.manifest.parent
    out_path = run_dir / f"generations.shard{args.shard}.jsonl"
    done = {r["output_id"] for r in read_jsonl(out_path)}
    reqs = requests_from_jobs(jobs)
    # aliases: emit pointer rows, resolved at merge
    alias_rows = [r for r in reqs if r["alias"]]
    reqs = [r for r in reqs if not r["alias"]]
    reqs = [r for i, r in enumerate(reqs) if i % args.num_shards == args.shard and r["output_id"] not in done]
    if args.shard == 0:
        pending_alias = [r for r in alias_rows if r["output_id"] not in done]
        if pending_alias:
            append_jsonl(out_path, [
                {**success_row(r, {"text": "", "completion_tokens": 0, "prompt_tokens": 0, "finish_reason": "stop"}, model_name=args.model, temperature=args.temperature, latency_s=0.0, max_tokens=r["max_tokens"]), "alias_of": r["alias"]}
                for r in pending_alias
            ])
    if args.limit:
        reqs = reqs[: args.limit]
    print(f"shard {args.shard}/{args.num_shards}: {len(reqs)} pending requests -> {out_path}", flush=True)
    if not reqs:
        return
    loaded = load_model(args.model)
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in reqs:
        groups[(steering_group_key(r["steering"]), r["max_tokens"])].append(r)
    t_start = time.time()
    n_done = 0
    for (gkey, max_tokens), group in groups.items():
        # sort by prompt length for padding efficiency
        group.sort(key=lambda r: len(r["prompt"]))
        for i in range(0, len(group), args.batch_size):
            batch = group[i : i + args.batch_size]
            hook = None
            layer_idx = None
            if gkey[0] == "add":
                _, path, key, layer, mode = gkey
                vec = load_vector(path, key, layer, loaded.device)
                coefs = torch.tensor([float(r["steering"]["coef"]) for r in batch], device=loaded.device)
                hook = AdditiveSteer(vec, coefs, mode)
                layer_idx = layer
            elif gkey[0] == "ablate":
                _, path, key = gkey
                vec = load_vector(path, key, None, loaded.device)
                hook = DirectionalAblation(vec)
                layer_idx = None
            t0 = time.time()
            gens = generate_batch(loaded, batch, temperature=args.temperature, max_tokens=max_tokens, hook=hook, layer_idx=layer_idx)
            dt = time.time() - t0
            rows = [success_row(r, g, model_name=args.model, temperature=args.temperature, latency_s=dt / len(batch), max_tokens=max_tokens) for r, g in zip(batch, gens)]
            append_jsonl(out_path, rows)
            n_done += len(batch)
            toks = sum(g["completion_tokens"] for g in gens)
            print(f"[{gkey[0]}] {n_done}/{len(reqs)} batch={len(batch)} {dt:.1f}s {toks/dt:.0f} tok/s elapsed={time.time()-t_start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
