"""The paper's blind task-rubric coder applied to our steered / ablated pairs (week 8, note item 2).

Reuses the paper's code unchanged: run_task_rubric_feature_coding.code_sample_row (which builds the prompt with
run_task_rubric_pilot.rubric_prompt / task_context, calls the coder, parses and normalizes the JSON codes).
Coder google/gemini-2.5-flash, temperature 0, max_tokens 1400, as in the paper. Sides A/B are assigned at random per
pair (seeded); the coder never sees condition labels.

Each cell is a (run, cell) from outputs/steering/runs; side a of every pair is the intervened text (left), side b the
opponent (right), so "left better" = intervened text better.

Outputs in --out:
  rubric_codes.jsonl   one record per coded pair (paper's record format + run, cell, pair_uid); resumable
  rubric_summary.csv   per cell x dimension: n, delta = (share left better - share right better), bootstrap 95% CI over
                       pairs (5,000 draws), % left better, % right better, % tie or not applicable
  rubric_summary.md    the same as tables
Paid API call: run only with the PI's authorization. --dry-run builds the sample and prints the first prompt, no calls.
Run: .venv/bin/python -m steering_extension.local.rubric_judge --out outputs/steering/w8_rubric --workers 8
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from utility_behavior_gap.constants import TASK_LABEL  # noqa: E402
from utility_behavior_gap.scripts.run_task_rubric_feature_coding import code_sample_row  # noqa: E402
from utility_behavior_gap.scripts.run_task_rubric_pilot import (  # noqa: E402
    DEFAULT_CODER_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    TASK_DIMENSIONS,
    rubric_prompt,
    task_context,
)
from steering_extension.local.keys import load_keys  # noqa: E402

RUNS = ROOT / "outputs/steering/runs"
# (run, cell, label): side a = intervened (left), side b = opponent (right). Panel W/L in the plan file.
CELLS = [
    ("w6_ablation", "effort_vs_neutral", "a. max-effort prompt vs neutral prompt, untouched"),
    ("w6_sweep", "steer_E_L6_r+0.100_response", "b. add E, layer 6, +0.1 vs unsteered"),
    ("w6_sweep", "steer_E_L14_r+0.050_response", "c. add E, layer 14, +0.05 vs unsteered"),
    ("w6_sweep", "steer_E_L16_r-0.100_response", "d. remove E, layer 16, -0.1 vs unsteered"),
    ("w6_sweep", "steer_E_L10_r-0.100_response", "e. remove E, layer 10, -0.1 vs unsteered"),
    ("w6_ablation_local", "ablate_E_L8+10+12+14+16_effort_vs_effort", "f. E ablated at layers 8-16 under max-effort vs untouched max-effort"),
    ("w7_random", "steer_rand0_L6_r+0.100_response", "g1. random direction 0, layer 6, +0.1 vs unsteered"),
    ("w7_random", "steer_rand1_L6_r+0.100_response", "g2. random direction 1, layer 6, +0.1 vs unsteered"),
    ("w7_role", "world_class_vs_skilled", "h. world-class vs skilled prompts, untouched"),
    ("w7_role", "steer_E_L6_r+0.100_skilled_vs_skilled", "i. add E, layer 6, +0.1 under skilled vs untouched skilled"),
    ("w7_crossval_grant", "steer_E_L16_r-0.100_response", "j. grant: remove essay-built E, layer 16, -0.1 vs unsteered"),
]


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open()]


def build_sample(seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    for run, cell, label in CELLS:
        rd = RUNS / run
        jobs = [j for j in load_jsonl(rd / "generation_jobs.jsonl") if j.get("cell", j["comparison"]) == cell]
        gens = {g["output_id"]: g for g in load_jsonl(rd / "generations.jsonl")}
        if not jobs:
            raise SystemExit(f"no jobs for {run}/{cell}")
        for j in jobs:
            uid = j["pair_uid"]
            ida = j.get("alias_a") or f"{uid}::a"
            idb = j.get("alias_b") or f"{uid}::b"
            ta, tb = gens[ida]["output_text"], gens[idb]["output_text"]
            if not ta.strip() or not tb.strip():
                continue
            a_side = rng.choice(["left", "right"])  # which original side is shown as OUTPUT A
            task = j["task"]
            rows.append({
                "coding_pair_uid": f"{run}:{cell}:{uid}", "run": run, "cell": cell, "cell_label": label, "pair_uid": uid,
                "comparison_name": cell, "source_mode": "steering_extension", "actor": j["actor"], "task": task,
                "task_label": j.get("task_label") or TASK_LABEL.get(task, task), "item_label": j["item_label"],
                "task_context": task_context(task, j["item_label"]),
                "left_condition": j["condition_a"], "right_condition": j["condition_b"], "left_output_id": ida, "right_output_id": idb,
                "a_side": a_side, "b_side": "right" if a_side == "left" else "left",
                "output_a_id": ida if a_side == "left" else idb, "output_b_id": idb if a_side == "left" else ida,
                "output_a": ta if a_side == "left" else tb, "output_b": tb if a_side == "left" else ta,
            })
    return pd.DataFrame(rows)


def summarize(codes: list[dict], sample: pd.DataFrame, out: Path, n_boot: int = 5000, seed: int = 0) -> None:
    meta = sample.set_index("coding_pair_uid")[["run", "cell", "cell_label", "task"]]
    rng = np.random.default_rng(seed)
    rows = []
    for (run, cell), ids in meta.groupby(["run", "cell"]).groups.items():
        recs = [c for c in codes if c["coding_pair_uid"] in set(ids) and c["success"]]
        if not recs:
            continue
        label = meta.loc[list(ids)[0], "cell_label"]
        for dim in TASK_DIMENSIONS[meta.loc[list(ids)[0], "task"]]:
            score = np.array([1 if c["codes"][dim]["winner_side"] == "left" else -1 if c["codes"][dim]["winner_side"] == "right" else 0 for c in recs])
            boots = np.array([score[rng.integers(0, len(score), len(score))].mean() for _ in range(n_boot)])
            rows.append({"cell_label": label, "run": run, "cell": cell, "dimension": dim, "n": len(score), "delta": score.mean(),
                         "ci_lo": np.percentile(boots, 2.5), "ci_hi": np.percentile(boots, 97.5),
                         "pct_left_better": (score == 1).mean(), "pct_right_better": (score == -1).mean(), "pct_tie_na": (score == 0).mean()})
    S = pd.DataFrame(rows)
    S.to_csv(out / "rubric_summary.csv", index=False)
    with (out / "rubric_summary.md").open("w") as f:
        f.write("# Paper rubric coder on our pairs\n\nCoder google/gemini-2.5-flash, temperature 0, blind A/B. delta = share intervened (left) better minus share opponent (right) better; CI bootstrapped over pairs.\n\n")
        for label, g in S.groupby("cell_label", sort=False):
            f.write(f"## {label}\n\n| marker | delta | 95% CI | % intervened better | % opponent better | % tie/NA | n |\n|---|---|---|---|---|---|---|\n")
            for _, r in g.iterrows():
                f.write(f"| {r.dimension} | {r.delta:+.2f} | [{r.ci_lo:+.2f}, {r.ci_hi:+.2f}] | {100 * r.pct_left_better:.0f}% | {100 * r.pct_right_better:.0f}% | {100 * r.pct_tie_na:.0f}% | {r.n} |\n")
            f.write("\n")
    pd.set_option("display.width", 250)
    print(S.round(2).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/steering/w8_rubric")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261106)
    ap.add_argument("--limit", type=int, default=None, help="code only the first N pairs (smoke test)")
    ap.add_argument("--dry-run", action="store_true", help="build the sample, print the first prompt, no API calls")
    ap.add_argument("--summarize-only", action="store_true")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    sample = build_sample(args.seed)
    sample.drop(columns=["output_a", "output_b", "task_context"]).to_csv(args.out / "rubric_sample.csv", index=False)
    print(f"sample: {len(sample)} pairs over {sample.cell.nunique()} cells")
    codes_path = args.out / "rubric_codes.jsonl"
    codes = load_jsonl(codes_path) if codes_path.exists() else []
    if args.dry_run:
        print(rubric_prompt(sample.iloc[0], TASK_DIMENSIONS[sample.iloc[0]["task"]])[:1500])
        return
    if not args.summarize_only:
        load_keys()
        done = {c["coding_pair_uid"] for c in codes if c["success"]}
        todo = [r for r in sample.to_dict(orient="records") if r["coding_pair_uid"] not in done]
        if args.limit:
            todo = todo[: args.limit]
        print(f"coding {len(todo)} pairs ({len(done)} already done)")
        cost = 0.0
        with ThreadPoolExecutor(max_workers=args.workers) as ex, codes_path.open("a") as f:
            futs = {ex.submit(code_sample_row, row_dict=r, coder_model=DEFAULT_CODER_MODEL, temperature=DEFAULT_TEMPERATURE, max_tokens=DEFAULT_MAX_TOKENS, timeout_s=120.0): r for r in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                rec = fut.result()
                r = futs[fut]
                rec.update({"run": r["run"], "cell": r["cell"], "pair_uid": r["pair_uid"]})
                rec.pop("request", None)  # the prompt holds both full texts; the sample csv + run dirs reconstruct it
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                codes.append(rec)
                cost += float((rec.get("usage") or {}).get("cost") or 0)
                if i % 50 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)} coded, cost so far ${cost:.2f}", flush=True)
        failed = [c for c in codes if not c["success"]]
        print(f"done: {len([c for c in codes if c['success']])} success, {len(failed)} failed, this run ${cost:.2f}")
    summarize([c for c in codes if c["success"]], sample, args.out)


if __name__ == "__main__":
    main()
