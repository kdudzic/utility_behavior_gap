"""Week 8 follow-up: compare role-vector steering cells with the E cell and the pooled random cell at the same
layer and dose (same table as section 4.3 of docs/week8_results.md, built there inline for w8_role_steer).

For every (key, layer, r) cell in the given runs: W / L of side a (steered) vs the unsteered essay, ties, mean
coherence a / b, the E cell and the random cell at that layer and dose from the pooled week-6/7 runs (Fisher p),
win rate among resolved pairs whose coherence differs by at most 3 points, and the share of pairs with a
coherence gap below -3 / above +3.
Run: .venv/bin/python -m steering_extension.local.week8b_compare --run-dir outputs/steering/runs/w8b_role_local \
       --run-dir outputs/steering/runs/w8b_role_remote --out outputs/steering/w8_analysis/role_recipes_vs_E_random.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from steering_extension.local.analyze_dose import pair_table  # noqa: E402
from steering_extension.local.week8_coherence import load_all  # noqa: E402


def wl(g: pd.DataFrame) -> tuple[int, int]:
    return int((g.outcome == "W").sum()), int((g.outcome == "L").sum())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, action="append", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    R = pd.concat([pair_table(d).assign(run=d.name) for d in args.run_dir], ignore_index=True)
    R["coh_d"] = R.coh_a - R.coh_b
    P = load_all()
    rows = []
    null = R[R.key == "baseline"]
    if len(null):
        a = wl(null)
        rows.append({"run": "+".join(sorted(null.run.unique())), "cell": "null", "W/L": f"{a[0]}/{a[1]}", "win": round(a[0] / max(sum(a), 1), 2), "ties": int((null.outcome == "T").sum()), "coh a/b": f"{null.coh_a.mean():.1f}/{null.coh_b.mean():.1f}"})
    cells = R[R.key != "baseline"][["run", "key", "layer0", "r"]].drop_duplicates().sort_values(["run", "key", "layer0"])
    for _, c in cells.iterrows():
        g = R[(R.run == c.run) & (R.key == c.key) & (R.layer0 == c.layer0) & np.isclose(R.r, c.r)]
        e = P[(P.type == "effort") & (P.layer0 == c.layer0) & np.isclose(P.r, c.r)]
        rn = P[(P.type == "random") & (P.layer0 == c.layer0) & np.isclose(P.r, c.r)]
        a, b, d = wl(g), wl(e), wl(rn)
        eq = g[(g.outcome != "T") & (g.coh_d.abs() <= 3)]
        rows.append({
            "run": c.run, "cell": f"{c.key} L{c.layer0} r{c.r:+.2f}", "W/L": f"{a[0]}/{a[1]}", "win": round(a[0] / max(sum(a), 1), 2), "ties": int((g.outcome == "T").sum()),
            "coh a/b": f"{g.coh_a.mean():.1f}/{g.coh_b.mean():.1f}", "share coh>=80 a": round((g.coh_a >= 80).mean(), 2),
            "E W/L": f"{b[0]}/{b[1]}", "p vs E": round(fisher_exact([a, b])[1], 3) if sum(b) else None,
            "random W/L": f"{d[0]}/{d[1]} ({rn.run.unique()[0] if len(rn) else ''})", "p vs random": round(fisher_exact([a, d])[1], 3) if sum(d) else None,
            "win | equal coh": f"{(eq.outcome == 'W').mean():.2f} (n={len(eq)})" if len(eq) else "-", "share gap<-3": round((g.coh_d < -3).mean(), 2), "share gap>3": round((g.coh_d > 3).mean(), 2),
            "words a/b": f"{g.words_a.mean():.0f}/{g.words_b.mean():.0f}",
        })
    T = pd.DataFrame(rows)
    pd.set_option("display.width", 300)
    print(T.to_string(index=False))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    T.to_csv(args.out, index=False)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
