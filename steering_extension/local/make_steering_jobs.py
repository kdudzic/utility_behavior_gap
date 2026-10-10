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

from safetensors.torch import load_file

from steering_extension.local.common import ROOT, framed_neutral_prompt, make_job, task_items, write_manifest


def parse_cell(spec: str) -> dict:
    parts = spec.split(":")
    key, layer, r = parts[0], int(parts[1]), float(parts[2])
    mode = parts[3] if len(parts) > 3 else "response"
    return {"key": key, "layer": layer, "r": r, "mode": mode}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vectors", type=Path, required=True, help="vectors.safetensors from extract.py")
    ap.add_argument("--cell", action="append", required=True)
    ap.add_argument("--items", type=int, default=30)
    ap.add_argument("--item-offset", type=int, default=0)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--max-tokens", type=int, default=None)
    args = ap.parse_args()
    tensors = load_file(str(args.vectors))
    vec_rel = str(args.vectors.resolve().relative_to(ROOT)) if args.vectors.resolve().is_relative_to(ROOT) else str(args.vectors.resolve())
    cells = [parse_cell(c) for c in args.cell]
    items = task_items("essay")[args.item_offset : args.item_offset + args.items]
    jobs = []
    for rep in range(args.repeats):
        for row in items:
            neutral = framed_neutral_prompt(row)
            base_uid = f"steer_baseline:essay:{row['item_index']}:r{rep}"
            extra = {"steering_a": None, "steering_b": None}
            if args.max_tokens:
                extra["max_tokens"] = args.max_tokens
            # baseline cell: two independent unsteered samples (null comparison; a is the "second" sample)
            jobs.append(make_job(pair_uid=base_uid, comparison="steer_baseline", task_row=row, condition_a="baseline_rep", condition_b="baseline", prompt_a=neutral, prompt_b=neutral, repeat=rep, extra=extra))
            for c in cells:
                rms = float(tensors[f"norm/layer{c['layer']}"][0])
                vnorm = float(tensors[f"{c['key']}/layer{c['layer']}"].norm())
                coef = c["r"] * rms / vnorm
                cond = f"steer_{c['key']}_L{c['layer']}_r{c['r']:+.3f}_{c['mode']}"
                uid = f"{cond}:essay:{row['item_index']}:r{rep}"
                steer = {"vector": vec_rel, "key": c["key"], "layer": c["layer"], "coef": coef, "mode": c["mode"], "r": c["r"], "rms_norm": rms, "vector_norm": vnorm}
                ex = {"steering_a": steer, "steering_b": None, "alias_b": f"{base_uid}::b", "cell": cond}
                if args.max_tokens:
                    ex["max_tokens"] = args.max_tokens
                jobs.append(make_job(pair_uid=uid, comparison="steer_vs_baseline", task_row=row, condition_a=cond, condition_b="baseline", prompt_a=neutral, prompt_b=neutral, repeat=rep, extra=ex))
    write_manifest(jobs, args.run_name)


if __name__ == "__main__":
    main()
