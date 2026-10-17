"""Stage L2 analysis: rank candidate injection layers with judge-free criteria.

Inputs in <run_dir> (a make_steering_jobs run on grant/postmortem with cells KEY:LAYER:R):
  generations.jsonl, generation_jobs.jsonl        steered (side a) vs shared unsteered baseline (side b)
  features.csv / signature.csv                    from text_features.py (signature match per cell x task)
  projections*.jsonl                              from steer/project.py (arrival: re-encoded projections on E)
  kl_check.jsonl                                  from steer/kl_check.py (optional)
  coherence.jsonl                                 optional, from coherence_judge.py (paid)

Per cell (key, layer, r) and task this script reports:
  mechanical coherence: repeat4 (fraction of repeated 4-grams), nonascii rate, truncation rate, words ratio
  arrival: Welch t of proj_rmean(steered) vs proj_rmean(baseline) at the monitoring layer, and Cohen's d
  KL (if present), signature_r / signature_cos / sign agreement, words_d
and applies the pre-registered two-hurdle rule (docs/layer_selection.md Stage L2):
  pass if repeat4 <= base + 0.05 and trunc <= base + 0.10 and nonascii <= base + 0.01 and (KL median < 0.1 if available)
  and arrival |t| >= 2;  r_L = largest passing dose per layer;  rank layers by signature_r at r_L.
Writes <run_dir>/layer_sweep.csv and <run_dir>/layer_rank.csv and prints both.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

CELL_RE = re.compile(r"^steer_(?P<key>.+)_L(?P<layer>\d+)_r(?P<r>[+-]\d+\.\d+)_(?P<mode>\w+)$")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open()] if p.exists() else []


def repeat4(text: str) -> float:
    toks = text.split()
    if len(toks) < 8:
        return 0.0
    grams = [tuple(toks[i : i + 4]) for i in range(len(toks) - 3)]
    return 1.0 - len(set(grams)) / len(grams)


def nonascii(text: str) -> float:
    return sum(1 for ch in text if ord(ch) > 127 and ch not in "—–’‘“”…") / max(1, len(text))


def welch(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    if len(x) < 2 or len(y) < 2:
        return (math.nan, math.nan)
    vx, vy = x.var(ddof=1), y.var(ddof=1)
    se = math.sqrt(vx / len(x) + vy / len(y))
    t = (x.mean() - y.mean()) / se if se > 0 else math.nan
    sp = math.sqrt(((len(x) - 1) * vx + (len(y) - 1) * vy) / (len(x) + len(y) - 2))
    d = (x.mean() - y.mean()) / sp if sp > 0 else math.nan
    return (t, d)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--monitor-layer", type=int, default=None, help="layer for the arrival test; default: the steered layer itself")
    ap.add_argument("--arrival-key", default=None, help="vector key used for arrival projections; default: the cell's key")
    ap.add_argument("--kl-max", type=float, default=0.1)
    args = ap.parse_args()
    rd = args.run_dir
    jobs = {j["pair_uid"]: j for j in load_jsonl(rd / "generation_jobs.jsonl")}
    gens = {g["output_id"]: g for g in load_jsonl(rd / "generations.jsonl")}
    sig = pd.read_csv(rd / "signature.csv") if (rd / "signature.csv").exists() else pd.DataFrame()
    proj = pd.DataFrame([r for p in sorted(rd.glob("projections*.jsonl")) for r in load_jsonl(p)])
    kl = pd.DataFrame(load_jsonl(rd / "kl_check.jsonl"))
    coh = {c["output_id"]: c["coherence"] for c in load_jsonl(rd / "coherence.jsonl") if c.get("coherence") is not None}
    # per output mechanical stats
    mech = {}
    for oid, g in gens.items():
        t = g.get("output_text", "")
        mech[oid] = {"repeat4": repeat4(t), "nonascii": nonascii(t), "trunc": float(g.get("finish_reason") == "length"), "words": len(t.split())}
    rows = []
    cells = defaultdict(list)
    for uid, j in jobs.items():
        cells[(j.get("cell", j["comparison"]), j["task"])].append(uid)
    base_stats = {}
    for (cell, task), uids in cells.items():
        if cell != "steer_baseline":
            continue
        b = [mech[f"{u}::b"] for u in uids if f"{u}::b" in mech]
        a = [mech[f"{u}::a"] for u in uids if f"{u}::a" in mech]
        allb = a + b
        base_stats[task] = {k: float(np.mean([m[k] for m in allb])) for k in ("repeat4", "nonascii", "trunc", "words")}
    for (cell, task), uids in cells.items():
        m = CELL_RE.match(cell)
        if not m:
            continue
        key, layer, r = m["key"], int(m["layer"]), float(m["r"])
        a = [mech[f"{u}::a"] for u in uids if f"{u}::a" in mech]
        if not a:
            continue
        bs = base_stats.get(task, {})
        row = {"cell": cell, "task": task, "key": key, "layer": layer, "r": r, "n": len(a)}
        for k in ("repeat4", "nonascii", "trunc", "words"):
            row[k] = float(np.mean([x[k] for x in a]))
            row[f"base_{k}"] = bs.get(k, math.nan)
        row["words_ratio"] = row["words"] / bs["words"] if bs.get("words") else math.nan
        # arrival
        mon = args.monitor_layer if args.monitor_layer is not None else layer
        akey = args.arrival_key or key
        if len(proj):
            pa = proj[(proj.layer == mon) & (proj.key == akey) & (proj.output_id.isin([f"{u}::a" for u in uids]))]["proj_rmean"].to_numpy()
            pb_ids = {jobs[u].get("alias_b") or f"{u}::b" for u in uids}
            pb = proj[(proj.layer == mon) & (proj.key == akey) & (proj.output_id.isin(pb_ids))]["proj_rmean"].to_numpy()
            t, d = welch(pa, pb)
            row.update({"arrival_t": round(t, 2) if t == t else math.nan, "arrival_d": round(d, 3) if d == d else math.nan, "arrival_n": int(min(len(pa), len(pb)))})
        if len(kl):
            k = kl[(kl.key == key) & (kl.layer == layer) & (np.isclose(kl.r, r))]
            row["kl_median"] = float(k["kl_median"].iloc[0]) if len(k) else math.nan
        if len(sig):
            s = sig[(sig.cell == cell) & (sig.task == task)]
            for c in ("signature_r", "signature_cos", "sign_agreement", "words_d"):
                row[c] = float(s[c].iloc[0]) if len(s) else math.nan
        ca = [coh[f"{u}::a"] for u in uids if f"{u}::a" in coh]
        row["coherence"] = float(np.mean(ca)) if ca else math.nan
        # hurdles
        h_mech = (row["repeat4"] <= bs.get("repeat4", 0) + 0.05) and (row["trunc"] <= bs.get("trunc", 0) + 0.10) and (row["nonascii"] <= bs.get("nonascii", 0) + 0.01)
        h_kl = (row.get("kl_median", 0) < args.kl_max) if row.get("kl_median", math.nan) == row.get("kl_median", math.nan) else True
        h_arr = abs(row.get("arrival_t", 0)) >= 2 if row.get("arrival_t", math.nan) == row.get("arrival_t", math.nan) else False
        row.update({"pass_mech": h_mech, "pass_kl": h_kl, "pass_arrival": h_arr, "pass_all": h_mech and h_kl and h_arr})
        rows.append(row)
    df = pd.DataFrame(rows).sort_values(["task", "key", "layer", "r"])
    df.to_csv(rd / "layer_sweep.csv", index=False)
    cols = [c for c in ["task", "key", "layer", "r", "n", "words_ratio", "repeat4", "trunc", "kl_median", "arrival_t", "signature_r", "signature_cos", "sign_agreement", "words_d", "coherence", "pass_all"] if c in df]
    print(df[cols].to_string(index=False))
    # selection: per task x key x layer, largest passing r; rank by signature_r there
    rank_rows = []
    for (task, key, layer), g in df.groupby(["task", "key", "layer"]):
        ok = g[g.pass_all]
        if len(ok):
            best = ok.sort_values("r").iloc[-1]
            rank_rows.append({"task": task, "key": key, "layer": layer, "r_L": best.r, "signature_r_at_rL": best.get("signature_r", math.nan), "arrival_t_at_rL": best.get("arrival_t", math.nan), "n_pass": len(ok), "n_doses": len(g)})
        else:
            rank_rows.append({"task": task, "key": key, "layer": layer, "r_L": math.nan, "signature_r_at_rL": math.nan, "arrival_t_at_rL": math.nan, "n_pass": 0, "n_doses": len(g)})
    rk = pd.DataFrame(rank_rows).sort_values(["task", "key", "signature_r_at_rL"], ascending=[True, True, False])
    rk.to_csv(rd / "layer_rank.csv", index=False)
    print("\nlayer ranking (largest passing dose per layer, ranked by signature match):")
    print(rk.to_string(index=False))


if __name__ == "__main__":
    main()
