#!/usr/bin/env python3
"""Analyze the fixed Qwen3.5 reasoning-stance follow-up and archived run."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import binomtest, fisher_exact

from utility_behavior_gap.io_utils import read_jsonl
from utility_behavior_gap.job_builder import build_generation_jobs
from utility_behavior_gap.paths import ANALYSIS, ROOT
from utility_behavior_gap.scripts.analyze_highlow_reasoning import build_pair_rows


ACTOR = "qwen3.5-9b-or"
COMPARISON = "qwen35_reasoning_stance_followup"
OLD_PAIRS = ANALYSIS / "highlow_reasoning_traces_medium__tasks-essay__7-actors_pair_outcomes.csv"
ARCHIVED_LOCAL_LABELS = ANALYSIS / "reasoning_trace_saved_stance_labels.jsonl.gz"
FOLLOWUP_LOCAL_LABELS = ANALYSIS / "incentive_belief_qwen9b_followup_traces.jsonl"
PAPER_OUT = ROOT / "CURRENT_PAPER" / "results" / "reasoning_trace"
FLAGS = ("believes", "disbelieves", "suspicious", "dismisses")
BOOTSTRAP_SEED = 20260915
BOOTSTRAP_REPS = 10_000


def read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    stream = gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open(encoding="utf-8")
    with stream as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl_gz(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            for row in rows:
                zipped.write((json.dumps(row, sort_keys=True) + "\n").encode("utf-8"))


def old_pair_metadata() -> pd.DataFrame:
    jobs = build_generation_jobs(
        comparisons={"modgrid_essay_highlow_reasoning_traces_medium"},
        tasks={"essay"},
        actors={ACTOR},
        system_repeats=10,
    )
    if len(jobs) != 300:
        raise RuntimeError(f"Expected 300 reconstructed archived jobs, found {len(jobs)}")
    return pd.DataFrame(
        {
            "pair_uid": job["pair_uid"],
            "utility_pair_id": f"{job['domain']}:p{int(job['pair_idx']):02d}",
            "topic": job["item_label"],
            "pair_idx": int(job["pair_idx"]),
        }
        for job in jobs
    )


def new_pair_metadata(manifest: Path) -> pd.DataFrame:
    jobs = read_jsonl(manifest)
    if len(jobs) != 1620:
        raise RuntimeError(f"Expected 1,620 follow-up jobs, found {len(jobs)}")
    return pd.DataFrame(
        {
            "pair_uid": job["pair_uid"],
            "utility_pair_id": f"{job['domain']}:p{int(job['pair_idx']):02d}",
            "topic": job["item_label"],
            "pair_idx": int(job["pair_idx"]),
        }
        for job in jobs
    )


def load_pairs(run_dir: Path) -> pd.DataFrame:
    old = pd.read_csv(OLD_PAIRS)
    old = old[old["actor"].eq(ACTOR)].copy()
    if len(old) != 300:
        raise RuntimeError(f"Expected 300 archived Qwen pair outcomes, found {len(old)}")
    old = old.merge(old_pair_metadata(), on="pair_uid", how="left", validate="one_to_one")
    old["cohort"] = "archived_300"

    manifest = run_dir / "generation_jobs.jsonl"
    new, audit = build_pair_rows([manifest], comparison_suffix=COMPARISON)
    audit_counts = audit["status"].value_counts().to_dict()
    if len(new) != 1620 or audit_counts != {"included": 1620}:
        raise RuntimeError(
            f"Follow-up is not analysis-complete: included={len(new)}, audit={audit_counts}"
        )
    new = new.merge(new_pair_metadata(manifest), on="pair_uid", how="left", validate="one_to_one")
    new["cohort"] = "followup_1620"
    pairs = pd.concat([old, new], ignore_index=True, sort=False)
    if len(pairs) != 1920 or pairs["pair_uid"].duplicated().any():
        raise RuntimeError("Combined pair dataset is not 1,920 unique comparisons")
    return pairs


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_local_labels(
    pairs: pd.DataFrame,
    *,
    archived_path: Path,
    followup_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load only the preserved local Opus labels for each cohort."""
    archived_all = pd.DataFrame(read_jsonl_gz(archived_path))
    followup = pd.DataFrame(read_jsonl_gz(followup_path))
    required = {"output_id", *FLAGS}
    for name, frame in (("archived", archived_all), ("followup", followup)):
        missing = required - set(frame.columns)
        if missing:
            raise RuntimeError(f"{name} local labels lack required fields: {sorted(missing)}")
        if frame["output_id"].duplicated().any():
            raise RuntimeError(f"{name} local labels contain duplicate output IDs")
        for flag in FLAGS:
            bad = ~frame[flag].map(lambda value: isinstance(value, (bool, np.bool_)))
            if bad.any():
                raise RuntimeError(f"{name} local labels contain non-boolean {flag} values")

    old_pairs = pairs[pairs["cohort"].eq("archived_300")]
    new_pairs = pairs[pairs["cohort"].eq("followup_1620")]
    old_ids = set(old_pairs["high_output_id"]) | set(old_pairs["low_output_id"])
    new_ids = set(new_pairs["high_output_id"]) | set(new_pairs["low_output_id"])
    archived = archived_all[archived_all["output_id"].isin(old_ids)].copy()
    followup_ids = set(followup["output_id"])
    if followup_ids - new_ids:
        raise RuntimeError(
            f"Follow-up local labels include {len(followup_ids - new_ids)} IDs outside the fixed follow-up"
        )
    if set(archived["output_id"]) & followup_ids:
        raise RuntimeError("Archived and follow-up local labels overlap")

    archived["label_source"] = "archived_local_opus"
    followup["label_source"] = "followup_local_opus"
    labels = pd.concat([archived, followup], ignore_index=True, sort=False)
    audit = {
        "archived_labels_path": str(archived_path.resolve()),
        "archived_labels_sha256": sha256(archived_path),
        "followup_labels_path": str(followup_path.resolve()),
        "followup_labels_sha256": sha256(followup_path),
        "api_opus_labels_used": False,
        "archived_traces": len(old_ids),
        "archived_locally_classified_traces": len(archived),
        "archived_unclassified_traces": len(old_ids) - len(archived),
        "followup_traces": len(new_ids),
        "followup_locally_classified_traces": len(followup),
        "followup_unclassified_traces": len(new_ids) - len(followup),
    }
    return labels, audit


def join_labels(pairs: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    if labels.empty or labels["output_id"].duplicated().any():
        raise RuntimeError("Missing or duplicate stance labels")
    for flag in FLAGS:
        labels[flag] = labels[flag].astype(bool)
    label_cols = ["output_id", "label_source", *FLAGS]
    high = labels[label_cols].add_prefix("high_").rename(columns={"high_output_id": "high_output_id"})
    low = labels[label_cols].add_prefix("low_").rename(columns={"low_output_id": "low_output_id"})
    joined = pairs.merge(high, on="high_output_id", how="left", validate="many_to_one")
    joined = joined.merge(low, on="low_output_id", how="left", validate="many_to_one")
    joined["both_traces_classified"] = joined["high_believes"].notna() & joined["low_believes"].notna()
    for side in ("high", "low"):
        for flag in FLAGS:
            joined[f"{side}_{flag}"] = joined[f"{side}_{flag}"].fillna(False).astype(bool)
    joined["either_disbelieves"] = joined["high_disbelieves"] | joined["low_disbelieves"]
    joined["either_suspicious_or_disbelieves"] = (
        joined["high_suspicious"]
        | joined["low_suspicious"]
        | joined["either_disbelieves"]
    )
    return joined


def exact_intervals(wins: int, n: int) -> tuple[float, float, float, float, float]:
    if not n:
        return (math.nan,) * 5
    nominal = binomtest(wins, n, 0.5).proportion_ci(0.95, method="exact")
    familywise = binomtest(wins, n, 0.5).proportion_ci(1 - 0.05 / 7, method="exact")
    p = float(binomtest(wins, n, 0.5, alternative="two-sided").pvalue)
    return float(nominal.low), float(nominal.high), float(familywise.low), float(familywise.high), p


def crossed_cluster_bootstrap(
    rows: pd.DataFrame, *, reps: int = BOOTSTRAP_REPS, seed: int = BOOTSTRAP_SEED
) -> tuple[float, float]:
    resolved = rows[rows["resolved_excluding_ties"].eq(1)].copy()
    if resolved.empty:
        return math.nan, math.nan
    pair_ids = sorted(resolved["utility_pair_id"].unique())
    topics = sorted(resolved["topic"].unique())
    pair_codes = pd.Categorical(resolved["utility_pair_id"], categories=pair_ids).codes
    topic_codes = pd.Categorical(resolved["topic"], categories=topics).codes
    outcomes = resolved["high_win"].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    estimates: list[float] = []
    for _ in range(reps):
        pair_weights = np.bincount(
            rng.integers(0, len(pair_ids), len(pair_ids)), minlength=len(pair_ids)
        )
        topic_weights = np.bincount(
            rng.integers(0, len(topics), len(topics)), minlength=len(topics)
        )
        weights = pair_weights[pair_codes] * topic_weights[topic_codes]
        denominator = float(weights.sum())
        if denominator:
            estimates.append(float(np.dot(weights, outcomes) / denominator))
    if not estimates:
        return math.nan, math.nan
    return tuple(float(value) for value in np.quantile(estimates, [0.025, 0.975]))


def estimate(
    rows: pd.DataFrame, *, bootstrap: bool, bootstrap_reps: int
) -> dict[str, Any]:
    high = int(rows["high_win"].sum())
    low = int(rows["low_win"].sum())
    ties = int(rows["tie"].sum())
    resolved = high + low
    ci_low, ci_high, fw_low, fw_high, p = exact_intervals(high, resolved)
    cluster_low, cluster_high = (
        crossed_cluster_bootstrap(rows, reps=bootstrap_reps)
        if bootstrap
        else (math.nan, math.nan)
    )
    return {
        "pairs": len(rows),
        "high_wins": high,
        "low_wins": low,
        "ties": ties,
        "resolved": resolved,
        "high_win_rate": high / resolved if resolved else math.nan,
        "exact95_ci_low": ci_low,
        "exact95_ci_high": ci_high,
        "seven_model_fwer95_ci_low": fw_low,
        "seven_model_fwer95_ci_high": fw_high,
        "two_sided_exact_p": p,
        "crossed_cluster95_ci_low": cluster_low,
        "crossed_cluster95_ci_high": cluster_high,
    }


def sample_masks(rows: pd.DataFrame) -> dict[str, pd.Series]:
    classified = rows["both_traces_classified"]
    return {
        "all_pairs": pd.Series(True, index=rows.index),
        "both_traces_classified": classified,
        # Match the original appendix convention: a trace without a returned
        # classifier label has no recorded positive flag.
        "exclude_explicit_disbelief": ~rows["either_disbelieves"],
        "exclude_suspicion_or_disbelief": ~rows["either_suspicious_or_disbelieves"],
        "classified_exclude_explicit_disbelief": classified
        & ~rows["either_disbelieves"],
        "classified_exclude_suspicion_or_disbelief": classified
        & ~rows["either_suspicious_or_disbelieves"],
    }


def summary_rows(rows: pd.DataFrame, *, bootstrap_reps: int) -> pd.DataFrame:
    out: list[dict[str, Any]] = []
    cohorts = {
        "archived_300": rows[rows["cohort"].eq("archived_300")],
        "followup_1620": rows[rows["cohort"].eq("followup_1620")],
        "combined_1920": rows,
    }
    for cohort, cohort_rows in cohorts.items():
        for sample, mask in sample_masks(cohort_rows).items():
            sub = cohort_rows[mask]
            out.append(
                {
                    "cohort": cohort,
                    "scope": "overall",
                    "domain": "all",
                    "sample": sample,
                    **estimate(
                        sub,
                        bootstrap=cohort == "combined_1920",
                        bootstrap_reps=bootstrap_reps,
                    ),
                }
            )
            if cohort == "combined_1920":
                for domain, domain_rows in sub.groupby("domain", sort=True):
                    out.append(
                        {
                            "cohort": cohort,
                            "scope": "domain",
                            "domain": domain,
                            "sample": sample,
                            **estimate(
                                domain_rows,
                                bootstrap=False,
                                bootstrap_reps=bootstrap_reps,
                            ),
                        }
                    )
    return pd.DataFrame(out)


def pattern_rows(rows: pd.DataFrame, flag: str, *, bootstrap_reps: int) -> pd.DataFrame:
    classified = rows[rows["both_traces_classified"]].copy()
    high_flag = classified[f"high_{flag}"]
    low_flag = classified[f"low_{flag}"]
    patterns = {
        "neither": ~high_flag & ~low_flag,
        "high_only": high_flag & ~low_flag,
        "low_only": ~high_flag & low_flag,
        "both": high_flag & low_flag,
    }
    return pd.DataFrame(
        {
            "flag": flag,
            "pattern": name,
            **estimate(
                classified[mask],
                bootstrap=False,
                bootstrap_reps=bootstrap_reps,
            ),
        }
        for name, mask in patterns.items()
    )


def pattern_contrast_rows(rows: pd.DataFrame) -> pd.DataFrame:
    classified = rows[
        rows["both_traces_classified"] & rows["resolved_excluding_ties"].eq(1)
    ]
    records: list[dict[str, Any]] = []
    for flag in ("believes", "disbelieves", "suspicious"):
        high_only = classified[
            classified[f"high_{flag}"] & ~classified[f"low_{flag}"]
        ]
        low_only = classified[
            ~classified[f"high_{flag}"] & classified[f"low_{flag}"]
        ]
        table = [
            [int(high_only["high_win"].sum()), int(high_only["low_win"].sum())],
            [int(low_only["high_win"].sum()), int(low_only["low_win"].sum())],
        ]
        odds, p_value = (
            fisher_exact(table, alternative="two-sided")
            if len(high_only) and len(low_only)
            else (math.nan, math.nan)
        )
        high_rate = (
            float(high_only["high_win"].mean()) if len(high_only) else math.nan
        )
        low_rate = float(low_only["high_win"].mean()) if len(low_only) else math.nan
        records.append(
            {
                "flag": flag,
                "high_only_resolved": len(high_only),
                "high_only_high_win_rate": high_rate,
                "low_only_resolved": len(low_only),
                "low_only_high_win_rate": low_rate,
                "high_only_minus_low_only": (
                    high_rate - low_rate
                    if not math.isnan(high_rate) and not math.isnan(low_rate)
                    else math.nan
                ),
                "fisher_exact_odds_ratio": float(odds),
                "fisher_exact_p": float(p_value),
            }
        )
    return pd.DataFrame(records)


def flagged_difference(rows: pd.DataFrame) -> pd.DataFrame:
    classified = rows[rows["both_traces_classified"] & rows["resolved_excluding_ties"].eq(1)]
    records: list[dict[str, Any]] = []
    for flag, flagged in {
        "explicit_disbelief": classified["either_disbelieves"],
        "suspicion_or_disbelief": classified["either_suspicious_or_disbelieves"],
    }.items():
        a, b = classified[flagged], classified[~flagged]
        table = [
            [int(a["high_win"].sum()), int(a["low_win"].sum())],
            [int(b["high_win"].sum()), int(b["low_win"].sum())],
        ]
        odds, p = fisher_exact(table, alternative="two-sided")
        records.append(
            {
                "flag": flag,
                "flagged_resolved": len(a),
                "flagged_high_win_rate": float(a["high_win"].mean()) if len(a) else math.nan,
                "unflagged_resolved": len(b),
                "unflagged_high_win_rate": float(b["high_win"].mean()) if len(b) else math.nan,
                "difference_flagged_minus_unflagged": (
                    float(a["high_win"].mean() - b["high_win"].mean()) if len(a) and len(b) else math.nan
                ),
                "fisher_exact_odds_ratio": float(odds),
                "fisher_exact_p": float(p),
            }
        )
    return pd.DataFrame(records)


def markdown_table(df: pd.DataFrame) -> str:
    show = df.copy()
    for column in show.columns:
        if pd.api.types.is_float_dtype(show[column]):
            show[column] = show[column].map(lambda value: "" if pd.isna(value) else f"{value:.3f}")
    headers = list(show.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(row[column]) for column in headers) + " |"
        for _, row in show.iterrows()
    )
    return "\n".join(lines)


def write_summary(
    summary: pd.DataFrame,
    patterns: pd.DataFrame,
    pattern_contrasts: pd.DataFrame,
    differences: pd.DataFrame,
    audit: dict[str, Any],
    path: Path,
) -> None:
    overall = summary[summary["scope"].eq("overall")][
        [
            "cohort",
            "sample",
            "pairs",
            "high_wins",
            "low_wins",
            "ties",
            "resolved",
            "high_win_rate",
            "exact95_ci_low",
            "exact95_ci_high",
            "crossed_cluster95_ci_low",
            "crossed_cluster95_ci_high",
        ]
    ]
    domain = summary[summary["scope"].eq("domain")][
        ["domain", "sample", "pairs", "high_wins", "low_wins", "ties", "resolved", "high_win_rate", "exact95_ci_low", "exact95_ci_high"]
    ]
    lines = [
        "# Qwen3.5 Reasoning-Stance Follow-up",
        "",
        "The fixed follow-up adds 1,620 comparisons to the archived 300. The combined design presents every one of 80 utility pairs per domain on six distinct essay topics and contains 16 comparisons in every topic-by-domain cell.",
        "",
        "Win rates exclude panel ties. Exact 95% intervals are the targeted Qwen-only intervals. The combined overall rows also report a crossed utility-pair/topic bootstrap interval. Seven-model familywise intervals remain available in the CSV for comparison with the original lollipop figure.",
        "",
        "Suspicion/disbelief exclusions are post-treatment sensitivity analyses, not causal estimands.",
        "All stance labels in this analysis were produced locally. No API-Opus classifications were used. The archived cohort has "
        f"{audit['archived_locally_classified_traces']}/{audit['archived_traces']} classified traces; the follow-up has "
        f"{audit['followup_locally_classified_traces']}/{audit['followup_traces']}. As in the original appendix, the primary exclusion rows treat traces without a returned classifier label as having no recorded positive flag. Rows prefixed `classified_` instead require both traces in a pair to have returned labels.",
        "",
        "## Overall",
        "",
        markdown_table(overall),
        "",
        "## Combined By Domain",
        "",
        markdown_table(domain),
        "",
        "## Side-Specific Stance Patterns",
        "",
        markdown_table(patterns),
        "",
        "## High-Only Versus Low-Only Stance",
        "",
        "If explicit belief amplifies the assigned incentive, the high-side win rate should be higher when only the high trace believes than when only the low trace believes.",
        "",
        markdown_table(pattern_contrasts),
        "",
        "## Flagged Versus Unflagged Resolved Comparisons",
        "",
        markdown_table(differences),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--pair-inputs", type=Path, help="Frozen pair outcomes and design metadata; no raw runs required.")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--copy-current-paper", action="store_true")
    parser.add_argument("--archived-labels", type=Path, default=ARCHIVED_LOCAL_LABELS)
    parser.add_argument("--followup-labels", type=Path, default=FOLLOWUP_LOCAL_LABELS)
    parser.add_argument("--bootstrap-reps", type=int, default=BOOTSTRAP_REPS)
    args = parser.parse_args()
    if args.pair_inputs:
        raw_pairs = pd.read_csv(args.pair_inputs)
        if len(raw_pairs) != 1920 or raw_pairs["pair_uid"].duplicated().any():
            raise ValueError("Expected 1,920 unique frozen Qwen comparisons")
        if not args.output_dir:
            parser.error("--pair-inputs requires --output-dir")
        out_dir = args.output_dir
    else:
        if not args.run_dir:
            parser.error("Provide --pair-inputs or an explicit --run-dir")
        raw_pairs = load_pairs(args.run_dir)
        out_dir = args.output_dir or args.run_dir / "analysis"
    labels, label_audit = load_local_labels(
        raw_pairs,
        archived_path=args.archived_labels,
        followup_path=args.followup_labels,
    )
    pairs = join_labels(raw_pairs, labels)
    label_audit.update(
        {
            "archived_pairs_with_both_traces_classified": int(
                pairs.loc[pairs["cohort"].eq("archived_300"), "both_traces_classified"].sum()
            ),
            "followup_pairs_with_both_traces_classified": int(
                pairs.loc[pairs["cohort"].eq("followup_1620"), "both_traces_classified"].sum()
            ),
            "combined_pairs_with_both_traces_classified": int(pairs["both_traces_classified"].sum()),
        }
    )
    summary = summary_rows(pairs, bootstrap_reps=args.bootstrap_reps)
    patterns = pd.concat(
        [
            pattern_rows(pairs, flag, bootstrap_reps=args.bootstrap_reps)
            for flag in ("believes", "disbelieves", "suspicious")
        ],
        ignore_index=True,
    )
    pattern_contrasts = pattern_contrast_rows(pairs)
    differences = flagged_difference(pairs)

    out_dir.mkdir(parents=True, exist_ok=True)
    compact_label_columns = [
        "output_id",
        "pair_uid",
        "cond",
        "domain",
        "label_source",
        *FLAGS,
        "evidence",
    ]
    compact_labels = labels[
        [column for column in compact_label_columns if column in labels.columns]
    ].to_dict(orient="records")
    compact_labels_path = out_dir / "qwen35_reasoning_stance_combined_local_labels.jsonl.gz"
    write_jsonl_gz(compact_labels_path, compact_labels)
    label_audit.update(
        {
            "combined_compact_labels_path": str(compact_labels_path.resolve()),
            "combined_compact_labels_sha256": sha256(compact_labels_path),
            "combined_compact_label_rows": len(compact_labels),
        }
    )
    summary.to_csv(out_dir / "qwen35_reasoning_stance_summary.csv", index=False)
    patterns.to_csv(out_dir / "qwen35_reasoning_stance_patterns.csv", index=False)
    pattern_contrasts.to_csv(
        out_dir / "qwen35_reasoning_stance_pattern_contrasts.csv", index=False
    )
    differences.to_csv(out_dir / "qwen35_reasoning_stance_flagged_difference.csv", index=False)
    pairs.to_csv(out_dir / "qwen35_reasoning_stance_pair_outcomes.csv", index=False)
    (out_dir / "qwen35_reasoning_stance_label_audit.json").write_text(
        json.dumps(label_audit, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_summary(
        summary,
        patterns,
        pattern_contrasts,
        differences,
        label_audit,
        out_dir / "qwen35_reasoning_stance_summary.md",
    )

    if not args.copy_current_paper:
        print(f"summary: {out_dir / 'qwen35_reasoning_stance_summary.md'}")
        return
    PAPER_OUT.mkdir(parents=True, exist_ok=True)
    for filename in (
        "qwen35_reasoning_stance_summary.csv",
        "qwen35_reasoning_stance_patterns.csv",
        "qwen35_reasoning_stance_pattern_contrasts.csv",
        "qwen35_reasoning_stance_flagged_difference.csv",
        "qwen35_reasoning_stance_label_audit.json",
        "qwen35_reasoning_stance_combined_local_labels.jsonl.gz",
        "qwen35_reasoning_stance_summary.md",
    ):
        (PAPER_OUT / filename).write_bytes((out_dir / filename).read_bytes())
    print(f"summary: {out_dir / 'qwen35_reasoning_stance_summary.md'}")
    print(f"paper-ready: {PAPER_OUT / 'qwen35_reasoning_stance_summary.md'}")


if __name__ == "__main__":
    main()
