"""Dose-response analysis for a steered-vs-baseline run (essay curve).

Reads <run_dir>/generation_jobs.jsonl, judge_votes.jsonl, generations.jsonl, coherence.jsonl and reports:
  1. per-cell table with the paper's conventions (panel majority, flips -> tie, ties excluded, exact CI) via
     analyze_cells' logic, plus all-vote tallies (every judge x order; no tie rule) as a higher-resolution view;
  2. logistic regression of the steered side winning on signed dose r (resolved pairs only), item-clustered
     SEs, for each (key, layer) with >= 3 doses; separate slopes for r <= 0 and r >= 0 when both sides exist;
  3. Fisher exact tests of each E cell against the pooled random cells at the same |r| and sign.
Writes <run_dir>/dose_summary.csv and prints everything.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from utility_behavior_gap.judging import derive_judge_verdict, derive_panel_winner_condition  # noqa: E402
from steering_extension.local.analyze_cells import clopper_pearson  # noqa: E402

CELL_RE = re.compile(r"^steer_(?P<key>.+)_L(?P<layer>\d+)_r(?P<r>[+-]\d+\.\d+)_(?P<mode>\w+)$")


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open()] if p.exists() else []


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()
    rd = args.run_dir
    jobs = {j["pair_uid"]: j for j in load(rd / "generation_jobs.jsonl")}
    votes = load(rd / "judge_votes.jsonl")
    gens = {g["output_id"]: g for g in load(rd / "generations.jsonl")}
    coh = {c["output_id"]: c["coherence"] for c in load(rd / "coherence.jsonl") if c.get("coherence") is not None}
    by_pj: dict[tuple[str, str], list[str]] = defaultdict(list)
    for v in votes:
        if v.get("success") is False:
            continue
        by_pj[(v["pair_uid"], v["judge_model"])].append(v["winner_condition"])
    # pair-level outcomes
    pair_rows = []
    for uid, job in jobs.items():
        jms = [jm for (p, jm) in by_pj if p == uid]
        if not jms:
            continue
        verdicts = [derive_judge_verdict(by_pj[(uid, jm)]) for jm in jms]
        panel = derive_panel_winner_condition(job, verdicts)
        cell = job.get("cell", job["comparison"])
        m = CELL_RE.match(cell)
        allv = [w for jm in jms for w in by_pj[(uid, jm)]]
        pair_rows.append({
            "pair_uid": uid, "cell": cell, "item": job.get("item_index", ""), "repeat": job.get("repeat", ""),
            "key": m["key"] if m else "baseline", "layer": int(m["layer"]) if m else -1, "r": float(m["r"]) if m else 0.0,
            "outcome": "W" if panel == job["condition_a"] else "L" if panel == job["condition_b"] else "T",
            "votes_w": sum(w == job["condition_a"] for w in allv), "votes_l": sum(w == job["condition_b"] for w in allv), "votes_n": len(allv),
            "words_a": len(gens.get(f"{uid}::a", {}).get("output_text", "").split()), "words_b": len(gens.get(f"{uid}::b", {}).get("output_text", "").split()),
            "coh_a": coh.get(f"{uid}::a", np.nan), "coh_b": coh.get(job.get("alias_b") or f"{uid}::b", np.nan),
            "trunc_a": gens.get(f"{uid}::a", {}).get("finish_reason") == "length",
        })
    P = pd.DataFrame(pair_rows)
    # 1. per-cell table
    rows = []
    for cell, g in P.groupby("cell"):
        w, l, t = (g.outcome == "W").sum(), (g.outcome == "L").sum(), (g.outcome == "T").sum()
        n = w + l
        lo, hi = clopper_pearson(int(w), int(n))
        from scipy.stats import binomtest
        p = binomtest(int(w), int(n), 0.5).pvalue if n else np.nan
        vw, vl = g.votes_w.sum(), g.votes_l.sum()
        rows.append({"cell": cell, "key": g.key.iloc[0], "layer": g.layer.iloc[0], "r": g.r.iloc[0], "pairs": len(g), "W": w, "L": l, "T": t, "win_rate": w / n if n else np.nan, "ci_lo": lo, "ci_hi": hi, "p": p,
                     "allvote_rate": vw / (vw + vl) if vw + vl else np.nan, "allvote_n": int(vw + vl), "words_a": g.words_a.mean(), "words_b": g.words_b.mean(), "coh_a": g.coh_a.mean(), "coh_pass80_a": (g.coh_a >= 80).mean() if g.coh_a.notna().any() else np.nan, "trunc_a": int(g.trunc_a.sum())})
    T = pd.DataFrame(rows).sort_values(["key", "layer", "r"])
    pd.set_option("display.width", 250)
    print("== per-cell (paper conventions) + all-vote rate")
    print(T[["cell", "pairs", "W", "L", "T", "win_rate", "ci_lo", "ci_hi", "p", "allvote_rate", "words_a", "words_b", "coh_a", "coh_pass80_a", "trunc_a"]].round(3).to_string(index=False))
    T.to_csv(rd / "dose_summary.csv", index=False)
    # 2. logistic dose regression per (key, layer)
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        print("\n== logistic regression: P(steered wins | resolved) ~ r, item-clustered SE")
        for (key, layer), g in P[(P.key != "baseline")].groupby(["key", "layer"]):
            res = g[g.outcome != "T"].copy()
            if res.r.nunique() < 3 or len(res) < 20:
                continue
            res["win"] = (res.outcome == "W").astype(int)
            for label, sub in (("all", res), ("r<=0", res[res.r <= 0]), ("r>=0", res[res.r >= 0])):
                if sub.r.nunique() < 2 or len(sub) < 15:
                    continue
                try:
                    fit = smf.glm("win ~ r", data=sub, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": sub["item"].astype(str)})
                    print(f"  {key} L{layer} [{label}] n={len(sub)} slope={fit.params['r']:.2f} se={fit.bse['r']:.2f} p={fit.pvalues['r']:.2g}")
                except Exception as e:  # noqa: BLE001
                    print(f"  {key} L{layer} [{label}] fit failed: {e}")
    except ImportError:
        print("statsmodels missing: regression skipped")
    # 3. Fisher: E cells vs pooled random at same signed r
    print("\n== Fisher exact: E cell vs pooled random cells at the same signed dose and layer")
    rnd = P[P.key.str.startswith("rand")]
    for cell, g in P[P.key.str.startswith("E")].groupby("cell"):
        r, layer = g.r.iloc[0], g.layer.iloc[0]
        rr = rnd[(np.isclose(rnd.r, r)) & (rnd.layer == layer)]
        if not len(rr):
            continue
        a = [(g.outcome == "W").sum(), (g.outcome == "L").sum()]
        b = [(rr.outcome == "W").sum(), (rr.outcome == "L").sum()]
        if sum(a) == 0 or sum(b) == 0:
            continue
        _, p = fisher_exact([a, b])
        print(f"  {cell}: E {a[0]}/{a[1]} vs random {b[0]}/{b[1]}  p={p:.3g}")


if __name__ == "__main__":
    main()
