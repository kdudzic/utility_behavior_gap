"""Week 8, note items 4 and 5: coherence of effort vs random steering, and win rate vs coherence.

Reads the judged essay runs (pair_table from analyze_dose) and writes to <out>/:
  A. coherence_grid.csv          week-7 grid (layers 6,10,14,20 x r -0.1,+0.05,+0.1): unsteered, random (two directions
                                 pooled), effort; coherence mean, share >= 80, delta vs unsteered, W/L. Plus ablation rows.
     coherence_grid.png          one panel per layer, coherence vs dose, effort / random / unsteered.
  B. cells_winrate_coherence.csv every essay cell with >= 10 resolved pairs: win rate, steered-side coherence, delta.
     winrate_vs_coherence.png    scatter, cells coloured by type, Spearman per type.
     pairs_coherence_bins.csv    pair level: win rate by bin of (coherence a - coherence b), per type;
                                 share of resolved pairs where the higher-coherence text won; logistic slope per 10 points.
Run: .venv/bin/python -m steering_extension.local.week8_coherence --out outputs/steering/w8_analysis
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from steering_extension.local.analyze_dose import pair_table  # noqa: E402

RUNS = ROOT / "outputs/steering/runs"
# essay runs with the week-6 vector (v4, response mean) or random directions, plus ablation cells
ESSAY_RUNS = ["w6_sweep", "w7_random", "w6_ablation_local", "w7_necessity", "w6_ablation", "w7_role", "w6_multilayer", "w6_positions", "w6_readouts"]
GRID_LAYERS = [6, 10, 14, 20]
GRID_R = [-0.1, 0.05, 0.1]
COL = {"effort": "#2a78d6", "random": "#eb6834", "ablation": "#1baf7a", "random ablation": "#eda100", "null": "#777777", "other": "#bbbbbb"}


def cell_type(cell: str) -> str:
    if cell in ("steer_baseline", "world_class_vs_skilled", "effort_vs_neutral"):
        return "null"
    if cell.startswith("ablate_rand"):
        return "random ablation"
    if cell.startswith("ablate_E"):
        return "ablation"
    if cell.startswith("steer_rand"):
        return "random"
    if re.match(r"^steer_E_L\d+_r[+-]\d+\.\d+_response$", cell):
        return "effort"
    return "other"  # readouts, multi-layer, prompt/all position modes, role-prompt cells


def load_all() -> pd.DataFrame:
    frames = []
    for run in ESSAY_RUNS:
        rd = RUNS / run
        if not (rd / "judge_votes.jsonl").exists():
            continue
        P = pair_table(rd)
        P["run"] = run
        P["type"] = [cell_type(c) for c in P.cell]
        frames.append(P)
    P = pd.concat(frames, ignore_index=True)
    P["coh_d"] = P.coh_a - P.coh_b
    return P


def cell_stats(g: pd.DataFrame) -> dict:
    w, l = int((g.outcome == "W").sum()), int((g.outcome == "L").sum())
    return {"pairs": len(g), "W": w, "L": l, "win_rate": w / (w + l) if w + l else np.nan,
            "coh_a": g.coh_a.mean(), "coh_pass80_a": (g.coh_a >= 80).mean(), "coh_b": g.coh_b.mean(), "coh_d": g.coh_d.mean(),
            "words_a": g.words_a.mean(), "words_b": g.words_b.mean()}


def part_a(P: pd.DataFrame, out: Path) -> None:
    rows = []
    for layer in GRID_LAYERS:
        for r in GRID_R:
            e = P[(P.type == "effort") & (P.layer0 == layer) & np.isclose(P.r, r)]
            rn = P[(P.type == "random") & (P.layer0 == layer) & np.isclose(P.r, r)]
            for label, g in (("effort", e), ("random", rn)):
                if not len(g):
                    continue
                s = cell_stats(g)
                rows.append({"layer": layer, "r": r, "steered with": label, "runs": "+".join(sorted(g.run.unique())), **s,
                             "delta_coh": s["coh_a"] - s["coh_b"]})
    # ablation rows (cells named explicitly; coherence of the ablated side vs its opponent)
    for cell in ["ablate_E_L8+10+12+14+16_effort_vs_effort", "ablate_E_L8+10+12+14+16_effort_vs_neutral", "ablate_rand0_L8+10+12+14+16_effort_vs_neutral",
                 "ablate_E_effort_vs_effort", "ablate_rand0_effort_vs_effort"]:
        g = P[P.cell == cell]
        if len(g):
            s = cell_stats(g)
            rows.append({"layer": cell.split("_L")[1].split("_")[0] if "_L" in cell else "all 32", "r": "ablate", "steered with": cell, "runs": "+".join(sorted(g.run.unique())), **s, "delta_coh": s["coh_a"] - s["coh_b"]})
    A = pd.DataFrame(rows)
    A.to_csv(out / "coherence_grid.csv", index=False)
    print("== A. coherence by layer x dose: effort vs random (delta = steered minus its unsteered opponent)")
    print(A[["layer", "r", "steered with", "pairs", "W", "L", "win_rate", "coh_a", "coh_pass80_a", "coh_b", "delta_coh", "words_a", "words_b"]].round(2).to_string(index=False))
    # pooled over the grid
    for t in ("effort", "random"):
        g = P[(P.type == t) & P.layer0.isin(GRID_LAYERS) & P.r.apply(lambda x: any(np.isclose(x, rr) for rr in GRID_R))]
        print(f"pooled {t}: n={len(g)} coh_a={g.coh_a.mean():.1f} coh_b={g.coh_b.mean():.1f} delta={g.coh_d.mean():.1f} (SE {g.coh_d.std() / np.sqrt(len(g)):.1f}) pass80 a={(g.coh_a >= 80).mean():.2f} b={(g.coh_b >= 80).mean():.2f}")
    # figure: full dose curves for effort (week-6 sweep, all doses) and random where present, one panel per grid layer
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.4), sharey=True)
    for ax, layer in zip(axes, GRID_LAYERS):
        for t in ("effort", "random"):
            g = P[(P.type == t) & (P.layer0 == layer)]
            if not len(g):
                continue
            s = g.groupby("r").agg(m=("coh_a", "mean"), se=("coh_a", lambda x: x.std() / np.sqrt(len(x)))).reset_index()
            ax.errorbar(s.r, s.m, yerr=s.se, color=COL[t], lw=2, marker="o", ms=6, capsize=2, label=t)
        b = P[(P.type == "effort") & (P.layer0 == layer)].coh_b.mean()
        ax.axhline(b, color=COL["null"], lw=1.5, ls="--", label="unsteered")
        ax.set_title(f"layer {layer}", fontsize=11)
        ax.set_xlabel("dose r")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e5e5", lw=0.8)
    axes[0].set_ylabel("coherence (mean, SE)")
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Coherence of the steered essay: effort direction vs random direction (essay, neutral prompt)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "coherence_grid.png", dpi=160)
    plt.close(fig)


def part_b(P: pd.DataFrame, out: Path) -> None:
    rows = []
    for (run, cell), g in P.groupby(["run", "cell"]):
        s = cell_stats(g)
        if s["W"] + s["L"] < 10:
            continue
        rows.append({"run": run, "cell": cell, "type": g.type.iloc[0], "layer0": g.layer0.iloc[0], "r": g.r.iloc[0], **s})
    cells = pd.DataFrame(rows).dropna(subset=["coh_a", "win_rate"])
    cells.to_csv(out / "cells_winrate_coherence.csv", index=False)
    print("\n== B1. cell level: win rate vs steered-side coherence (Spearman)")
    for t, g in cells.groupby("type"):
        if len(g) >= 5:
            rho, p = spearmanr(g.win_rate, g.coh_a)
            rho2, p2 = spearmanr(g.win_rate, g.coh_d)
            print(f"  {t:16s} cells={len(g):3d} rho(win, coh_a)={rho:+.2f} p={p:.2g} | rho(win, coh_a-coh_b)={rho2:+.2f} p={p2:.2g}")
    main_types = ["effort", "random", "ablation", "random ablation", "null"]
    main = cells[cells.type.isin(main_types)]
    rho, p = spearmanr(main.win_rate, main.coh_a)
    print(f"  all main types     cells={len(main)} rho={rho:+.2f} p={p:.2g}")
    for label, e in (("effort |r|<=0.1", cells[(cells.type == "effort") & (cells.r.abs() <= 0.1)]), ("effort r<0", cells[(cells.type == "effort") & (cells.r < 0)]), ("effort r>0", cells[(cells.type == "effort") & (cells.r > 0)])):
        rho, p = spearmanr(e.win_rate, e.coh_a)
        print(f"  {label:18s} cells={len(e)} rho={rho:+.2f} p={p:.2g}")
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for t in main_types:
        g = cells[cells.type == t]
        if len(g):
            ax.scatter(g.coh_a, g.win_rate, s=36, color=COL[t], label=f"{t} ({len(g)})", alpha=0.85, edgecolor="white", lw=0.8)
    ax.axhline(0.5, color="#999", lw=1, ls=":")
    ax.set_xlabel("coherence of the intervened essay (cell mean)")
    ax.set_ylabel("win rate vs unsteered opponent")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(color="#e5e5e5", lw=0.8)
    ax.legend(frameon=False, fontsize=9)
    ax.set_title("Win rate against coherence, one point per cell (essay)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "winrate_vs_coherence.png", dpi=160)
    plt.close(fig)
    # B2 pair level
    print("\n== B2. pair level: does the higher-coherence essay win? (resolved pairs, coherence on both sides)")
    R = P[(P.outcome != "T") & P.coh_a.notna() & P.coh_b.notna()].copy()
    R["win"] = (R.outcome == "W").astype(int)
    bins = [-100, -10, -3, 3, 10, 100]
    labels = ["< -10", "-10 to -3", "-3 to 3", "3 to 10", "> 10"]
    R["bin"] = pd.cut(R.coh_d, bins=bins, labels=labels)
    # split the steering types by sign of the dose: removal (r < 0) and addition (r > 0), |r| <= 0.1 only
    R["group"] = R.type
    for t in ("effort", "random"):
        R.loc[(R.type == t) & (R.r < 0) & (R.r >= -0.1), "group"] = f"{t} remove (-0.1,-0.05)"
        R.loc[(R.type == t) & (R.r > 0) & (R.r <= 0.1), "group"] = f"{t} add (+0.025..+0.1)"
        R.loc[(R.type == t) & (R.r.abs() > 0.1), "group"] = f"{t} |r|>0.1"
    rows = []
    for t in ["effort remove (-0.1,-0.05)", "effort add (+0.025..+0.1)", "effort |r|>0.1", "random remove (-0.1,-0.05)", "random add (+0.025..+0.1)", "random |r|>0.1", "ablation", "random ablation", "null", "other"]:
        g = R[R.group == t]
        if len(g) < 20:
            continue
        ne = g[g.coh_d != 0]
        agree = ((ne.coh_d > 0) == (ne.win == 1)).mean()
        line = {"type": t, "pairs": len(g), "share higher-coherence wins": round(agree, 3), "n unequal": len(ne)}
        for b in labels:
            gb = g[g.bin == b]
            line[f"win {b}"] = f"{gb.win.mean():.2f} (n={len(gb)})" if len(gb) else ""
        try:
            import statsmodels.api as sm
            import statsmodels.formula.api as smf
            fit = smf.glm("win ~ coh_d", data=g, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": g["item"].astype(str)})
            line["logit slope per 10 pts"] = f"{10 * fit.params['coh_d']:+.2f} (p={fit.pvalues['coh_d']:.2g})"
            if g.cell.nunique() > 1:
                fit2 = smf.glm("win ~ coh_d + C(cell)", data=g, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": g["item"].astype(str)})
                line["slope within cell"] = f"{10 * fit2.params['coh_d']:+.2f} (p={fit2.pvalues['coh_d']:.2g})"
        except Exception as ex:  # noqa: BLE001
            line["logit slope per 10 pts"] = f"fit failed: {ex}"
        rows.append(line)
    B = pd.DataFrame(rows)
    B.to_csv(out / "pairs_coherence_bins.csv", index=False)
    pd.set_option("display.width", 250)
    print(B.to_string(index=False))
    # figure: win rate by coherence-difference bin, one line per group
    fig, ax = plt.subplots(figsize=(7, 4.4))
    styles = {"effort remove (-0.1,-0.05)": (COL["effort"], "-"), "effort add (+0.025..+0.1)": (COL["effort"], "--"), "random remove (-0.1,-0.05)": (COL["random"], "-"), "random add (+0.025..+0.1)": (COL["random"], "--"), "ablation": (COL["ablation"], "-"), "null": (COL["null"], "-")}
    for t, (c, ls) in styles.items():
        g = R[R.group == t]
        if len(g) < 20:
            continue
        s = g.groupby("bin", observed=True).win.agg(["mean", "size"]).reindex(labels)
        ax.plot(range(len(labels)), s["mean"], color=c, ls=ls, lw=2, marker="o", ms=6, label=f"{t} (n={len(g)})")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlabel("coherence of intervened essay minus coherence of its opponent")
    ax.set_ylabel("share of resolved pairs the intervened essay won")
    ax.axhline(0.5, color="#999", lw=1, ls=":")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", lw=0.8)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Panel decision against the within-pair coherence gap", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "pairs_winrate_by_coherence_gap.png", dpi=160)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/steering/w8_analysis")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    P = load_all()
    print(f"pairs loaded: {len(P)}; by type: {P.type.value_counts().to_dict()}")
    part_a(P, args.out)
    part_b(P, args.out)


if __name__ == "__main__":
    main()
