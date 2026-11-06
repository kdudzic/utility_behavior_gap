"""Week 8, plan item 2a: do the role prompts move the model along the effort direction?

Reads the projection files written by steer/project.py (re-encoded, unsteered essays; response-token-mean residual
projected onto unit vectors E, R_id, R_id_perp, rand0 at layers 4 to 20) and compares, per key and layer:
  - w7_role:      world_class vs skilled essays (the paper's role contrast, both untouched)
  - w6_ablation:  effort (max-effort prompt) vs neutral essays (the paper's exhortation contrast, both untouched)
Projection is reported as a fraction of the layer's residual RMS. Columns: mean per condition, difference, Cohen's d,
AUC (Mann-Whitney), and the ratio of the role shift to the exhortation shift.
Writes <out>/proj_role.csv, proj_exhortation.csv, proj_role_vs_effort.csv and prints them.
Run: .venv/bin/python -m steering_extension.local.week8_role --out outputs/steering/w8_analysis
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "outputs/steering/runs"
CONTRASTS = {"role": ("w7_role", "world_class", "skilled"), "exhortation": ("w6_ablation", "effort", "neutral")}


def load(run: str) -> pd.DataFrame:
    rows = [json.loads(l) for l in (RUNS / run / "projections.shard0.jsonl").open()]
    P = pd.DataFrame(rows).drop_duplicates(["output_id", "layer", "key"])
    P["p"] = P.proj_rmean / P.resid_rms_rmean
    return P


def contrast_table(P: pd.DataFrame, pos: str, neg: str, name: str) -> pd.DataFrame:
    rows = []
    for (k, l), g in P.groupby(["key", "layer"]):
        a, b = g[g.condition == pos].p, g[g.condition == neg].p
        if not len(a) or not len(b):
            continue
        d = (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2)
        auc = mannwhitneyu(a, b).statistic / (len(a) * len(b))
        rows.append({"contrast": name, "key": k, "layer": l, "n": f"{len(a)}/{len(b)}", "pos_mean": a.mean(), "neg_mean": b.mean(),
                     "diff": a.mean() - b.mean(), "cohen_d": d, "auc": auc})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/steering/w8_analysis")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    tables = {}
    for name, (run, pos, neg) in CONTRASTS.items():
        if (RUNS / run / "projections.shard0.jsonl").exists():
            tables[name] = contrast_table(load(run), pos, neg, name)
            tables[name].to_csv(args.out / f"proj_{name}.csv", index=False)
    pd.set_option("display.width", 220)
    for name, T in tables.items():
        print(f"== {name}: projection onto unit vectors, fraction of residual RMS (pos minus neg)")
        print(T.round(4).to_string(index=False))
    if {"role", "exhortation"} <= tables.keys():
        M = tables["role"].merge(tables["exhortation"], on=["key", "layer"], suffixes=("_role", "_exh"))
        M["role_over_exh"] = M.diff_role / M.diff_exh
        print("\n== shift along each direction: role (world-class minus skilled) vs exhortation (max-effort minus neutral)")
        print(M[["key", "layer", "diff_role", "cohen_d_role", "auc_role", "diff_exh", "cohen_d_exh", "auc_exh", "role_over_exh"]].round(4).to_string(index=False))
        M.to_csv(args.out / "proj_role_vs_effort.csv", index=False)


if __name__ == "__main__":
    main()
