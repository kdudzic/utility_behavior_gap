"""Paper text features on steering outputs, and the effort "signature match" proxy.

Features are computed with the paper's own `scalar_features` (analyze_final_text_features.py), so
they are the same quantities as the paper's Table 2 / feature appendix. The paper's reference signature
is taken from `data/processed/final_text_analysis_pair_deltas.csv.gz`: the per-pair deltas of the
paper's direct-exhortation contrast (`framed_user_strong_headroom`, direct_high minus direct_low) for
actor qwen3.5-9b-or, per task. Both sides are expressed as paired standardised effects
(mean delta / sd delta), and the signature match of a steering cell is the Pearson correlation across
features between the cell's standardised deltas (steered minus unsteered, same item and repeat) and the
paper's, plus the fraction of features with the same sign.

Usage:
  python -m steering_extension.local.text_features --run-dir <run>              # writes <run>/features.csv, <run>/signature.csv
  python -m steering_extension.local.text_features --paper-signature             # prints the reference per task
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from utility_behavior_gap.scripts.analyze_final_text_features import (  # noqa: E402
    load_textstat_module,
    load_vader_lexicon,
    load_zipf_frequency,
    scalar_features,
)

PAIR_DELTAS = ROOT / "data" / "processed" / "final_text_analysis_pair_deltas.csv.gz"
# the paper's standard generic set (analysis_specs/feature_definitions.yaml: generic_features.standard_set);
# `quantitative_detail` in the spec is numbers+percentages per 1k; the pair-delta file carries
# `numeric_specificity_per_1k` (numbers+percentages+currency), which is the closest stored column.
STANDARD = ["words", "paragraphs", "mattr_50", "rare_word_rate_per_1k", "numeric_specificity_per_1k", "textstat_flesch_kincaid_grade", "positive_words_per_1k", "negative_words_per_1k"]
EXTENDED = STANDARD + ["avg_sentence_words", "mean_word_length_chars", "semicolon_colon_per_1k", "dash_per_1k", "sentences", "unique_word_ratio"]
PAPER_ACTOR = "qwen3.5-9b-or"
PAPER_COMPARISON = "framed_user_strong_headroom"


def feature_fns():
    ts = load_textstat_module()
    pos, neg = load_vader_lexicon()
    zipf, note = load_zipf_frequency()
    if ts is None or not pos or zipf is None:
        print(f"warning: textstat={ts is not None} vader={bool(pos)} wordfreq={zipf is not None}; some features NaN", file=sys.stderr)
    return lambda text: scalar_features(text, textstat_module=ts, positive_words=pos, negative_words=neg, zipf_frequency_fn=zipf)


def paper_signature(tasks: list[str] | None = None, features: list[str] = EXTENDED) -> pd.DataFrame:
    """Rows: task x feature -> paper mean delta, sd, standardised effect d, n pairs."""
    df = pd.read_csv(PAIR_DELTAS, low_memory=False)
    q = df[(df.actor == PAPER_ACTOR) & (df.comparison == PAPER_COMPARISON)]
    if tasks:
        q = q[q.task.isin(tasks)]
    rows = []
    for task, g in q.groupby("task"):
        for f in features:
            col = f"delta_{f}"
            if col not in g:
                continue
            x = g[col].astype(float).dropna()
            sd = x.std(ddof=1)
            rows.append({"task": task, "feature": f, "paper_mean_delta": x.mean(), "paper_sd_delta": sd, "paper_d": x.mean() / sd if sd > 0 else math.nan, "paper_n": len(x)})
    return pd.DataFrame(rows)


def run_features(run_dir: Path) -> pd.DataFrame:
    fn = feature_fns()
    jobs = {j["pair_uid"]: j for j in (json.loads(l) for l in (run_dir / "generation_jobs.jsonl").open())}
    rows = []
    for l in (run_dir / "generations.jsonl").open():
        g = json.loads(l)
        if not g.get("output_text"):
            continue
        job = jobs[g["pair_uid"]]
        side = g["output_id"].rsplit("::", 1)[1]
        f = fn(g["output_text"])
        rows.append({"output_id": g["output_id"], "pair_uid": g["pair_uid"], "side": side, "condition": g["condition"], "cell": job.get("cell", job.get("comparison", "")), "task": job["task"], "item_index": job.get("item_index", ""), "repeat": job.get("repeat", ""), "finish_reason": g.get("finish_reason", ""), "alias_of": g.get("alias_of", ""), **f})
    return pd.DataFrame(rows)


def cell_deltas(feats: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Per cell x task: paired deltas side a minus side b (steered minus baseline), standardised."""
    a = feats[feats.side == "a"].set_index("pair_uid")
    b = feats[feats.side == "b"].set_index("pair_uid")
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    rows = []
    for (cell, task), idx in a.groupby(["cell", "task"]).groups.items():
        for f in features:
            d = (a.loc[idx, f].astype(float) - b.loc[idx, f].astype(float)).dropna()
            sd = d.std(ddof=1) if len(d) > 1 else math.nan
            rows.append({"cell": cell, "task": task, "feature": f, "mean_delta": d.mean(), "sd_delta": sd, "d": d.mean() / sd if sd and sd > 0 else math.nan, "n": len(d), "mean_a": a.loc[idx, f].astype(float).mean(), "mean_b": b.loc[idx, f].astype(float).mean()})
    return pd.DataFrame(rows)


def signature_match(deltas: pd.DataFrame, paper: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rows = []
    for (cell, task), g in deltas.groupby(["cell", "task"]):
        p = paper[paper.task == task].set_index("feature")
        g = g.set_index("feature")
        fs = [f for f in features if f in g.index and f in p.index and np.isfinite(g.loc[f, "d"]) and np.isfinite(p.loc[f, "paper_d"])]
        if len(fs) < 3:
            continue
        x = np.array([g.loc[f, "d"] for f in fs]); y = np.array([p.loc[f, "paper_d"] for f in fs])
        r = float(np.corrcoef(x, y)[0, 1]) if x.std() > 0 and y.std() > 0 else math.nan
        # cosine of standardised-effect vectors (scale-free, no centering) and sign agreement
        cos = float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y))) if np.linalg.norm(x) > 0 else math.nan
        sign = float(np.mean(np.sign(x) == np.sign(y)))
        words_d = float(g.loc["words", "d"]) if "words" in g.index else math.nan
        rows.append({"cell": cell, "task": task, "n_features": len(fs), "n_pairs": int(g["n"].max()), "signature_r": round(r, 3), "signature_cos": round(cos, 3), "sign_agreement": round(sign, 3), "words_d": round(words_d, 3), "paper_words_d": round(float(p.loc["words", "paper_d"]), 3) if "words" in p.index else math.nan})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path)
    ap.add_argument("--paper-signature", action="store_true")
    ap.add_argument("--feature-set", choices=["standard", "extended"], default="standard")
    args = ap.parse_args()
    features = STANDARD if args.feature_set == "standard" else EXTENDED
    paper = paper_signature(features=EXTENDED)
    if args.paper_signature:
        print(paper.pivot(index="feature", columns="task", values="paper_d").round(3).to_string())
        return
    feats = run_features(args.run_dir)
    feats.to_csv(args.run_dir / "features.csv", index=False)
    deltas = cell_deltas(feats, EXTENDED)
    deltas.to_csv(args.run_dir / "feature_deltas.csv", index=False)
    sig = signature_match(deltas, paper, features)
    sig.to_csv(args.run_dir / "signature.csv", index=False)
    print(sig.sort_values(["task", "signature_r"], ascending=[True, False]).to_string(index=False))


if __name__ == "__main__":
    main()
