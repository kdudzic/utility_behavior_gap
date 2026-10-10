"""Per-cell win rates from a run's judge_votes.jsonl using the paper's conventions:
majority of three judges, each judge's two presentation orders collapsed (flip -> tie),
panel ties excluded, exact binomial (Clopper-Pearson) 95% CI; plus length and coherence
summaries per condition. Writes <run_dir>/cell_summary.csv and prints a table."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from scipy.stats import beta, binomtest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from utility_behavior_gap.judging import derive_judge_verdict, derive_panel_winner_condition  # noqa: E402


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    lo = beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return (float(lo), float(hi))


def load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open()] if path.exists() else []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--group-by", default="condition_a", help="job field that defines a cell (condition_a or comparison)")
    args = ap.parse_args()
    jobs = {j["pair_uid"]: j for j in load(args.run_dir / "generation_jobs.jsonl")}
    votes = load(args.run_dir / "judge_votes.jsonl")
    gens = {g["output_id"]: g for g in load(args.run_dir / "generations.jsonl")}
    coh = {c["output_id"]: c["coherence"] for c in load(args.run_dir / "coherence.jsonl") if c.get("coherence") is not None}
    by_pair_judge: dict[tuple[str, str], list[str]] = defaultdict(list)
    for v in votes:
        if v.get("success") is False:
            continue
        by_pair_judge[(v["pair_uid"], v["judge_model"])].append(v["winner_condition"])
    panel: dict[str, str] = {}
    for pair_uid in {k[0] for k in by_pair_judge}:
        job = jobs[pair_uid]
        judge_verdicts = [derive_judge_verdict(by_pair_judge[(pair_uid, jm)]) for (p, jm) in by_pair_judge if p == pair_uid]
        panel[pair_uid] = derive_panel_winner_condition(job, judge_verdicts)
    cells: dict[str, dict] = defaultdict(lambda: {"win": 0, "loss": 0, "tie": 0, "len_a": [], "len_b": [], "coh_a": [], "coh_b": [], "trunc_a": 0, "n_pairs": 0})
    for pair_uid, job in jobs.items():
        cell = job.get(args.group_by, "")
        c = cells[cell]
        c["n_pairs"] += 1
        ga, gb = gens.get(f"{pair_uid}::a"), gens.get(f"{pair_uid}::b")
        if ga:
            c["len_a"].append(len(ga["output_text"].split()))
            c["trunc_a"] += ga.get("finish_reason") == "length"
            if ga["output_id"] in coh:
                c["coh_a"].append(coh[ga["output_id"]])
        if gb:
            c["len_b"].append(len(gb["output_text"].split()))
            if gb["output_id"] in coh:
                c["coh_b"].append(coh[gb["output_id"]])
        w = panel.get(pair_uid)
        if w is None:
            continue
        if w == job["condition_a"]:
            c["win"] += 1
        elif w == job["condition_b"]:
            c["loss"] += 1
        else:
            c["tie"] += 1
    out_rows = []
    hdr = f"{'cell':44s} {'n':>4s} {'W':>3s} {'L':>3s} {'T':>3s} {'win%':>6s} {'CI95':>13s} {'p':>7s} {'len_a':>6s} {'len_b':>6s} {'coh_a':>6s} {'coh_b':>6s} {'tr_a':>4s}"
    print(hdr)
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")  # noqa: E731
    for cell, c in sorted(cells.items()):
        n = c["win"] + c["loss"]
        rate = c["win"] / n if n else float("nan")
        lo, hi = clopper_pearson(c["win"], n)
        p = binomtest(c["win"], n, 0.5).pvalue if n else float("nan")
        row = {"cell": cell, "n_pairs": c["n_pairs"], "wins": c["win"], "losses": c["loss"], "ties": c["tie"], "win_rate": rate, "ci_lo": lo, "ci_hi": hi, "p_two_sided": p, "mean_words_a": mean(c["len_a"]), "mean_words_b": mean(c["len_b"]), "coherence_a": mean(c["coh_a"]), "coherence_b": mean(c["coh_b"]), "truncated_a": c["trunc_a"]}
        out_rows.append(row)
        print(f"{cell:44s} {n:4d} {c['win']:3d} {c['loss']:3d} {c['tie']:3d} {rate*100:6.1f} [{lo:.2f},{hi:.2f}] {p:7.3f} {row['mean_words_a']:6.0f} {row['mean_words_b']:6.0f} {row['coherence_a']:6.1f} {row['coherence_b']:6.1f} {c['trunc_a']:4d}")
    import csv
    with (args.run_dir / "cell_summary.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)


if __name__ == "__main__":
    main()
