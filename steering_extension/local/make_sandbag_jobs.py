"""Week 9: is the paper's sandbagging (harmful-cause framing vs the framed-empty baseline) carried by the effort
direction? Builds manifests in the paper's job schema with the paper's prompts byte-for-byte:

  harmful : build_modgrid_prompt(task, task_block, amount=1000, target=<bad_text of a moral cause pair>)
            (the moral_bad arm of the paper's modgrid_<task>_moral comparison)
  empty   : build_modgrid_empty_prompt(task, task_block)   (the paper's framed_empty arm)

The cause for (item, repeat) follows the paper's rule: cause_rows[(repeat * n_items_in_task + item_position) % n_causes].

Pairs, per item and repeat (side a first):
  harmful_vs_empty                      harmful untouched            vs empty untouched     (replicates the paper cell)
  steer_<K>_L<L>_r<r>_harmful           harmful steered with K       vs harmful untouched   (cell spec K:L:r:harmful)
  steer_<K>_L<L>_r<r>_empty             empty steered with K         vs empty untouched     (cell spec K:L:r:empty)
  ..._harmful_vs_empty  (--bridge)      the same steered harmful text vs empty untouched    (aliases only, no new text)
  effort_vs_neutral     (--effort-ref)  max-effort prompt            vs framed-neutral prompt, untouched (readout reference)

The untouched harmful and empty texts are generated once per item and repeat (in harmful_vs_empty) and aliased.
Doses are fractions of the layer's RMS residual norm stored in the vector file (norm/layer<L>).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

from steering_extension.local.common import ROOT, effort_prompt, framed_neutral_prompt, make_job, task_items, write_manifest
from utility_behavior_gap.io_utils import read_csv_rows
from utility_behavior_gap.paths import INPUTS
from utility_behavior_gap.prompts import build_modgrid_empty_prompt, build_modgrid_prompt


def task_block(row: dict[str, str]) -> str:
    if row["task"] == "essay":
        from utility_behavior_gap.job_builder import clean_essay_direct_prompt

        return clean_essay_direct_prompt(str(row["item_label"]))
    return str(row["base_prompt"])


def harmful_prompt(row: dict[str, str], cause: dict[str, str]) -> str:
    return build_modgrid_prompt(row["task"], task_block(row), amount=1000, target=cause["bad_text"])


def empty_prompt(row: dict[str, str]) -> str:
    return build_modgrid_empty_prompt(row["task"], task_block(row))


def cause_for(causes: list[dict[str, str]], n_pool: int, item_pos: int, rep: int) -> dict[str, str]:
    return causes[(rep * n_pool + item_pos) % len(causes)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vectors", type=Path, default=None, help="vectors.safetensors; only needed with --cell")
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--task", default="grant_proposal_abstract")
    ap.add_argument("--items", type=int, default=30)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--repeat-start", type=int, default=0, help="first repeat index (for top-up runs that extend an earlier run)")
    ap.add_argument("--cell", action="append", default=[], help="KEY:LAYER:R:PROMPT with PROMPT in harmful|empty, e.g. E:10:0.05:harmful")
    ap.add_argument("--bridge", action="store_true", help="for harmful cells also pair the steered text with the untouched empty text")
    ap.add_argument("--effort-ref", action="store_true", help="also generate untouched max-effort vs framed-neutral pairs")
    args = ap.parse_args()
    if args.cell and args.vectors is None:
        ap.error("--cell needs --vectors")
    tensors = load_file(str(args.vectors)) if args.vectors else {}
    vec_rel = "" if args.vectors is None else str(args.vectors.resolve().relative_to(ROOT)) if args.vectors.resolve().is_relative_to(ROOT) else str(args.vectors.resolve())
    causes = read_csv_rows(INPUTS / "moral_cause_pairs.csv")
    pool = task_items(args.task)
    cells = []
    for spec in args.cell:
        key, layer, r, prompt = spec.split(":")
        assert prompt in ("harmful", "empty"), spec
        L = int(layer)
        rms = float(tensors[f"norm/layer{L}"][0])
        vnorm = float(np.linalg.norm(tensors[f"{key}/layer{L}"].astype(np.float64)))
        cells.append({"key": key, "layer": L, "r": float(r), "prompt": prompt,
                      "steer": {"vector": vec_rel, "key": key, "layer": L, "coef": float(r) * rms / vnorm, "mode": "response", "r": float(r), "rms_norm": rms, "vector_norm": vnorm}})
    jobs = []
    for rep in range(args.repeat_start, args.repeat_start + args.repeats):
        for pos, row in enumerate(pool[: args.items]):
            task = row["task"]
            cause = cause_for(causes, len(pool), pos, rep)
            ph, pe = harmful_prompt(row, cause), empty_prompt(row)
            meta = {"cause_pair_label": cause["cause_pair_label"], "bad_text": cause["bad_text"]}
            stem = f"{task}:{row['item_index']}:r{rep}"
            base_uid = f"harmful_vs_empty:{stem}"
            jobs.append(make_job(pair_uid=base_uid, comparison="harmful_vs_empty", task_row=row, condition_a="harmful", condition_b="framed_empty", prompt_a=ph, prompt_b=pe, repeat=rep,
                                 extra={"steering_a": None, "steering_b": None, "cell": "harmful_vs_empty", **meta}))
            for c in cells:
                side = c["prompt"]
                cond = f"steer_{c['key']}_L{c['layer']}_r{c['r']:+.3f}_{side}"
                untouched = "harmful" if side == "harmful" else "framed_empty"
                uid = f"{cond}:{stem}"
                jobs.append(make_job(pair_uid=uid, comparison=f"steer_vs_{side}", task_row=row, condition_a=cond, condition_b=untouched,
                                     prompt_a=ph if side == "harmful" else pe, prompt_b=ph if side == "harmful" else pe, repeat=rep,
                                     extra={"steering_a": c["steer"], "steering_b": None, "alias_b": f"{base_uid}::{'a' if side == 'harmful' else 'b'}", "cell": cond, **meta}))
                if args.bridge and side == "harmful":
                    jobs.append(make_job(pair_uid=f"{cond}_vs_empty:{stem}", comparison="steered_harmful_vs_empty", task_row=row, condition_a=cond, condition_b="framed_empty", prompt_a=ph, prompt_b=pe, repeat=rep,
                                         extra={"steering_a": c["steer"], "steering_b": None, "alias_a": f"{uid}::a", "alias_b": f"{base_uid}::b", "cell": f"{cond}_vs_empty", **meta}))
            if args.effort_ref:
                jobs.append(make_job(pair_uid=f"effort_vs_neutral:{stem}", comparison="effort_vs_neutral", task_row=row, condition_a="effort", condition_b="neutral", prompt_a=effort_prompt(row), prompt_b=framed_neutral_prompt(row), repeat=rep,
                                     extra={"steering_a": None, "steering_b": None, "cell": "effort_vs_neutral"}))
    write_manifest(jobs, args.run_name)
    print(f"{args.run_name}: {len(jobs)} pairs, {len(cells)} steered cells, {args.items} items x {args.repeats} repeats")


if __name__ == "__main__":
    main()
