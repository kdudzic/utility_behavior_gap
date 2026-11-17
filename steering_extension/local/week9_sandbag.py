"""Week 9, sandbagging and the effort direction (week9_plan.txt item 4): tables for the judged runs.

Reads, per run dir (default w9_sandbag_local and w9_sandbag_remote): generation_jobs.jsonl, generations.jsonl,
judge_votes.jsonl, coherence.jsonl, refusal_labels.jsonl (sandbag_refusals.py), projections.shard0.jsonl.

A. Cell table. One row per cell: pairs, pairs dropped by the refusal screen (a harmful-prompt text on either side
   labelled full_refusal, partial_refusal or degenerate; the paper's strict screen), W / L / T for side a, win rate,
   exact binomial p against 0.50, mean coherence and words of both sides, and Fisher p against a reference cell
   (steered-vs-harmful cells against the random-direction cell of the same run; steered-vs-empty cells against the
   untouched harmful vs empty cell). Coherence and refusal labels are looked up by output text, so aliased sides
   are covered.
B. Projections. For the untouched texts: harmful vs framed-empty and max-effort vs neutral, Cohen's d and AUC of the
   response-mean projection (as a fraction of the residual RMS) onto each unit vector and layer, and the ratio of
   the sandbagging shift to the exhortation shift. Within untouched harmful vs empty pairs: does the harmful text's
   E projection separate the pairs the harmful side won from those it lost.

Writes CSVs to --out (default outputs/steering/w9_analysis) with prefix sandbag_ and prints them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, fisher_exact, mannwhitneyu

from steering_extension.local.analyze_dose import derive_judge_verdict, derive_panel_winner_condition

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "outputs/steering/runs"
BAD = {"full_refusal", "partial_refusal", "degenerate"}


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open()] if p.exists() else []


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def pair_table(rd: Path) -> pd.DataFrame:
    jobs = {j["pair_uid"]: j for j in load(rd / "generation_jobs.jsonl")}
    gens = {g["output_id"]: g for g in load(rd / "generations.jsonl")}
    text_of = {oid: (g.get("output_text") or "") for oid, g in gens.items()}
    coh_by_sha = {sha(text_of[c["output_id"]]): c["coherence"] for c in load(rd / "coherence.jsonl") if c.get("coherence") is not None and c["output_id"] in text_of}
    lab_by_sha = {r["text_sha"]: r["label"] for r in load(rd / "refusal_labels.jsonl")}
    by_pj: dict[tuple[str, str], list[str]] = defaultdict(list)
    for v in load(rd / "judge_votes.jsonl"):
        if v.get("success") is False:
            continue
        by_pj[(v["pair_uid"], v["judge_model"])].append(v["winner_condition"])
    rows = []
    for uid, job in jobs.items():
        jms = [jm for (p, jm) in by_pj if p == uid]
        ta, tb = text_of.get(f"{uid}::a", ""), text_of.get(f"{uid}::b", "")
        labels = [lab_by_sha.get(sha(t)) for t, cond in ((ta, job["condition_a"]), (tb, job["condition_b"])) if "harmful" in cond]
        if jms:
            panel = derive_panel_winner_condition(job, [derive_judge_verdict(by_pj[(uid, jm)]) for jm in jms])
            outcome = "W" if panel == job["condition_a"] else "L" if panel == job["condition_b"] else "T"
        else:
            outcome = None
        rows.append({
            "run": rd.name, "pair_uid": uid, "cell": job.get("cell", job["comparison"]), "comparison": job["comparison"], "item": job.get("item_index", ""), "repeat": job.get("repeat", ""),
            "cause": job.get("cause_pair_label", ""), "outcome": outcome, "screened": any(l in BAD for l in labels), "unlabelled": any(l is None for l in labels),
            "labels": ",".join(str(l) for l in labels), "coh_a": coh_by_sha.get(sha(ta), np.nan), "coh_b": coh_by_sha.get(sha(tb), np.nan),
            "words_a": len(ta.split()), "words_b": len(tb.split()),
            "trunc_a": gens.get(f"{uid}::a", {}).get("finish_reason") == "length",
        })
    return pd.DataFrame(rows)


def cell_table(P: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (run, cell), g in P.groupby(["run", "cell"], sort=False):
        k = g[~g.screened & g.outcome.notna()]
        W, L, T = int((k.outcome == "W").sum()), int((k.outcome == "L").sum()), int((k.outcome == "T").sum())
        rows.append({"run": run, "cell": cell, "pairs": len(g), "judged": int(g.outcome.notna().sum()), "screened_out": int(g.screened.sum()), "unlabelled": int(g.unlabelled.sum()),
                     "W": W, "L": L, "T": T, "win_rate": W / (W + L) if W + L else np.nan, "p_vs_0.5": binomtest(W, W + L, 0.5).pvalue if W + L else np.nan,
                     "coh_a": k.coh_a.mean(), "coh_b": k.coh_b.mean(), "words_a": k.words_a.mean(), "words_b": k.words_b.mean(), "trunc_a": k.trunc_a.mean()})
    C = pd.DataFrame(rows)
    C["ref_cell"], C["ref_WL"], C["p_vs_ref"] = "", "", np.nan
    for i, r in C.iterrows():
        same = C[C.run == r.run]
        if r.cell.endswith("_vs_empty") and r.cell != "harmful_vs_empty":
            ref = same[same.cell == "harmful_vs_empty"]
        elif r.cell.startswith("steer_") and "rand" not in r.cell:
            side = r.cell.rsplit("_", 1)[1]
            ref = same[same.cell.str.startswith("steer_rand") & same.cell.str.endswith(side)]
        else:
            ref = same.iloc[0:0]
        if len(ref) and (r.W + r.L) and (ref.iloc[0].W + ref.iloc[0].L):
            q = ref.iloc[0]
            C.loc[i, ["ref_cell", "ref_WL", "p_vs_ref"]] = [q.cell, f"{q.W} / {q.L}", fisher_exact([[r.W, r.L], [q.W, q.L]])[1]]
    return C


def projections(run: str) -> pd.DataFrame:
    f = RUNS / run / "projections.shard0.jsonl"
    if not f.exists():
        return pd.DataFrame()
    P = pd.DataFrame(load(f)).drop_duplicates(["output_id", "layer", "key"])
    # keep the untouched texts only (their own generation rows, not aliased copies in steered or bridge pairs)
    P = P[P.output_id.str.startswith(("harmful_vs_empty:", "effort_vs_neutral:"))].copy()
    P["p"] = P.proj_rmean / P.resid_rms_rmean
    P["run"] = run
    return P


def contrast(P: pd.DataFrame, pos: str, neg: str) -> pd.DataFrame:
    rows = []
    for (k, l), g in P.groupby(["key", "layer"]):
        a, b = g[g.condition == pos].p, g[g.condition == neg].p
        if len(a) < 2 or len(b) < 2:
            continue
        rows.append({"key": k, "layer": l, "n": f"{len(a)}/{len(b)}", "diff": a.mean() - b.mean(), "cohen_d": (a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2),
                     "auc": mannwhitneyu(a, b).statistic / (len(a) * len(b))})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, action="append", default=None)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/steering/w9_analysis")
    args = ap.parse_args()
    rds = args.run_dir or [RUNS / "w9_sandbag_local", RUNS / "w9_sandbag_remote"]
    rds = [rd for rd in rds if (rd / "generations.jsonl").exists()]
    args.out.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 250)
    P = pd.concat([pair_table(rd) for rd in rds], ignore_index=True)
    P.to_csv(args.out / "sandbag_pairs.csv", index=False)
    C = cell_table(P)
    C.to_csv(args.out / "sandbag_cells.csv", index=False)
    print("== A. cells (side a vs side b; refusal-screened pairs dropped)")
    print(C.round(3).to_string(index=False))
    base = P[(P.cell == "harmful_vs_empty") & ~P.screened & P.outcome.notna()]
    if len(base):
        W, L = int((base.outcome == "W").sum()), int((base.outcome == "L").sum())
        print(f"\nharmful vs framed-empty pooled over runs: {W} / {L} = {W / max(W + L, 1):.3f} (paper, Qwen3.5-9B grant: 51 / 128 = 0.285)")
        lab = P[P.cell == "harmful_vs_empty"].labels.value_counts()
        print("refusal labels of the untouched harmful texts:", lab.to_dict())

    Q = pd.concat([projections(rd.name) for rd in rds], ignore_index=True) if rds else pd.DataFrame()
    if len(Q):
        S = contrast(Q, "harmful", "framed_empty")
        E = contrast(Q, "effort", "neutral")
        S.to_csv(args.out / "sandbag_proj_harmful_vs_empty.csv", index=False)
        print("\n== B1. untouched harmful minus framed-empty, projection onto unit vectors (fraction of residual RMS)")
        print(S.round(4).to_string(index=False))
        if len(E):
            E.to_csv(args.out / "sandbag_proj_effort_vs_neutral.csv", index=False)
            M = S.merge(E, on=["key", "layer"], suffixes=("_sandbag", "_exh"))
            M["sandbag_over_exh"] = M.diff_sandbag / M.diff_exh
            M.to_csv(args.out / "sandbag_proj_vs_effort.csv", index=False)
            print("\n== B2. the same shift next to the exhortation shift (max-effort minus neutral, grant)")
            print(M[["key", "layer", "diff_sandbag", "cohen_d_sandbag", "auc_sandbag", "diff_exh", "cohen_d_exh", "auc_exh", "sandbag_over_exh"]].round(4).to_string(index=False))
        # within untouched harmful vs empty pairs: E projection of the harmful text, pairs won vs lost by the harmful side
        H = Q[(Q.condition == "harmful")].copy()
        H["pair_uid"] = H.output_id.str.rsplit("::", n=1).str[0]
        H = H.merge(P[["run", "pair_uid", "outcome", "screened"]], on=["run", "pair_uid"])
        H = H[~H.screened & H.outcome.isin(["W", "L"])]
        rows = []
        for (k, l), g in H.groupby(["key", "layer"]):
            a, b = g[g.outcome == "W"].p, g[g.outcome == "L"].p
            if len(a) >= 3 and len(b) >= 3:
                rows.append({"key": k, "layer": l, "n_W/n_L": f"{len(a)}/{len(b)}", "mean_W": a.mean(), "mean_L": b.mean(), "auc_W_over_L": mannwhitneyu(a, b).statistic / (len(a) * len(b)), "p": mannwhitneyu(a, b).pvalue})
        if rows:
            W = pd.DataFrame(rows)
            W.to_csv(args.out / "sandbag_proj_within_harmful.csv", index=False)
            print("\n== B3. harmful texts: projection for pairs the harmful side won vs lost")
            print(W.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
