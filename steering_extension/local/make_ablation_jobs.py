"""Necessity arm: directional ablation of the effort direction UNDER the real max-effort prompt.

Cells (side a vs side b, same item and repeat; the paper's framed-neutral competition prompts):
  ablate_E_vs_effort     : max-effort prompt with E projected out at every block output  vs  max-effort prompt, untouched
  ablate_rand0_vs_effort : same with a random matched-norm direction projected out           vs  max-effort, untouched   (control)
  ablate_E_vs_neutral    : max-effort prompt with E projected out                            vs  framed-neutral prompt, untouched
  effort_vs_neutral      : max-effort prompt, untouched                                      vs  framed-neutral (Phase 0 replication, bridge)
If E carries the exhortation's effect, ablate_E loses against untouched max-effort (first cell) and no longer
beats neutral (third cell), while the random ablation does neither. Ablation uses each layer's own direction
(`E/layer{L}`), all positions, prompt and response (Arditi et al. style; see hooks.DirectionalAblation).
--layers restricts the ablation to a subset (e.g. 8,10,12,14,16) for a locality check.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from steering_extension.local.common import ROOT, effort_prompt, framed_neutral_prompt, make_job, task_items, write_manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vectors", type=Path, required=True)
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--task", default="essay")
    ap.add_argument("--items", type=int, default=30)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--keys", default="E,rand0", help="directions to ablate; the first is the test direction, the rest controls")
    ap.add_argument("--layers", default=None, help="comma list; default every layer")
    ap.add_argument("--cells", default="vs_effort,vs_neutral,bridge", help="which cell families to include")
    args = ap.parse_args()
    vec_rel = str(args.vectors.resolve().relative_to(ROOT)) if args.vectors.resolve().is_relative_to(ROOT) else str(args.vectors.resolve())
    layers = [int(x) for x in args.layers.split(",")] if args.layers else None
    ltag = f"_L{args.layers.replace(',', '+')}" if args.layers else ""
    keys = args.keys.split(",")
    fams = set(args.cells.split(","))
    jobs = []
    for rep in range(args.repeats):
        for row in task_items(args.task)[: args.items]:
            task = row["task"]
            eff, neu = effort_prompt(row), framed_neutral_prompt(row)
            for key in keys:
                abl = {"ablate": vec_rel, "key": key, **({"layers": layers} if layers else {})}
                cond = f"ablate_{key}{ltag}_effort"
                if "vs_effort" in fams:
                    uid = f"{cond}_vs_effort:{task}:{row['item_index']}:r{rep}"
                    jobs.append(make_job(pair_uid=uid, comparison="ablate_vs_effort", task_row=row, condition_a=cond, condition_b="effort", prompt_a=eff, prompt_b=eff, repeat=rep,
                                         extra={"steering_a": abl, "steering_b": None, "cell": f"{cond}_vs_effort"}))
                if "vs_neutral" in fams and key == keys[0]:
                    uid = f"{cond}_vs_neutral:{task}:{row['item_index']}:r{rep}"
                    jobs.append(make_job(pair_uid=uid, comparison="ablate_vs_neutral", task_row=row, condition_a=cond, condition_b="neutral", prompt_a=eff, prompt_b=neu, repeat=rep,
                                         extra={"steering_a": abl, "steering_b": None, "cell": f"{cond}_vs_neutral"}))
            if "bridge" in fams:
                uid = f"effort_vs_neutral:{task}:{row['item_index']}:r{rep}"
                jobs.append(make_job(pair_uid=uid, comparison="effort_vs_neutral", task_row=row, condition_a="effort", condition_b="neutral", prompt_a=eff, prompt_b=neu, repeat=rep,
                                     extra={"steering_a": None, "steering_b": None, "cell": "effort_vs_neutral"}))
    write_manifest(jobs, args.run_name)


if __name__ == "__main__":
    main()
