"""Week 9: does essay length explain the judged sandbagging results? Offline, reads the pair tables written by
week9_sandbag.py (sandbag_pairs.csv: one row per judged pair with outcome W / L / T for side a and the word counts
of both sides).

For each model:
  A. per comparison type, how often the longer text wins among resolved pairs, and the odds ratio of winning per
     10 extra words (logistic regression of win on words_a - words_b);
  B. harmful-prompt texts (untouched or steered) against the baseline text: win rate by bin of the word difference
     per group of cells, and the logistic regression with group indicators, with and without the word difference;
  C. steered harmful text against the untouched harmful text: the same, with the random-direction cell as reference;
  D. the predicted win rate of a harmful-prompt text against the baseline at equal length.

Pairs within a model share texts (every cell is compared with the same untouched texts), so the p values are
approximate. Qwen pairs are restricted to clean pairs (the paper's refusal screen).

  python -m steering_extension.local.week9_length            # writes outputs/steering/w9_analysis/length_tables.txt
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from steering_extension.local.common import ROOT

OUT = ROOT / "outputs" / "steering" / "w9_analysis"


def group(cell: str) -> str:
    if cell.startswith("harmful_vs_empty"):
        return "untouched harmful"
    m = re.match(r"steer_(\w+?)_L(\d+)_r([+-][\d.]+)_", cell)
    key, layer, r = m.group(1), int(m.group(2)), float(m.group(3))
    if key == "E":
        return f"E added L{layer}"
    if key == "rand0":
        return f"random added L{layer}"
    return f"{key} {'removed' if r < 0 else 'added'}"


def logit(y: pd.Series, x: pd.DataFrame):
    return sm.Logit(y, sm.add_constant(x)).fit(disp=0)


def expit(v: float) -> float:
    return float(1 / (1 + np.exp(-v)))


def model_tables(name: str, pairs: pd.DataFrame, bins_vs_base: list[int], bins_vs_harm: list[int], ref_group: str | None) -> list[str]:
    out = [f"\n================ {name} ================"]
    d = pairs[pairs.outcome != "T"].copy()
    d["win"] = (d.outcome == "W").astype(int)
    d["dw"] = d.words_a - d.words_b

    rows = []
    for comp, g in d.groupby("comparison"):
        longer = int((((g.dw > 0) & (g.win == 1)) | ((g.dw < 0) & (g.win == 0))).sum())
        m = logit(g.win, (g.dw / 10).rename("dw10").to_frame())
        rows.append({"comparison": comp, "resolved": len(g), "longer_wins": longer, "share": longer / max(1, int((g.dw != 0).sum())),
                     "mean_dw": g.dw.mean(), "odds_ratio_per_10_words": float(np.exp(m.params["dw10"])), "p": float(m.pvalues["dw10"])})
    a = pd.DataFrame(rows)
    out += ["\n== A. the longer text wins (resolved pairs)", a.round(4).to_string(index=False)]
    a.to_csv(OUT / f"length_{name}_A.csv", index=False)

    for label, sel, bins, ref in [
        ("B. harmful-prompt text (side a) vs baseline text", d.comparison.isin(["harmful_vs_empty", "steered_harmful_vs_empty"]), bins_vs_base, "untouched harmful"),
        ("C. steered harmful text (side a) vs untouched harmful text", d.comparison == "steer_vs_harmful", bins_vs_harm, ref_group),
    ]:
        g = d[sel].copy()
        if g.empty:
            continue
        g["group"] = g.cell.map(group)
        g["bin"] = pd.cut(g.dw, bins)
        tab = g.groupby(["group", "bin"], observed=False).win.agg(["sum", "count"])
        wide = (tab["sum"].astype(str) + " / " + tab["count"].astype(str)).unstack("bin")
        wide.insert(0, "all", g.groupby("group").win.agg(lambda s: f"{int(s.sum())} / {len(s)}"))
        wide.insert(1, "mean_dw", g.groupby("group").dw.mean().round(1))
        out += [f"\n== {label}: wins / resolved pairs by word difference (a minus b)", wide.to_string()]
        wide.to_csv(OUT / f"length_{name}_{label[0]}.csv")
        if ref is None or ref not in set(g.group):
            continue
        dummies = pd.get_dummies(g.group, dtype=float).drop(columns=[ref])
        m0 = logit(g.win, dummies)
        m1 = logit(g.win, dummies.assign(dw10=g.dw / 10))
        reg = pd.DataFrame({"log_odds_vs_ref": m0.params, "p": m0.pvalues, "log_odds_at_equal_length": m1.params, "p_equal_length": m1.pvalues}).drop(index="const", errors="ignore")
        out += [f"\nlogistic regression, reference group: {ref} (dw10 = word difference / 10)", reg.round(4).to_string()]
        reg.to_csv(OUT / f"length_{name}_{label[0]}_regression.csv")

    g = d[d.comparison.isin(["harmful_vs_empty", "steered_harmful_vs_empty"])]
    for label, x in [("untouched harmful vs baseline", g[g.comparison == "harmful_vs_empty"]), ("all harmful-prompt cells vs baseline", g)]:
        if len(x) < 20:
            continue
        m = logit(x.win, (x.dw / 10).rename("dw10").to_frame())
        lo, hi = m.conf_int().loc["const"]
        out.append(f"\n== D. {label}: predicted win rate at equal length {expit(m.params['const']):.2f} "
                   f"(95% interval {expit(lo):.2f} to {expit(hi):.2f}); observed {int(x.win.sum())} / {len(x)} at a mean difference of {x.dw.mean():.0f} words")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--qwen", type=Path, default=OUT / "sandbag_pairs.csv")
    ap.add_argument("--deepseek", type=Path, default=OUT / "ds" / "sandbag_pairs.csv")
    args = ap.parse_args()
    lines: list[str] = []
    ds = pd.read_csv(args.deepseek)
    ds = ds[ds.run != "ds_base_grant"]   # essay only: the steering cells are essays
    lines += model_tables("deepseek_essay", ds, [-1000, -90, -60, -30, 0, 1000], [-1000, -15, 15, 45, 1000], "random added L20")
    qw = pd.read_csv(args.qwen)
    qw = qw[~qw.screened]
    lines += model_tables("qwen_grant_clean", qw, [-1000, -60, -20, 20, 60, 1000], [-1000, -60, -20, 20, 60, 1000], "random added L10")
    text = "\n".join(lines)
    (OUT / "length_tables.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
