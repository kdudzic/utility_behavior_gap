"""Week 9, plan item 1: coherence vs score, closer (offline, no API calls).

Reads the judged essay runs through week8_coherence.load_all() and writes to <out>/:
  1a. 1a_coherence_distribution.csv  distribution of the steered essay's coherence per layer x dose (layers 6, 10, 14, 20),
                                     effort vs random vs unsteered; share below 80 and below 70.
      1a_coherence_distribution.png, 1a_share_below_80.png
  1b. 1b_mixture_cells.csv           every effort-addition cell split into damaged / as coherent / more coherent pairs
                                     (coherence gap = steered minus unsteered partner, threshold 3), W / L / T inside each part.
      1b_mixture_pooled.csv          the same pooled (by dose, by layer band), for random addition and for the null cells,
                                     and restricted to pairs whose unsteered partner scored 92 or more.
      1b_mixture.png
  1c. 1c_topics.csv                  per topic: how often the essay scores below 80 when effort is added, when a random
                                     direction is added, and unsteered.
      1c_concentration.csv           top-5 share, the share expected by chance, rank correlations between conditions.
      1c_topics.png
  1d. 1d_dose_curve.csv              per layer x dose: share damaged, share won at equal-or-better coherence.
      1d_dose_curve.png
  1e. 1e_mixture_cells.csv, 1e_mixture_pooled.csv, 1e_mixture.png   the 1b tables for removal (r < 0).
Run: .venv/bin/python -m steering_extension.local.week9_coherence
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import binomtest, spearmanr

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from steering_extension.local import week8_coherence as w8  # noqa: E402

BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#777777"
GAP = 3  # points; a pair is "damaged" if steered minus unsteered < -GAP, "more coherent" if > +GAP
GRID_LAYERS = [6, 10, 14, 20]
PARTS = ["damaged", "as coherent", "more coherent"]
NULL_CELL = "steer_baseline"  # unsteered vs unsteered, neutral prompt on both sides
BINS = [("below 70", -1, 70), ("70 to 79", 70, 80), ("80 to 87", 80, 88), ("88 to 91", 88, 92), ("92 or more", 92, 101)]


def ci(k: int, n: int) -> tuple[float, float]:
    """Exact (Clopper-Pearson) 95% interval for k of n."""
    if n == 0:
        return (np.nan, np.nan)
    c = binomtest(int(k), int(n)).proportion_ci(method="exact")
    return (c.low, c.high)


def add_part(P: pd.DataFrame) -> pd.DataFrame:
    P = P.copy()
    P["part"] = np.where(P.coh_d < -GAP, "damaged", np.where(P.coh_d > GAP, "more coherent", "as coherent"))
    return P


def style(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", lw=0.8)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------- data sets

def split(P: pd.DataFrame) -> dict:
    E = P[(P.run == "w6_sweep") & (P.type == "effort")]
    R = P[(P.run == "w7_random") & (P.type == "random")]
    N = P[P.cell == NULL_CELL]
    # every unsteered essay we have a score for: side a of the null cells, and the partner (side b) of each run,
    # one row per distinct essay (the same partner essay serves every cell of a run)
    a = N[["run", "item", "repeat", "coh_a", "words_a"]].rename(columns={"coh_a": "coh", "words_a": "words"}).assign(side="null side a")
    b = P[P.run.isin(N.run.unique()) & (P.type != "ablation") & (P.type != "random ablation")]
    b = b[["run", "item", "repeat", "coh_b", "words_b"]].rename(columns={"coh_b": "coh", "words_b": "words"}).assign(side="partner")
    # the runs do not share essays (word counts differ between runs), so one row per run, side, topic and repeat
    U = pd.concat([a, b], ignore_index=True).drop_duplicates(["run", "side", "item", "repeat"])
    return {"E": E, "R": R, "N": N, "U": U}


# ---------------------------------------------------------------- 1a

def dist_row(x: pd.Series) -> dict:
    x = x.dropna()
    n = len(x)
    row = {"essays": n, "mean": x.mean(), "median": x.median()}
    for name, lo, hi in BINS:
        row[f"share {name}"] = ((x >= lo) & (x < hi)).mean()
    for thr in (80, 70):
        k = int((x < thr).sum())
        lo_, hi_ = ci(k, n)
        row[f"n below {thr}"] = k
        row[f"share below {thr}"] = k / n
        row[f"below {thr} ci lo"], row[f"below {thr} ci hi"] = lo_, hi_
    return row


def part_1a(D: dict, out: Path) -> pd.DataFrame:
    E, R, N, U = D["E"], D["R"], D["N"], D["U"]
    rows = []
    rows.append({"layer": "", "r": 0.0, "essays from": "unsteered, all distinct essays", **dist_row(U.coh)})
    rows.append({"layer": "", "r": 0.0, "essays from": "unsteered, partners of the effort sweep", **dist_row(E.drop_duplicates(["item", "repeat"]).coh_b)})
    rows.append({"layer": "", "r": 0.0, "essays from": "unsteered, partners of the random run", **dist_row(R.drop_duplicates(["item", "repeat"]).coh_b)})
    rows.append({"layer": "", "r": 0.0, "essays from": "unsteered, side a of the null cells", **dist_row(N.coh_a)})
    for layer in GRID_LAYERS:
        for r in sorted(E.r.unique()):
            rows.append({"layer": layer, "r": r, "essays from": "effort", **dist_row(E[(E.layer0 == layer) & np.isclose(E.r, r)].coh_a)})
            g = R[(R.layer0 == layer) & np.isclose(R.r, r)]
            if len(g):
                rows.append({"layer": layer, "r": r, "essays from": "random", **dist_row(g.coh_a)})
    # pooled over the four layers, per dose
    for r in sorted(E.r.unique()):
        rows.append({"layer": "6+10+14+20", "r": r, "essays from": "effort", **dist_row(E[E.layer0.isin(GRID_LAYERS) & np.isclose(E.r, r)].coh_a)})
        g = R[np.isclose(R.r, r)]
        if len(g):
            rows.append({"layer": "6+10+14+20", "r": r, "essays from": "random", **dist_row(g.coh_a)})
    A = pd.DataFrame(rows)
    A.to_csv(out / "1a_coherence_distribution.csv", index=False)

    # figure 1: distributions, rows = layers, columns = doses
    doses = sorted(E.r.unique())
    names = [b[0] for b in BINS]
    u = A.iloc[0]
    fig, axes = plt.subplots(len(GRID_LAYERS), len(doses), figsize=(2.3 * len(doses), 2.0 * len(GRID_LAYERS)), sharex=True, sharey=True)
    xs = np.arange(len(names))
    for i, layer in enumerate(GRID_LAYERS):
        for j, r in enumerate(doses):
            ax = axes[i, j]
            sel = A[(A.layer == layer) & np.isclose(A.r.astype(float), r)]
            e = sel[sel["essays from"] == "effort"].iloc[0]
            rn = sel[sel["essays from"] == "random"]
            wid = 0.4 if len(rn) else 0.8
            ax.bar(xs - (0.2 if len(rn) else 0), [e[f"share {n}"] for n in names], width=wid, color=BLUE, label="effort")
            if len(rn):
                ax.bar(xs + 0.2, [rn.iloc[0][f"share {n}"] for n in names], width=0.4, color=ORANGE, label="random")
            ax.step(np.r_[xs - 0.5, xs[-1] + 0.5], np.r_[[u[f"share {n}"] for n in names], u[f"share {names[-1]}"]], where="post", color=GREY, lw=1.5, label="unsteered")
            style(ax)
            if i == 0:
                ax.set_title(f"dose {r:+g}", fontsize=10)
            if j == 0:
                ax.set_ylabel(f"layer {layer}\nshare of essays", fontsize=9)
            if i == len(GRID_LAYERS) - 1:
                ax.set_xticks(xs, ["<70", "70-79", "80-87", "88-91", "92+"], fontsize=7, rotation=45)
    h, l = axes[0, doses.index(0.1)].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=10)
    fig.suptitle("Coherence score of the steered essay, by layer and dose (essay task; 60 essays per effort cell, 120 per random cell)", fontsize=11)
    fig.supxlabel("coherence score (0 to 100)", fontsize=10, y=0.045)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(out / "1a_coherence_distribution.png", dpi=150)
    plt.close(fig)

    # figure 2: share below 80 by dose
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6), sharey=True)
    for ax, layer in zip(axes, GRID_LAYERS):
        for t, c in (("effort", BLUE), ("random", ORANGE)):
            s = A[(A.layer == layer) & (A["essays from"] == t)].sort_values("r")
            y = s["share below 80"].to_numpy()
            ax.errorbar(s.r.astype(float), y, yerr=[y - s["below 80 ci lo"], s["below 80 ci hi"] - y], color=c, lw=2, marker="o", ms=5, capsize=2, label=t)
        ax.axhline(u["share below 80"], color=GREY, lw=1.5, ls="--", label="unsteered")
        ax.set_title(f"layer {layer}", fontsize=11)
        ax.set_xlabel("dose r (below 0 removes, above 0 adds)")
        style(ax)
    axes[0].set_ylabel("share of essays with coherence below 80")
    axes[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Share of low-coherence essays by dose: effort direction, random direction, unsteered (bars: exact 95% interval)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "1a_share_below_80.png", dpi=150)
    plt.close(fig)
    return A


# ---------------------------------------------------------------- 1b / 1e

def mixture(g: pd.DataFrame, **label) -> list[dict]:
    """One row per part (and one 'all' row) for a set of pairs."""
    rows = []
    n = len(g)
    W_all, L_all = int((g.outcome == "W").sum()), int((g.outcome == "L").sum())
    for part in PARTS + ["all"]:
        s = g if part == "all" else g[g.part == part]
        w, l, t = int((s.outcome == "W").sum()), int((s.outcome == "L").sum()), int((s.outcome == "T").sum())
        lo, hi = ci(w, w + l)
        rows.append({**label, "part": part, "pairs": len(s), "share of pairs": len(s) / n if n else np.nan,
                     "W": w, "L": l, "T": t, "win rate": w / (w + l) if w + l else np.nan, "win ci lo": lo, "win ci hi": hi,
                     "share of all W": w / W_all if W_all else np.nan, "share of all L": l / L_all if L_all else np.nan,
                     "coh steered": s.coh_a.mean(), "coh unsteered": s.coh_b.mean(), "mean gap": s.coh_d.mean(),
                     # part of the cell's mean coherence gap carried by this part (sums to the 'all' row's mean gap)
                     "gap contribution": s.coh_d.sum() / n if n else np.nan})
    return rows


def band(layer: int) -> str:
    return "6 to 14" if layer <= 14 else "16 to 28"


def mixture_tables(E: pd.DataFrame, R: pd.DataFrame, N: pd.DataFrame, sign: int, out: Path, tag: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    word = "added" if sign > 0 else "removed"
    e = E[(np.sign(E.r) == sign)]
    rn = R[(np.sign(R.r) == sign)]
    cells = []
    for (layer, r), g in e.groupby(["layer0", "r"]):
        cells += mixture(g, layer=layer, r=r)
    C = pd.DataFrame(cells)
    C.to_csv(out / f"{tag}_mixture_cells.csv", index=False)

    pooled = []
    main = e[e.r.abs() <= 0.1]  # the -0.2 cells are reported on their own rows
    pooled += mixture(main, group=f"effort {word}, all layers, abs(r) <= 0.1", layers="6 to 28", r="all", partner="any")
    for r, g in e.groupby("r"):
        pooled += mixture(g, group=f"effort {word}, r {r:+g}", layers="6 to 28", r=r, partner="any")
    for b in ("6 to 14", "16 to 28"):
        gb = main[main.layer0.map(band) == b]
        pooled += mixture(gb, group=f"effort {word}, layers {b}", layers=b, r="all", partner="any")
        for r, g in e[e.layer0.map(band) == b].groupby("r"):
            pooled += mixture(g, group=f"effort {word}, layers {b}, r {r:+g}", layers=b, r=r, partner="any")
    # effort on the random run's grid, for a like-for-like comparison with random
    for r, g in rn.groupby("r"):
        ge = e[e.layer0.isin(GRID_LAYERS) & np.isclose(e.r, r)]
        pooled += mixture(ge, group=f"effort {word}, layers 6+10+14+20, r {r:+g}", layers="6+10+14+20", r=r, partner="any")
        pooled += mixture(g, group=f"random {word}, layers 6+10+14+20, r {r:+g}", layers="6+10+14+20", r=r, partner="any")
    pooled += mixture(e[e.layer0.isin(GRID_LAYERS) & e.r.isin(rn.r.unique())], group=f"effort {word}, random run's grid", layers="6+10+14+20", r="grid", partner="any")
    pooled += mixture(rn, group=f"random {word}, all", layers="6+10+14+20", r="grid", partner="any")
    pooled += mixture(N, group="null (unsteered vs unsteered), 5 runs", layers="", r=0, partner="any")
    # partner fixed at the top score: a steered essay cannot be "more coherent" here, so this isolates damage from
    # the effect of a weak unsteered partner
    for label, g in ((f"effort {word}, all layers, abs(r) <= 0.1", main), (f"random {word}, all", rn), ("null (unsteered vs unsteered), 5 runs", N)):
        pooled += mixture(g[g.coh_b >= 92], group=label, layers="", r="all", partner="scored 92 or more")
        pooled += mixture(g[g.coh_b < 92], group=label, layers="", r="all", partner="scored below 92")
    for b in ("6 to 14", "16 to 28"):
        gb = main[(main.layer0.map(band) == b)]
        pooled += mixture(gb[gb.coh_b >= 92], group=f"effort {word}, layers {b}", layers=b, r="all", partner="scored 92 or more")
    Pd = pd.DataFrame(pooled)
    Pd.to_csv(out / f"{tag}_mixture_pooled.csv", index=False)

    # figure: share of pairs per part, and win rate inside each part
    groups = [("null (unsteered vs unsteered), 5 runs", "unsteered vs unsteered", GREY), (f"random {word}, all", f"random direction {word}", ORANGE),
              (f"effort {word}, all layers, abs(r) <= 0.1", f"effort direction {word}", BLUE)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    xs = np.arange(len(PARTS))
    for k, (gname, lab, c) in enumerate(groups):
        s = Pd[(Pd.group == gname) & (Pd.partner == "any")].set_index("part").loc[PARTS]
        off = (k - 1) * 0.27
        axes[0].bar(xs + off, s["share of pairs"], width=0.25, color=c, label=f"{lab} ({int(s.pairs.sum())} pairs)")
        y = s["win rate"].to_numpy()
        axes[1].bar(xs + off, y, width=0.25, color=c)
        axes[1].errorbar(xs + off, y, yerr=[y - s["win ci lo"], s["win ci hi"] - y], fmt="none", ecolor="#333333", capsize=2, lw=1)
        for x, (w, l) in zip(xs + off, zip(s.W, s.L)):
            axes[1].text(x, 1.02, f"{w}/{l}", ha="center", va="bottom", fontsize=7, color="#333333")
    ticklabels = [f"damaged\n(steered more than {GAP} below)", f"as coherent\n(within {GAP})", f"more coherent\n(steered more than {GAP} above)"]
    for ax in axes:
        ax.set_xticks(xs, ticklabels, fontsize=9)
        style(ax)
    axes[0].set_ylabel("share of pairs")
    axes[0].set_title("How the pairs split by coherence gap", fontsize=11)
    axes[0].set_ylim(0, 0.85)
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")
    axes[1].set_ylabel("win rate of the steered essay, W / (W + L)")
    axes[1].set_ylim(0, 1.12)
    axes[1].axhline(0.5, color="#999999", lw=1, ls=":")
    axes[1].set_title("Win rate inside each part (W/L above the bar, exact 95% interval)", fontsize=11)
    dose_txt = "r +0.025 to +0.1" if sign > 0 else "r -0.1 and -0.05"
    fig.suptitle(f"Effort {word} ({dose_txt}, layers 6 to 28) against random and null: mixture by coherence gap", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / f"{tag}_mixture.png", dpi=150)
    plt.close(fig)
    return C, Pd


# ---------------------------------------------------------------- 1c

def top_share(counts: np.ndarray, k: int = 5) -> float:
    return np.sort(counts)[::-1][:k].sum() / counts.sum() if counts.sum() else np.nan


def chance_top_share(n_per_topic: np.ndarray, rate: float, k: int = 5, sims: int = 20000, seed: int = 0) -> tuple[float, float]:
    """Top-k share expected if every topic had the same below-80 rate (mean and 97.5th percentile)."""
    rng = np.random.default_rng(seed)
    draws = rng.binomial(n_per_topic, rate, size=(sims, len(n_per_topic)))
    tot = draws.sum(axis=1)
    top = np.sort(draws, axis=1)[:, ::-1][:, :k].sum(axis=1)
    sh = top[tot > 0] / tot[tot > 0]
    return float(sh.mean()), float(np.quantile(sh, 0.975))


def part_1c(D: dict, out: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    E, R, U = D["E"], D["R"], D["U"]
    ea = E[E.r > 0]
    ea_grid = ea[ea.layer0.isin(GRID_LAYERS) & ea.r.isin([0.05, 0.1])]
    ra = R[R.r > 0]
    er = E[(E.r < 0) & (E.r >= -0.1)]
    items = sorted(E.item.unique(), key=int)

    def rate(g, col):
        return g.groupby("item")[col].agg(n="size", low=lambda x: int((x < 80).sum()))

    T = pd.DataFrame(index=items)
    for name, g, col in (("effort added", ea, "coh_a"), ("effort added, random run's grid", ea_grid, "coh_a"), ("random added", ra, "coh_a"),
                         ("effort removed", er, "coh_a"), ("unsteered", U, "coh")):
        s = rate(g, col).reindex(items).fillna(0).astype(int)
        T[f"{name}: essays"] = s.n
        T[f"{name}: below 80"] = s.low
        T[f"{name}: share below 80"] = s.low / s.n
    T["effort added: below 70"] = ea.groupby("item").coh_a.apply(lambda x: int((x < 70).sum())).reindex(items)
    T["effort added: share damaged (gap below -3)"] = ea.groupby("item").part.apply(lambda x: (x == "damaged").mean()).reindex(items)
    T["unsteered: mean coherence"] = U.groupby("item").coh.mean().reindex(items)
    pc = E.drop_duplicates(["item", "repeat"]).pivot(index="item", columns="repeat", values="coh_b").reindex(items)
    T["sweep partner coherence, repeat 0"], T["sweep partner coherence, repeat 1"] = pc["0"], pc["1"]
    T["effort minus unsteered, share below 80"] = T["effort added: share below 80"] - T["unsteered: share below 80"]
    # split halves of the effort-addition cells, to see whether the same topics are low in independent essays
    for name, g in (("layers 6 to 16", ea[ea.layer0 <= 16]), ("layers 18 to 28", ea[ea.layer0 >= 18]), ("repeat 0", ea[ea.repeat == "0"]), ("repeat 1", ea[ea.repeat == "1"])):
        T[f"effort added, {name}: share below 80"] = g.groupby("item").coh_a.apply(lambda x: (x < 80).mean()).reindex(items)
    T.index.name = "topic"
    T = T.reset_index()
    T.to_csv(out / "1c_topics.csv", index=False)

    rows = []
    for name in ("effort added", "effort added, random run's grid", "random added", "effort removed", "unsteered"):
        cnt, n = T[f"{name}: below 80"].to_numpy(), T[f"{name}: essays"].to_numpy()
        exp, hi = chance_top_share(n, cnt.sum() / n.sum())
        rows.append({"measure": "top 5 of 30 topics, share of all below-80 essays", "condition": name, "essays": int(n.sum()), "below 80": int(cnt.sum()),
                     "value": top_share(cnt), "expected if all topics equal": exp, "97.5th pct if all topics equal": hi,
                     "topics with zero below 80": int((cnt == 0).sum()), "min topic share": (cnt / n).min(), "max topic share": (cnt / n).max()})

    def rho(a, b, label):
        r_, p_ = spearmanr(T[a], T[b])
        rows.append({"measure": "Spearman across 30 topics, share below 80", "condition": label, "value": r_, "p": p_})

    rho("effort added: share below 80", "unsteered: share below 80", "effort added vs unsteered")
    rho("effort added: share below 80", "random added: share below 80", "effort added vs random added")
    rho("random added: share below 80", "unsteered: share below 80", "random added vs unsteered")
    rho("effort added: share below 80", "effort removed: share below 80", "effort added vs effort removed")
    rho("effort removed: share below 80", "unsteered: share below 80", "effort removed vs unsteered")
    rho("effort added, layers 6 to 16: share below 80", "effort added, layers 18 to 28: share below 80", "effort added, layers 6 to 16 vs layers 18 to 28")
    rho("effort added, repeat 0: share below 80", "effort added, repeat 1: share below 80", "effort added, repeat 0 vs repeat 1")
    above = int((T["effort added: share below 80"] > T["unsteered: share below 80"]).sum())
    rows.append({"measure": "topics (of 30) where the effort-added share below 80 is above the same topic's unsteered share", "condition": "effort added vs unsteered", "value": above})
    above_r = int((T["effort added, random run's grid: share below 80"] > T["random added: share below 80"]).sum())
    rows.append({"measure": "topics (of 30) where the effort-added share below 80 is above the same topic's random-added share (same layers and doses)", "condition": "effort added, random run's grid vs random added", "value": above_r})
    # the topics that are worst unsteered: how much of the effort damage do they carry
    worst_u = T.sort_values("unsteered: share below 80", ascending=False).head(5)
    rows.append({"measure": "share of effort-added below-80 essays carried by the 5 topics that are lowest unsteered", "condition": "topics " + ", ".join(worst_u.topic),
                 "value": worst_u["effort added: below 80"].sum() / T["effort added: below 80"].sum()})
    top_e = T.sort_values("effort added: below 80", ascending=False).head(5)
    rows.append({"measure": "the 5 topics with most effort-added below-80 essays: their unsteered share below 80", "condition": "topics " + ", ".join(top_e.topic),
                 "value": top_e["unsteered: below 80"].sum() / top_e["unsteered: essays"].sum(), "essays": int(top_e["unsteered: essays"].sum())})
    rest = T.drop(top_e.index)
    rows.append({"measure": "the other 25 topics: their unsteered share below 80", "condition": "",
                 "value": rest["unsteered: below 80"].sum() / rest["unsteered: essays"].sum(), "essays": int(rest["unsteered: essays"].sum())})
    rows.append({"measure": "the 5 topics with most effort-added below-80 essays: their effort-added share below 80", "condition": "topics " + ", ".join(top_e.topic),
                 "value": top_e["effort added: below 80"].sum() / top_e["effort added: essays"].sum(), "essays": int(top_e["effort added: essays"].sum())})
    rows.append({"measure": "the other 25 topics: their effort-added share below 80", "condition": "",
                 "value": rest["effort added: below 80"].sum() / rest["effort added: essays"].sum(), "essays": int(rest["effort added: essays"].sum())})
    rows.append({"measure": "the other 25 topics: their random-added share below 80", "condition": "",
                 "value": rest["random added: below 80"].sum() / rest["random added: essays"].sum(), "essays": int(rest["random added: essays"].sum())})
    rows.append({"measure": "the 5 topics with most effort-added below-80 essays: their random-added share below 80", "condition": "topics " + ", ".join(top_e.topic),
                 "value": top_e["random added: below 80"].sum() / top_e["random added: essays"].sum(), "essays": int(top_e["random added: essays"].sum())})
    K = pd.DataFrame(rows)
    K.to_csv(out / "1c_concentration.csv", index=False)

    S = T.sort_values("effort added: share below 80", ascending=False).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(12, 4.4))
    xs = np.arange(len(S))
    ax.bar(xs, S["effort added: share below 80"], color=BLUE, width=0.7, label="effort added (96 essays per topic)")
    ax.scatter(xs, S["random added: share below 80"], color=ORANGE, s=42, zorder=3, marker="D", label="random direction added (32 per topic)")
    ax.scatter(xs, S["unsteered: share below 80"], color=GREY, s=46, zorder=4, edgecolor="black", linewidth=0.8, label=f"unsteered ({int(S['unsteered: essays'].min())} per topic)")
    ax.set_xticks(xs, S.topic, fontsize=8)
    ax.set_xlabel("essay topic (index), sorted by the effort-added share")
    ax.set_ylabel("share of essays with coherence below 80")
    ax.set_title("Low-coherence essays by topic: effort added (r +0.025 to +0.1, layers 6 to 28), random added, unsteered", fontsize=11)
    ax.legend(frameon=False, fontsize=9)
    style(ax)
    fig.tight_layout()
    fig.savefig(out / "1c_topics.png", dpi=150)
    plt.close(fig)
    return T, K


# ---------------------------------------------------------------- 1d

def curve_row(g: pd.DataFrame, **label) -> dict:
    n = len(g)
    w, l = int((g.outcome == "W").sum()), int((g.outcome == "L").sum())
    dmg = int((g.part == "damaged").sum())
    won_ok = int(((g.outcome == "W") & (g.part != "damaged")).sum())
    lost_ok = int(((g.outcome == "L") & (g.part != "damaged")).sum())
    d_lo, d_hi = ci(dmg, n)
    w_lo, w_hi = ci(won_ok, n)
    return {**label, "pairs": n, "W": w, "L": l, "win rate": w / (w + l) if w + l else np.nan,
            "damaged": dmg, "share damaged": dmg / n, "damaged ci lo": d_lo, "damaged ci hi": d_hi,
            "won at equal-or-better coherence": won_ok, "share won at equal-or-better coherence": won_ok / n, "won ci lo": w_lo, "won ci hi": w_hi,
            "share lost at equal-or-better coherence": lost_ok / n,
            "share damaged and lost": int(((g.outcome == "L") & (g.part == "damaged")).sum()) / n,
            "share damaged and won": int(((g.outcome == "W") & (g.part == "damaged")).sum()) / n,
            "share below 80": (g.coh_a < 80).mean(), "coh steered": g.coh_a.mean(), "coh unsteered": g.coh_b.mean()}


def part_1d(D: dict, out: Path) -> pd.DataFrame:
    E, R, N = D["E"], D["R"], D["N"]
    rows = [curve_row(N, steered="unsteered vs unsteered", layer="", r=0.0)]
    for (layer, r), g in E.groupby(["layer0", "r"]):
        rows.append(curve_row(g, steered="effort", layer=layer, r=r))
    for (layer, r), g in R.groupby(["layer0", "r"]):
        rows.append(curve_row(g, steered="random", layer=layer, r=r))
    # pooled over layers, per dose
    for r, g in E.groupby("r"):
        rows.append(curve_row(g, steered="effort", layer="6 to 28", r=r))
        for b in ("6 to 14", "16 to 28"):
            rows.append(curve_row(g[g.layer0.map(band) == b], steered="effort", layer=b, r=r))
        if len(R[np.isclose(R.r, r)]):
            rows.append(curve_row(g[g.layer0.isin(GRID_LAYERS)], steered="effort", layer="6+10+14+20", r=r))
    for r, g in R.groupby("r"):
        rows.append(curve_row(g, steered="random", layer="6+10+14+20", r=r))
    C = pd.DataFrame(rows)
    C["layer"] = C.layer.astype(str)
    C.to_csv(out / "1d_dose_curve.csv", index=False)

    layers = sorted(E.layer0.unique())
    null = C[C.steered == "unsteered vs unsteered"].iloc[0]
    fig, axes = plt.subplots(3, 4, figsize=(13, 8.2), sharex=True, sharey=True)
    for ax, layer in zip(axes.ravel(), layers):
        s = C[(C.steered == "effort") & (C.layer == str(layer)) & (C.r > 0)].sort_values("r")
        ax.plot(s.r, s["share won at equal-or-better coherence"], color=BLUE, lw=2, marker="o", ms=6, label="effort: won at equal-or-better coherence")
        ax.plot(s.r, s["share damaged"], color=BLUE, lw=2, ls="--", marker="s", ms=6, mfc="white", label="effort: damaged (coherence more than 3 below partner)")
        rn = C[(C.steered == "random") & (C.layer == str(layer)) & (C.r > 0)].sort_values("r")
        if len(rn):
            ax.plot(rn.r, rn["share won at equal-or-better coherence"], color=ORANGE, lw=1.5, marker="o", ms=5, label="random: won at equal-or-better coherence")
            ax.plot(rn.r, rn["share damaged"], color=ORANGE, lw=1.5, ls="--", marker="s", ms=5, mfc="white", label="random: damaged")
        ax.axhline(null["share won at equal-or-better coherence"], color=GREY, lw=1.2, label="unsteered vs unsteered: won at equal-or-better")
        ax.axhline(null["share damaged"], color=GREY, lw=1.2, ls="--", label="unsteered vs unsteered: damaged")
        ax.set_title(f"layer {layer}", fontsize=10)
        ax.set_xticks([0.025, 0.05, 0.075, 0.1], ["+0.025", "+0.05", "+0.075", "+0.1"], fontsize=8)
        style(ax)
    for ax in axes[-1]:
        ax.set_xlabel("dose r added")
    for ax in axes[:, 0]:
        ax.set_ylabel("share of all pairs in the cell")
    h, l = axes.ravel()[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=9)
    fig.suptitle("Adding the effort direction: share of pairs won at equal-or-better coherence, and share damaged, by layer and dose (60 pairs per cell)", fontsize=11)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(out / "1d_dose_curve.png", dpi=150)
    plt.close(fig)
    return C


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/steering/w9_analysis")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 60)
    pd.set_option("display.max_rows", 400)

    P = add_part(w8.load_all())
    D = {k: v for k, v in split(P).items()}
    E, R, N, U = D["E"], D["R"], D["N"], D["U"]
    print(f"effort sweep pairs {len(E)}, random pairs {len(R)}, null pairs {len(N)} ({N.run.nunique()} runs), distinct unsteered essays {len(U)}")
    print(f"missing coherence: effort {int(E.coh_a.isna().sum())}, random {int(R.coh_a.isna().sum())}, null {int(N.coh_a.isna().sum())}")
    print("coherence scores used by the judge (effort sweep, side a):", E.coh_a.value_counts().sort_index().to_dict())
    print("gap values (effort sweep):", E.coh_d.value_counts().sort_index().to_dict())

    A = part_1a(D, args.out)
    print("\n== 1a"); print(A.round(3).to_string(index=False))
    Cb, Pb = mixture_tables(E, R, N, +1, args.out, "1b")
    print("\n== 1b pooled"); print(Pb.round(3).to_string(index=False))
    T, K = part_1c(D, args.out)
    print("\n== 1c"); print(T.round(2).to_string(index=False)); print(K.round(3).to_string(index=False))
    C = part_1d(D, args.out)
    print("\n== 1d"); print(C.round(3).to_string(index=False))
    Ce, Pe = mixture_tables(E, R, N, -1, args.out, "1e")
    print("\n== 1e pooled"); print(Pe.round(3).to_string(index=False))
    print(f"\nwritten to {args.out}")


if __name__ == "__main__":
    main()
