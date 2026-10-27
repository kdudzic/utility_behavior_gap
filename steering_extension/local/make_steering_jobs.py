"""Build steered-vs-baseline essay manifests.

Cells are given as --cell KEY:LAYER:R[:MODE] where R is the dose as a fraction of the layer's
RMS residual norm (sign allowed). Every cell pairs the steered side (a) against the shared
unsteered baseline (b) for the same item and repeat; the baseline is generated once per
(item, repeat) in a dedicated `baseline` cell and aliased into the other cells.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

from steering_extension.local.common import ROOT, framed_neutral_prompt, make_job, task_items, write_manifest


def parse_cell(spec: str) -> dict:
    """KEY:LAYER:R[:MODE]; LAYER may be several layers joined by '+', e.g. E:12+16+20:0.05 (the dose r is
    split evenly across the layers, each relative to its own RMS). MODE: response (default) | all | prompt."""
    parts = spec.split(":")
    key, r = parts[0], float(parts[2])
    layers = [int(x) for x in parts[1].split("+")]
    mode = parts[3] if len(parts) > 3 else "response"
    if mode not in {"response", "all", "prompt"}:
        raise ValueError(f"bad mode {mode} in {spec}")
    return {"key": key, "layers": layers, "r": r, "mode": mode}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vectors", type=Path, required=True, help="vectors.safetensors from extract.py")
    ap.add_argument("--cell", action="append", required=True)
    ap.add_argument("--items", type=int, default=30)
    ap.add_argument("--item-offset", type=int, default=0)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--task", default="essay", help="essay (evaluation) or grant_proposal_abstract / incident_postmortem (layer sweep); comma list allowed")
    ap.add_argument("--max-tokens", type=int, default=None)
    args = ap.parse_args()
    tensors = load_file(str(args.vectors))
    vec_rel = str(args.vectors.resolve().relative_to(ROOT)) if args.vectors.resolve().is_relative_to(ROOT) else str(args.vectors.resolve())
    cells = [parse_cell(c) for c in args.cell]
    items = []
    for t in args.task.split(","):
        items += task_items(t)[args.item_offset : args.item_offset + args.items]
    jobs = []
    for rep in range(args.repeats):
        for row in items:
            task = row["task"]
            neutral = framed_neutral_prompt(row)
            base_uid = f"steer_baseline:{task}:{row['item_index']}:r{rep}"
            extra = {"steering_a": None, "steering_b": None}
            if args.max_tokens:
                extra["max_tokens"] = args.max_tokens
            # baseline cell: two independent unsteered samples (null comparison; a is the "second" sample)
            jobs.append(make_job(pair_uid=base_uid, comparison="steer_baseline", task_row=row, condition_a="baseline_rep", condition_b="baseline", prompt_a=neutral, prompt_b=neutral, repeat=rep, extra=extra))
            for c in cells:
                per_layer = c["r"] / len(c["layers"])
                coefs, rmss, vnorms = [], [], []
                for L in c["layers"]:
                    rms = float(tensors[f"norm/layer{L}"][0])
                    vnorm = float(np.linalg.norm(tensors[f"{c['key']}/layer{L}"].astype(np.float64)))
                    coefs.append(per_layer * rms / vnorm); rmss.append(rms); vnorms.append(vnorm)
                lname = "+".join(str(L) for L in c["layers"])
                cond = f"steer_{c['key']}_L{lname}_r{c['r']:+.3f}_{c['mode']}"
                uid = f"{cond}:{task}:{row['item_index']}:r{rep}"
                if len(c["layers"]) == 1:
                    steer = {"vector": vec_rel, "key": c["key"], "layer": c["layers"][0], "coef": coefs[0], "mode": c["mode"], "r": c["r"], "rms_norm": rmss[0], "vector_norm": vnorms[0]}
                else:
                    steer = {"vector": vec_rel, "key": c["key"], "layers": c["layers"], "coefs": coefs, "mode": c["mode"], "r": c["r"], "r_per_layer": per_layer, "rms_norm": rmss, "vector_norm": vnorms}
                ex = {"steering_a": steer, "steering_b": None, "alias_b": f"{base_uid}::b", "cell": cond}
                if args.max_tokens:
                    ex["max_tokens"] = args.max_tokens
                jobs.append(make_job(pair_uid=uid, comparison="steer_vs_baseline", task_row=row, condition_a=cond, condition_b="baseline", prompt_a=neutral, prompt_b=neutral, repeat=rep, extra=ex))
    write_manifest(jobs, args.run_name)


if __name__ == "__main__":
    main()
