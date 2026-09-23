#!/usr/bin/env python3
"""Summarize the saved LLM stance labels without making API calls.

This script reproduces statistics from the fixed classification artifact. The
classifier prompt, lexical gate, batch design, and recorded model identifier
are preserved in ``analysis_specs/reasoning_trace_stance_classifier.md``.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import binomtest

from utility_behavior_gap.constants import ACTOR_LABEL
from utility_behavior_gap.paths import ROOT


ANALYSIS = ROOT / "outputs" / "analysis"
DEFAULT_LABELS = ANALYSIS / "incentive_belief_classification_all_traces.jsonl"
DEFAULT_PAIRS = ANALYSIS / "highlow_reasoning_traces_medium__tasks-essay__7-actors_pair_outcomes.csv"
FLAGS = ["believes", "disbelieves", "suspicious", "dismisses"]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    stream = (
        gzip.open(path, mode="rt", encoding="utf-8")
        if path.suffix == ".gz"
        else path.open(mode="rt", encoding="utf-8")
    )
    with stream as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_compact_labels(labels: pd.DataFrame, path: Path) -> None:
    """Write the saved labels without duplicating trace text stored separately."""

    columns = [
        "id",
        "actor",
        "task",
        "domain",
        "cond",
        "output_id",
        "pair_uid",
        "assigned_outcome",
        "panel_winner",
        "flag_mismatch",
        *FLAGS,
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = (
        gzip.open(path, mode="wt", encoding="utf-8")
        if path.suffix == ".gz"
        else path.open(mode="wt", encoding="utf-8")
    )
    with stream as fh:
        for record in labels[columns].to_dict(orient="records"):
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def truthy(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def exact_interval(wins: int, n: int) -> tuple[float, float, float]:
    if not n:
        return math.nan, math.nan, math.nan
    test = binomtest(wins, n, 0.5, alternative="two-sided")
    interval = test.proportion_ci(confidence_level=0.95, method="exact")
    return float(interval.low), float(interval.high), float(test.pvalue)


def summarize_flags(labels: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    stance_takers = labels[FLAGS].any(axis=1)
    stance_n = int(stance_takers.sum())
    rows: list[dict[str, Any]] = []
    actor_rows: list[dict[str, Any]] = []
    for flag in FLAGS:
        sub = labels[labels[flag]]
        rows.append(
            {
                "stance": flag,
                "n": int(len(sub)),
                "percent_of_stance_takers": 100 * len(sub) / stance_n if stance_n else math.nan,
                "high": int(sub["cond"].eq("hl_high").sum()),
                "low": int(sub["cond"].eq("hl_low").sum()),
                "flag_mismatch_rows": int(sub["flag_mismatch"].sum()),
            }
        )
        for actor, actor_sub in sub.groupby("actor", sort=True):
            actor_rows.append(
                {
                    "actor": actor,
                    "actor_label": ACTOR_LABEL.get(str(actor), str(actor)),
                    "stance": flag,
                    "n": int(len(actor_sub)),
                    "high": int(actor_sub["cond"].eq("hl_high").sum()),
                    "low": int(actor_sub["cond"].eq("hl_low").sum()),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(actor_rows)


def performance_rows(labels: pd.DataFrame, pairs: pd.DataFrame) -> pd.DataFrame:
    high_labels = labels[labels["cond"].eq("hl_high")].copy()
    if high_labels["pair_uid"].duplicated().any():
        raise RuntimeError("Saved high-side stance labels contain duplicate pair_uid values")
    keep = ["pair_uid", "flag_mismatch", *FLAGS]
    joined = pairs.merge(high_labels[keep], on="pair_uid", how="left", validate="one_to_one")
    for flag in ["flag_mismatch", *FLAGS]:
        joined[flag] = joined[flag].fillna(False).astype(bool)
    rows: list[dict[str, Any]] = []

    def add_row(label: str, mask: pd.Series) -> None:
        sub = joined[mask]
        high = int(sub["high_win"].sum())
        low = int(sub["low_win"].sum())
        ties = int(sub["tie"].sum())
        resolved = high + low
        ci_low, ci_high, p_value = exact_interval(high, resolved)
        rows.append(
            {
                "high_side_trace_category": label,
                "pairs": int(len(sub)),
                "high_wins": high,
                "low_wins": low,
                "ties": ties,
                "n_excluding_ties": resolved,
                "high_win_rate_excluding_ties": high / resolved if resolved else math.nan,
                "exact95_ci_low": ci_low,
                "exact95_ci_high": ci_high,
                "two_sided_binomial_p": p_value,
            }
        )

    for flag in FLAGS:
        add_row(flag, joined[flag])
    classified_pair_uids = set(high_labels["pair_uid"].astype(str))
    classified = joined["pair_uid"].astype(str).isin(classified_pair_uids)
    add_row(
        "neither_believes_nor_disbelieves_among_classified",
        classified & ~joined["believes"] & ~joined["disbelieves"],
    )
    add_row("all_pairs", pd.Series(True, index=joined.index))
    return pd.DataFrame(rows)


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
    lines.extend("| " + " | ".join(str(row[column]) for column in headers) + " |" for _, row in show.iterrows())
    return "\n".join(lines)


def write_summary(
    *,
    labels: pd.DataFrame,
    stance: pd.DataFrame,
    performance: pd.DataFrame,
    path: Path,
) -> None:
    stance_n = int(labels[FLAGS].any(axis=1).sum())
    lines = [
        "# Saved Reasoning-Trace Stance Labels",
        "",
        "This is a reproducible summary of the fixed LLM-classification artifact. It makes no API calls.",
        "",
        f"- lexically gated traces classified: {len(labels)}",
        f"- traces assigned at least one non-exclusive stance: {stance_n}",
        f"- rows marked `flag_mismatch`: {int(labels['flag_mismatch'].sum())}",
        "",
        "## Classifier provenance",
        "",
        "The classification used a 66-batch Claude workflow at medium reasoning effort (`wf_f3a7fe17-901`) and the recorded model identifier `claude-opus-4-8[1m]`. The exact prompt, lexical gate, batch design, response schema, and preserved inputs are documented in `analysis_specs/reasoning_trace_stance_classifier.md`.",
        "",
        "The four `flag_mismatch` rows retain their saved labels and corrected source metadata. Counts below use the corrected `cond` field in the saved artifact.",
        "",
        "## Stance counts",
        "",
        markdown_table(stance),
        "",
        "Flags are non-exclusive, so percentages do not sum to 100%.",
        "",
        "## Panel outcomes conditioned on the high-side trace",
        "",
        markdown_table(performance),
        "",
        "Confidence intervals and p-values are unadjusted exact binomial quantities and are descriptive exploratory analyses.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--pair-outcomes", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--out-prefix", default="reasoning_trace_saved_stance_labels")
    parser.add_argument(
        "--export-compact-labels",
        type=Path,
        help="Write the saved labels without duplicate reasoning text to JSONL(.gz).",
    )
    args = parser.parse_args()

    labels = pd.DataFrame(read_jsonl(args.labels))
    if len(labels) != 2620 or labels["output_id"].duplicated().any():
        raise RuntimeError(f"Expected 2,620 unique saved labels, found {len(labels)}")
    for flag in [*FLAGS, "flag_mismatch"]:
        labels[flag] = truthy(labels[flag])
    if not set(labels["cond"]).issubset({"hl_high", "hl_low"}):
        raise RuntimeError("Unexpected condition in saved stance labels")
    if args.export_compact_labels:
        write_compact_labels(labels, args.export_compact_labels)
    pairs = pd.read_csv(args.pair_outcomes)
    if len(pairs) != 2100 or pairs["pair_uid"].duplicated().any():
        raise RuntimeError(f"Expected 2,100 unique pair outcomes, found {len(pairs)}")

    stance, actor_stance = summarize_flags(labels)
    performance = performance_rows(labels, pairs)
    prefix = ANALYSIS / args.out_prefix
    stance.to_csv(f"{prefix}_counts.csv", index=False)
    actor_stance.to_csv(f"{prefix}_counts_by_actor.csv", index=False)
    performance.to_csv(f"{prefix}_conditioned_performance.csv", index=False)
    summary_path = Path(f"{prefix}_summary.md")
    write_summary(labels=labels, stance=stance, performance=performance, path=summary_path)

    print(f"stance counts: {prefix}_counts.csv")
    print(f"conditioned performance: {prefix}_conditioned_performance.csv")
    print(f"summary: {summary_path}")
    if args.export_compact_labels:
        print(f"compact saved labels: {args.export_compact_labels}")
    print(stance.to_string(index=False))
    print(performance.to_string(index=False))


if __name__ == "__main__":
    main()
