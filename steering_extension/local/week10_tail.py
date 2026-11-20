"""Week 10 tail check: the week-6/7 essay cells generated again with a nucleus cut (top-p 0.95, run w10_tail95)
against the same cells sampled from the full distribution (w6_sweep for E, w7_random for the random direction, both
runs' unsteered pairs for the null). Same prompts, vectors, items and repeats; only the sampler differs.

Per cell and sampler: panel W / L and win rate (side a against the unsteered partner of its own run), coherence of
both sides, the share of pairs where the steered essay is damaged (more than 3 coherence points below its partner),
the win rate at equal coherence (within 3 points), and the share of texts with a foreign-script word. Fisher tests
compare the samplers cell by cell.

  python -m steering_extension.local.week10_tail     # writes outputs/steering/w10_analysis/tail_tables.txt
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

from steering_extension.local.analyze_dose import pair_table
from steering_extension.local.common import ROOT
from steering_extension.local.week10_tokens import ANY

RUNS = ROOT / "outputs" / "steering" / "runs"
OUT = ROOT / "outputs" / "steering" / "w10_analysis"
CELLS = ["steer_baseline", "steer_E_L6_r+0.050_response", "steer_E_L6_r+0.100_response", "steer_E_L14_r+0.050_response",
         "steer_E_L14_r+0.100_response", "steer_rand0_L6_r+0.100_response", "steer_rand0_L14_r+0.100_response"]
FULL = {"steer_baseline": ["w6_sweep", "w7_random"], "steer_rand0_L6_r+0.100_response": ["w7_random"], "steer_rand0_L14_r+0.100_response": ["w7_random"]}
GAP = 3


def foreign(rd: Path) -> dict[str, bool]:
    gens = {}
    for l in (rd / "generations.jsonl").open():
        g = json.loads(l)
        gens[g["output_id"]] = g
    out = {}
    for oid, g in gens.items():
        src = gens.get(g.get("alias_of"), g) if g.get("alias_of") else g
        out[oid] = bool(ANY.search(src.get("output_text") or ""))
    return out


def load(run: str, sampler: str) -> pd.DataFrame:
    rd = RUNS / run
    P = pair_table(rd)
    P = P[P.cell.isin(CELLS)].copy()
    f = foreign(rd)
    jobs = {json.loads(l)["pair_uid"]: json.loads(l) for l in (rd / "generation_jobs.jsonl").open()}
    P["foreign_a"] = [f.get(f"{u}::a", False) for u in P.pair_uid]
    P["foreign_b"] = [f.get(jobs[u].get("alias_b") or f"{u}::b", False) for u in P.pair_uid]
    P["run"], P["sampler"] = run, sampler
    return P


def stats(g: pd.DataFrame) -> dict:
    w, l = int((g.outcome == "W").sum()), int((g.outcome == "L").sum())
    d = g.coh_a - g.coh_b
    eq = g[d.abs() <= GAP]
    we, le = int((eq.outcome == "W").sum()), int((eq.outcome == "L").sum())
    return {"pairs": len(g), "W": w, "L": l, "win_rate": w / (w + l) if w + l else np.nan, "coh_a": g.coh_a.mean(), "coh_b": g.coh_b.mean(),
            "damaged": int((d < -GAP).sum()), "damaged_share": float((d < -GAP).mean()), "W_eq": we, "L_eq": le,
            "win_rate_eq": we / (we + le) if we + le else np.nan, "foreign_a": float(g.foreign_a.mean()), "foreign_b": float(g.foreign_b.mean()),
            "words_a": g.words_a.mean()}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = [load("w10_tail95", "top-p 0.95")]
    for run in ("w6_sweep", "w7_random"):
        frames.append(load(run, "full"))
    P = pd.concat(frames, ignore_index=True)
    keep = []
    for cell in CELLS:
        runs = FULL.get(cell, ["w6_sweep"])
        keep.append(P[(P.cell == cell) & ((P.sampler != "full") | P.run.isin(runs))])
    P = pd.concat(keep, ignore_index=True)
    P.to_csv(OUT / "tail_pairs.csv", index=False)
    rows = []
    for (cell, sampler), g in P.groupby(["cell", "sampler"], sort=False):
        rows.append({"cell": cell, "sampler": sampler, **stats(g)})
    S = pd.DataFrame(rows)
    tests = []
    for cell in CELLS:
        a, b = S[(S.cell == cell) & (S.sampler == "top-p 0.95")], S[(S.cell == cell) & (S.sampler == "full")]
        if a.empty or b.empty:
            continue
        a, b = a.iloc[0], b.iloc[0]
        tests.append({"cell": cell, "p_win": fisher_exact([[a.W, a.L], [b.W, b.L]])[1],
                      "p_damaged": fisher_exact([[a.damaged, a.pairs - a.damaged], [b.damaged, b.pairs - b.damaged]])[1],
                      "p_win_eq": fisher_exact([[a.W_eq, a.L_eq], [b.W_eq, b.L_eq]])[1]})
    T = pd.DataFrame(tests)
    S.to_csv(OUT / "tail_cells.csv", index=False)
    T.to_csv(OUT / "tail_tests.csv", index=False)
    pd.set_option("display.width", 250)
    pooled = []
    for label, sel in [("E added, all four cells", P.cell.str.startswith("steer_E")), ("random added, both cells", P.cell.str.startswith("steer_rand")), ("unsteered", P.cell == "steer_baseline")]:
        for sampler, g in P[sel].groupby("sampler"):
            pooled.append({"group": label, "sampler": sampler, **stats(g)})
    Q = pd.DataFrame(pooled)
    Q.to_csv(OUT / "tail_pooled.csv", index=False)
    text = "\n".join(["== A. per cell (side a vs the unsteered partner of its own run)", S.round(3).to_string(index=False),
                      "\n== B. top-p 0.95 against full distribution, Fisher p", T.round(3).to_string(index=False),
                      "\n== C. pooled", Q.round(3).to_string(index=False)])
    (OUT / "tail_tables.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
