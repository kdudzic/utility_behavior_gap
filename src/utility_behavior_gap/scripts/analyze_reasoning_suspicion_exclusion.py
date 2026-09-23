#!/usr/bin/env python3
"""Test the high-low result after excluding traces marked suspicious or disbelieving.

This is a post-treatment sensitivity analysis. A pair is excluded when either
the high-side or low-side returned reasoning trace was classified as
``suspicious`` or ``disbelieves``. Traces outside the original lexical gate
have no saved LLM label and are treated as having no recorded flag.
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

from utility_behavior_gap.paths import ROOT


DEFAULT_PAIRS = (
    ROOT
    / "outputs"
    / "analysis"
    / "highlow_reasoning_traces_medium__tasks-essay__7-actors_pair_outcomes.csv"
)
DEFAULT_LABELS = ROOT / "outputs" / "analysis" / "incentive_belief_classification_all_traces.jsonl"
DEFAULT_QWEN_FOLLOWUP = (
    ROOT
    / "CURRENT_PAPER"
    / "results"
    / "reasoning_trace"
    / "qwen35_reasoning_stance_summary.csv"
)
DEFAULT_OUTPUT_DIR = ROOT / "CURRENT_PAPER" / "results" / "reasoning_trace"
OUTPUT_STEM = "reasoning_suspicion_disbelief_exclusion"
N_MODELS = 7


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    stream = (
        gzip.open(path, mode="rt", encoding="utf-8")
        if path.suffix == ".gz"
        else path.open(mode="rt", encoding="utf-8")
    )
    with stream as fh:
        return [json.loads(line) for line in fh if line.strip()]


def truthy(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def exact_familywise_ci(wins: int, n: int) -> tuple[float, float]:
    """Exact two-sided CI with Bonferroni familywise coverage over seven models."""

    if not n:
        return math.nan, math.nan
    interval = binomtest(wins, n, 0.5).proportion_ci(
        confidence_level=1.0 - 0.05 / N_MODELS,
        method="exact",
    )
    return float(interval.low), float(interval.high)


def holm_adjust(p_values: list[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [math.nan] * len(p_values)
    running = 0.0
    m = len(p_values)
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p_values[index]))
        adjusted[index] = running
    return adjusted


def estimate(sub: pd.DataFrame) -> dict[str, Any]:
    high = int(sub["high_win"].sum())
    low = int(sub["low_win"].sum())
    ties = int(sub["tie"].sum())
    resolved = high + low
    ci_low, ci_high = exact_familywise_ci(high, resolved)
    p_value = (
        float(binomtest(high, resolved, 0.5, alternative="greater").pvalue)
        if resolved
        else math.nan
    )
    return {
        "pairs": int(len(sub)),
        "high_wins": high,
        "low_wins": low,
        "ties": ties,
        "resolved_excluding_ties": resolved,
        "high_win_rate_excluding_ties": high / resolved if resolved else math.nan,
        "fwer95_ci_low": ci_low,
        "fwer95_ci_high": ci_high,
        "one_sided_binomial_p": p_value,
    }


def replace_qwen_with_followup(
    results: pd.DataFrame, qwen_followup: pd.DataFrame
) -> pd.DataFrame:
    samples = {"all_pairs", "exclude_suspicion_or_disbelief"}
    qwen = qwen_followup[
        qwen_followup["cohort"].eq("combined_1920")
        & qwen_followup["scope"].eq("overall")
        & qwen_followup["domain"].eq("all")
        & qwen_followup["sample"].isin(samples)
    ].copy()
    if set(qwen["sample"]) != samples or len(qwen) != 2:
        raise RuntimeError("Qwen follow-up summary lacks the two combined overall rows")

    qwen = qwen.set_index("sample")
    full_pairs = int(qwen.loc["all_pairs", "pairs"])
    if full_pairs != 1920:
        raise RuntimeError(f"Expected 1,920 combined Qwen pairs, found {full_pairs}")

    updated = results.copy()
    for sample in samples:
        source = qwen.loc[sample]
        high = int(source["high_wins"])
        low = int(source["low_wins"])
        resolved = high + low
        target = updated["actor"].eq("qwen3.5-9b-or") & updated["sample"].eq(sample)
        if int(target.sum()) != 1:
            raise RuntimeError(f"Expected one Qwen target row for {sample}")
        pairs = int(source["pairs"])
        updated.loc[target, "pairs_excluded"] = 0 if sample == "all_pairs" else full_pairs - pairs
        updated.loc[target, "pairs"] = pairs
        updated.loc[target, "high_wins"] = high
        updated.loc[target, "low_wins"] = low
        updated.loc[target, "ties"] = int(source["ties"])
        updated.loc[target, "resolved_excluding_ties"] = resolved
        updated.loc[target, "high_win_rate_excluding_ties"] = float(source["high_win_rate"])
        updated.loc[target, "fwer95_ci_low"] = float(source["seven_model_fwer95_ci_low"])
        updated.loc[target, "fwer95_ci_high"] = float(source["seven_model_fwer95_ci_high"])
        updated.loc[target, "one_sided_binomial_p"] = float(
            binomtest(high, resolved, 0.5, alternative="greater").pvalue
        )
    return updated


def analyze(
    pairs: pd.DataFrame,
    labels: pd.DataFrame,
    qwen_followup: pd.DataFrame,
) -> pd.DataFrame:
    if len(pairs) != 2100 or pairs["pair_uid"].duplicated().any():
        raise RuntimeError(f"Expected 2,100 unique pair outcomes, found {len(pairs)}")
    if len(labels) != 2620 or labels["output_id"].duplicated().any():
        raise RuntimeError(f"Expected 2,620 unique saved labels, found {len(labels)}")

    for flag in ["suspicious", "disbelieves"]:
        labels[flag] = truthy(labels[flag])
    flagged_ids = set(
        labels.loc[labels["suspicious"] | labels["disbelieves"], "output_id"].astype(str)
    )
    pairs = pairs.copy()
    pairs["excluded_suspicion_or_disbelief"] = (
        pairs["high_output_id"].astype(str).isin(flagged_ids)
        | pairs["low_output_id"].astype(str).isin(flagged_ids)
    )

    rows: list[dict[str, Any]] = []
    for actor, actor_pairs in pairs.groupby("actor", sort=False):
        actor_label = str(actor_pairs["actor_label"].iloc[0])
        excluded = int(actor_pairs["excluded_suspicion_or_disbelief"].sum())
        for sample, sample_pairs in (
            ("all_pairs", actor_pairs),
            (
                "exclude_suspicion_or_disbelief",
                actor_pairs[~actor_pairs["excluded_suspicion_or_disbelief"]],
            ),
        ):
            rows.append(
                {
                    "actor": actor,
                    "actor_label": actor_label,
                    "sample": sample,
                    "pairs_excluded": 0 if sample == "all_pairs" else excluded,
                    **estimate(sample_pairs),
                }
            )

    results = replace_qwen_with_followup(pd.DataFrame(rows), qwen_followup)
    for sample in results["sample"].unique():
        mask = results["sample"].eq(sample)
        adjusted = holm_adjust(results.loc[mask, "one_sided_binomial_p"].tolist())
        results.loc[mask, "holm_adjusted_p"] = adjusted
    results["holm_positive"] = (
        results["holm_adjusted_p"].lt(0.05)
        & results["high_win_rate_excluding_ties"].gt(0.5)
    )
    return results


def pct(value: float) -> str:
    return "" if pd.isna(value) else f"{100 * value:.1f}%"


def write_summary(results: pd.DataFrame, path: Path) -> None:
    full = results[results["sample"].eq("all_pairs")].set_index("actor")
    filtered = results[results["sample"].eq("exclude_suspicion_or_disbelief")].set_index("actor")
    lines = [
        "# Sensitivity Analysis Excluding Suspicion or Disbelief",
        "",
        "A comparison is excluded when either returned actor reasoning trace was classified as "
        "expressing suspicion about the setup or explicit disbelief in its real-world causality. "
        "The outcome is the panel's high-side win rate after ties are excluded. Intervals are "
        "exact 95% familywise confidence intervals across the seven model estimates "
        "(Bonferroni-adjusted Clopper-Pearson intervals); significance tests are one-sided exact "
        "binomial tests with Holm correction across models.",
        "",
        "| Model | Pairs removed | Retained pairs | Resolved | Full win rate [FWER 95% CI] | After exclusion [FWER 95% CI] |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for actor in full.index:
        a = full.loc[actor]
        b = filtered.loc[actor]
        lines.append(
            f"| {a['actor_label']} | {int(b['pairs_excluded'])} | {int(b['pairs'])} | "
            f"{int(b['resolved_excluding_ties'])} | {pct(a['high_win_rate_excluding_ties'])} "
            f"[{pct(a['fwer95_ci_low'])}, {pct(a['fwer95_ci_high'])}] | "
            f"{pct(b['high_win_rate_excluding_ties'])} "
            f"[{pct(b['fwer95_ci_low'])}, {pct(b['fwer95_ci_high'])}] |"
        )

    removed = int(filtered["pairs_excluded"].sum())
    total_pairs = int(full["pairs"].sum())
    changes_pp = (
        100
        * (
            filtered["high_win_rate_excluding_ties"]
            - full["high_win_rate_excluding_ties"]
        ).abs()
    )
    qwen = filtered.loc["qwen3.5-9b-or"]
    qwen_full = full.loc["qwen3.5-9b-or"]
    lines.extend(
        [
            "",
            f"The filter removes {removed:,} of {total_pairs:,} comparisons. Across all seven "
            f"models, the filtered point estimate changes by at most {changes_pp.max():.1f} "
            "percentage points. The expanded Qwen3.5 estimate changes from "
            f"{pct(qwen_full['high_win_rate_excluding_ties'])} to "
            f"{pct(qwen['high_win_rate_excluding_ties'])}; its filter retains "
            f"{int(qwen['pairs']):,} of {int(qwen_full['pairs']):,} comparisons and leaves "
            f"{int(qwen['resolved_excluding_ties'])} resolved comparisons. No filtered model is "
            "significantly above chance under the familywise analysis.",
            "",
            "This is a sensitivity analysis, not a replacement causal estimand: suspicion and "
            "disbelief are post-treatment responses to the prompt, so conditioning on them can "
            "introduce selection bias. For the original six model runs, saved LLM labels exist "
            "only for traces selected by the documented lexical gate; gate-negative traces count "
            "as having no recorded suspicion or disbelief. The Qwen3.5 row incorporates the "
            "fixed 1,620-comparison follow-up and its preserved local stance labels, combined with "
            "the original 300 comparisons.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-outcomes", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--qwen-followup", type=Path, default=DEFAULT_QWEN_FOLLOWUP)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    pairs = pd.read_csv(args.pair_outcomes)
    labels = pd.DataFrame(read_jsonl(args.labels))
    qwen_followup = pd.read_csv(args.qwen_followup)
    results = analyze(pairs, labels, qwen_followup)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / f"{OUTPUT_STEM}.csv"
    md_path = args.output_dir / f"{OUTPUT_STEM}.md"
    results.to_csv(csv_path, index=False)
    write_summary(results, md_path)
    print(f"results: {csv_path}")
    print(f"summary: {md_path}")


if __name__ == "__main__":
    main()
