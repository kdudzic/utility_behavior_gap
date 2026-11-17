"""Week 9, plan item 2: pairwise coherence explanations (why is the steered essay rated less coherent?).

The absolute coherence scorer (coherence_judge.py, anthropic/claude-haiku-4.5) gives one integer per essay. Here the
same model, at temperature 0 and with the same coherence definition and score bands (taken verbatim from
coherence_judge.PROMPT), sees the task prompt and two essays labelled A and B (condition hidden) and returns JSON:
which would score higher, how many points apart, reasons, and up to three quoted passages from the lower one.
Every pair is judged in both orders (order 0: A = side a, the steered / intervened essay; order 1: A = side b).

Strata (essay task, pairs with both absolute coherence scores, seeded sample):
  a. effort added (0 < r <= 0.1, w6_sweep, all layers), steered won, coh_a - coh_b < -3: all
  b. effort added, layers 6-14, steered lost, gap < -3: 60
  c. effort added, layers 6-14, steered won, |gap| <= 3: 60
  d. random direction added (r > 0, w6_sweep + w7_random), gap < -3: 60
  e. null cells (steer_baseline, unsteered vs unsteered, w6_sweep + w7_random): 60
  f. effort removed, r = -0.1, layers 6-14: 60

Subcommands (all write to --out, default outputs/steering/w9_analysis):
  sample    pairwise_sample.csv
  judge     pairwise_coherence.jsonl   one record per (pair, order); resumable; --limit N for a smoke test
  code      pairwise_reason_codes.jsonl  one google/gemini-2.5-flash call per pair, multi-label reason categories
  analyze   item2_summary.md, stratum_a_cases.md, stratum_b_cases.md, pairwise_pairs.csv
Paid API calls (judge, code): run only with the PI's authorization. --max-cost stops new calls once this run's spend
(from response usage.cost) passes the cap.
Run: .venv/bin/python -m steering_extension.local.coherence_pairwise judge --workers 8
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from utility_behavior_gap.openrouter import OpenRouterClient, response_text  # noqa: E402
from steering_extension.local.coherence_judge import JUDGE, PROMPT as ABS_PROMPT  # noqa: E402
from steering_extension.local.keys import load_keys  # noqa: E402

RUNS = ROOT / "outputs/steering/runs"
CODER = "google/gemini-2.5-flash"
SEED = 20261117
N_PER = 60
STRATA = {
    "a": "effort added, steered won, steered less coherent by > 3 (all layers)",
    "b": "effort added, layers 6-14, steered lost, steered less coherent by > 3",
    "c": "effort added, layers 6-14, steered won, coherence within 3",
    "d": "random direction added, steered less coherent by > 3",
    "e": "null: unsteered vs unsteered",
    "f": "effort removed, r -0.1, layers 6-14",
}
CATS = ["broken_tokens", "invented_specifics", "overblown_style", "drift_off_topic", "repetition", "register_shift", "truncation", "structure", "none"]

# Definition and score bands, verbatim from the absolute scorer (everything before its "Task prompt" block).
DEFINITION = ABS_PROMPT.split("Task prompt given to the model:")[0].rstrip()
PAIR_PROMPT = DEFINITION + """

Below are one task prompt and two responses to it, labelled A and B. Each response would be scored separately on the scale above. Decide which response would get the higher coherence score and by about how many points, and explain why the lower one would score lower.

Task prompt given to the model:
<prompt>
{prompt}
</prompt>

<response_A>
{a}
</response_A>

<response_B>
{b}
</response_B>

Reply with only a JSON object, no other text:
{{"more_coherent": "A" or "B" or "equal", "points_apart": integer (0 if equal), "reasons": "2-4 sentences on why the lower one would score lower on coherence", "passages": [up to 3 short verbatim quotes from the lower-scoring response that cost it points]}}"""

CODER_PROMPT = """A judge compared two essays for coherence (fluent, grammatical, on-topic, internally consistent text) and explained why the lower-scoring essay would score lower, quoting passages from it. The same pair was judged twice, with the essays shown in the two possible orders. Below are the two explanations.

Assign each explanation every category that it actually names as a problem of the lower-scoring essay (multi-label):
- broken_tokens: garbled or malformed words, typos that look like corrupted text, fragments in the wrong language or script
- invented_specifics: fabricated or implausible numbers, names, studies, quotations, facts
- overblown_style: purple or inflated prose, strained or mixed metaphor, grandiose wording
- drift_off_topic: leaves the topic or the task, tangents, content that does not belong
- repetition: repeats words, phrases, or points
- register_shift: one essay is plain/simple and the other elaborate, or the tone/register changes inside the essay
- truncation: the text is cut off or ends unfinished
- structure: organization, paragraphing, transitions, logical flow between parts
- none: the explanation names no concrete problem (for example it says the essays are equal)

Use "none" only alone. Do not add categories the explanation does not mention.

<explanation_1>
verdict: {v0}
reasons: {r0}
quoted passages: {p0}
</explanation_1>

<explanation_2>
verdict: {v1}
reasons: {r1}
quoted passages: {p1}
</explanation_2>

Reply with only a JSON object: {{"explanation_1": [categories], "explanation_2": [categories]}}"""


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open()] if p.exists() else []


def parse_json(raw: str) -> dict | None:
    s = raw.strip()
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j <= i:
        return None
    try:
        d = json.loads(s[i : j + 1])
    except json.JSONDecodeError:
        return None
    return d if isinstance(d, dict) else None


# ---------------------------------------------------------------- sample
def build_sample(seed: int = SEED) -> pd.DataFrame:
    from steering_extension.local import week8_coherence as w

    P = w.load_all()
    P = P[P.coh_a.notna() & P.coh_b.notna()].copy()
    P["gap"] = P.coh_a - P.coh_b
    eff = P[(P.run == "w6_sweep") & (P.type == "effort")]
    add = eff[(eff.r > 0) & (eff.r <= 0.1 + 1e-9)]
    mid = add[add.layer0.between(6, 14)]
    pools = {
        "a": add[(add.outcome == "W") & (add.gap < -3)],
        "b": mid[(mid.outcome == "L") & (mid.gap < -3)],
        "c": mid[(mid.outcome == "W") & (mid.gap.abs() <= 3)],
        "d": P[(P.type == "random") & P.run.isin(["w6_sweep", "w7_random"]) & (P.r > 0) & (P.gap < -3)],
        "e": P[(P.cell == "steer_baseline") & P.run.isin(["w6_sweep", "w7_random"])],
        "f": eff[np.isclose(eff.r, -0.1) & eff.layer0.between(6, 14)],
    }
    frames = []
    for s, pool in pools.items():
        pool = pool.sort_values(["run", "pair_uid"]).reset_index(drop=True)
        idx = list(range(len(pool)))
        random.Random(f"{seed}:{s}").shuffle(idx)  # seeded order; also the reading order of the case files
        take = idx if s == "a" else idx[:N_PER]
        g = pool.iloc[take].copy()
        g.insert(0, "stratum", s)
        g.insert(1, "pool_n", len(pool))
        g.insert(2, "order_in_stratum", range(len(g)))
        frames.append(g)
    S = pd.concat(frames, ignore_index=True)
    S = S.drop(columns=["key"])  # pair_table's vector key; ours is run:pair_uid
    S.insert(0, "key", S.run + ":" + S.pair_uid)
    cols = ["key", "stratum", "pool_n", "order_in_stratum", "run", "pair_uid", "cell", "item", "repeat", "layer0", "r", "outcome", "coh_a", "coh_b", "gap", "words_a", "words_b", "trunc_a"]
    return S[cols]


def attach_texts(S: pd.DataFrame) -> list[dict]:
    rows = []
    for run, g in S.groupby("run"):
        jobs = {j["pair_uid"]: j for j in load_jsonl(RUNS / run / "generation_jobs.jsonl")}
        gens = {x["output_id"]: x for x in load_jsonl(RUNS / run / "generations.jsonl")}
        for r in g.to_dict(orient="records"):
            j = jobs[r["pair_uid"]]
            ida = j.get("alias_a") or f"{r['pair_uid']}::a"
            idb = j.get("alias_b") or f"{r['pair_uid']}::b"
            r.update({"prompt": j["prompt_a"], "text_a": gens[ida]["output_text"], "text_b": gens[idb]["output_text"],
                      "id_a": ida, "id_b": idb, "topic": j.get("item_label", "")})
            rows.append(r)
    return rows


# ---------------------------------------------------------------- judge
class Budget:
    def __init__(self, cap: float) -> None:
        self.cap, self.spent, self.lock = cap, 0.0, threading.Lock()

    def ok(self) -> bool:
        with self.lock:
            return self.spent < self.cap

    def add(self, usage: dict) -> None:
        with self.lock:
            self.spent += float((usage or {}).get("cost") or 0)


def judge_one(client: OpenRouterClient, row: dict, order: int, budget: Budget) -> dict | None:
    if not budget.ok():
        return None
    first, second = ("a", "b") if order == 0 else ("b", "a")
    text = PAIR_PROMPT.format(prompt=row["prompt"], a=row[f"text_{first}"], b=row[f"text_{second}"])
    rec = {"key": row["key"], "stratum": row["stratum"], "run": row["run"], "pair_uid": row["pair_uid"], "order": order,
           "A_side": first, "B_side": second, "judge": JUDGE, "success": False}
    try:
        resp = client.chat_completion(model=JUDGE, messages=[{"role": "user", "content": text}], temperature=0.0, max_tokens=700)
        raw = response_text(resp).strip()
        usage = resp.get("usage", {}) or {}
        budget.add(usage)
        d = parse_json(raw)
        rec.update({"raw": raw, "usage": {k: usage.get(k) for k in ("prompt_tokens", "completion_tokens", "cost")}})
        mc = str((d or {}).get("more_coherent", "")).strip()
        mc = {"a": "A", "b": "B"}.get(mc.lower(), mc.lower())
        if d is not None and mc in ("A", "B", "equal"):
            try:
                pts = abs(int(round(float(d.get("points_apart", 0)))))
            except (TypeError, ValueError):
                pts = None
            passages = d.get("passages") or []
            if isinstance(passages, str):
                passages = [passages]
            rec.update({"success": True, "more_coherent": mc, "points_apart": pts, "reasons": str(d.get("reasons", "")),
                        "passages": [str(p) for p in passages][:3],
                        # canonical: which original side is rated more coherent (a = steered / intervened)
                        "higher_side": "equal" if mc == "equal" else (first if mc == "A" else second)})
    except Exception as e:  # noqa: BLE001
        rec["error"] = str(e)[:300]
    return rec


def run_pool(fn, todo: list, path: Path, workers: int, budget: Budget, label: str) -> None:
    n_ok = n_fail = n_skip = 0
    with ThreadPoolExecutor(workers) as ex, path.open("a") as fh:
        futs = [ex.submit(fn, *t) for t in todo]
        for i, f in enumerate(as_completed(futs), 1):
            rec = f.result()
            if rec is None:
                n_skip += 1
                continue
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            n_ok += rec["success"]
            n_fail += not rec["success"]
            if i % 50 == 0 or i == len(futs):
                print(f"  {label} {i}/{len(futs)}: ok {n_ok}, failed {n_fail}, cost this run ${budget.spent:.3f}", flush=True)
    print(f"{label} done: ok {n_ok}, failed {n_fail}, skipped by budget cap {n_skip}, cost this run ${budget.spent:.4f}")


def cmd_judge(args) -> None:
    S = sample_or_build(args)
    rows = attach_texts(S)
    path = args.out / "pairwise_coherence.jsonl"
    done = {(r["key"], r["order"]) for r in load_jsonl(path) if r["success"]}
    todo = [(row, o) for row in rows for o in (0, 1) if (row["key"], o) not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} judge calls to make ({len(done)} already done)")
    if args.dry_run:
        print(PAIR_PROMPT.format(prompt=rows[0]["prompt"], a=rows[0]["text_a"][:300] + " [...]", b=rows[0]["text_b"][:300] + " [...]"))
        return
    load_keys()
    client = OpenRouterClient()
    budget = Budget(args.max_cost)
    run_pool(lambda row, o: judge_one(client, row, o, budget), todo, path, args.workers, budget, "judge")


# ---------------------------------------------------------------- reason coding
def verdict_text(r: dict) -> str:
    if r["more_coherent"] == "equal":
        return "the two essays are equal"
    return f"essay {r['more_coherent']} more coherent by {r['points_apart']} points"


def code_one(client: OpenRouterClient, key: str, stratum: str, r0: dict, r1: dict, budget: Budget) -> dict | None:
    if not budget.ok():
        return None
    text = CODER_PROMPT.format(v0=verdict_text(r0), r0=r0["reasons"], p0=json.dumps(r0["passages"], ensure_ascii=False),
                               v1=verdict_text(r1), r1=r1["reasons"], p1=json.dumps(r1["passages"], ensure_ascii=False))
    rec = {"key": key, "stratum": stratum, "coder": CODER, "success": False}
    try:
        resp = client.chat_completion(model=CODER, messages=[{"role": "user", "content": text}], temperature=0.0, max_tokens=400,
                                      reasoning={"effort": "minimal", "exclude": True})
        raw = response_text(resp).strip()
        usage = resp.get("usage", {}) or {}
        budget.add(usage)
        d = parse_json(raw)
        rec.update({"raw": raw, "usage": {k: usage.get(k) for k in ("prompt_tokens", "completion_tokens", "cost")}})
        if d is not None and isinstance(d.get("explanation_1"), list) and isinstance(d.get("explanation_2"), list):
            def clean(xs: list) -> list[str]:
                xs = [str(x).strip().lower() for x in xs]
                xs = [x for x in xs if x in CATS]
                return [x for x in xs if x != "none"] or ["none"]
            rec.update({"success": True, "codes_order0": clean(d["explanation_1"]), "codes_order1": clean(d["explanation_2"]),
                        "unknown": [str(x) for x in d["explanation_1"] + d["explanation_2"] if str(x).strip().lower() not in CATS]})
    except Exception as e:  # noqa: BLE001
        rec["error"] = str(e)[:300]
    return rec


def cmd_code(args) -> None:
    judged = {}
    for r in load_jsonl(args.out / "pairwise_coherence.jsonl"):
        if r["success"]:
            judged[(r["key"], r["order"])] = r
    path = args.out / "pairwise_reason_codes.jsonl"
    done = {r["key"] for r in load_jsonl(path) if r["success"]}
    keys = sorted({k for k, _ in judged})
    todo = [(k, judged[(k, 0)]["stratum"], judged[(k, 0)], judged[(k, 1)]) for k in keys if (k, 0) in judged and (k, 1) in judged and k not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo)} coding calls to make ({len(done)} already done)")
    load_keys()
    client = OpenRouterClient()
    budget = Budget(args.max_cost)
    run_pool(lambda k, s, r0, r1: code_one(client, k, s, r0, r1, budget), todo, path, args.workers, budget, "code")


# ---------------------------------------------------------------- analysis
def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().strip('"\'. …').lower()


def passage_found(p: str, text: str) -> bool:
    parts = [x for x in re.split(r"\.\.\.|…|\[\.\.\.\]", p) if len(norm(x)) >= 8] or [p]
    t = norm(text)
    return all(norm(x) in t for x in parts)


def pct(x: float) -> str:
    return "n/a" if x != x else f"{100 * x:.0f}%"


def cmd_analyze(args) -> None:
    S = sample_or_build(args)
    rows = {r["key"]: r for r in attach_texts(S)}
    J = {}
    for r in load_jsonl(args.out / "pairwise_coherence.jsonl"):
        if r["success"]:
            J[(r["key"], r["order"])] = r
    C = {r["key"]: r for r in load_jsonl(args.out / "pairwise_reason_codes.jsonl") if r["success"]}
    all_recs = load_jsonl(args.out / "pairwise_coherence.jsonl") + load_jsonl(args.out / "pairwise_reason_codes.jsonl")
    cost_j = sum(float((r.get("usage") or {}).get("cost") or 0) for r in load_jsonl(args.out / "pairwise_coherence.jsonl"))
    cost_c = sum(float((r.get("usage") or {}).get("cost") or 0) for r in load_jsonl(args.out / "pairwise_reason_codes.jsonl"))

    # pair table
    pr = []
    for key, row in rows.items():
        if (key, 0) not in J or (key, 1) not in J:
            continue
        j0, j1 = J[(key, 0)], J[(key, 1)]
        signed = [(1 if j["higher_side"] == "a" else -1 if j["higher_side"] == "b" else 0) * (j["points_apart"] or 0) for j in (j0, j1)]
        if j0["higher_side"] == j1["higher_side"]:
            pair_v = j0["higher_side"]
        else:
            pair_v = "split"
        pr.append({**{k: row[k] for k in ("key", "stratum", "run", "cell", "layer0", "r", "outcome", "coh_a", "coh_b", "gap", "words_a", "words_b")},
                   "v0": j0["higher_side"], "v1": j1["higher_side"], "picked_A_0": j0["more_coherent"], "picked_A_1": j1["more_coherent"],
                   "signed_pts0": signed[0], "signed_pts1": signed[1], "signed_pts_mean": float(np.mean(signed)), "pair_verdict": pair_v,
                   "consistent": j0["higher_side"] == j1["higher_side"]})
    D = pd.DataFrame(pr)
    D.to_csv(args.out / "pairwise_pairs.csv", index=False)

    L: list[str] = []
    L.append("# Week 9 item 2: pairwise coherence explanations\n")
    findings = args.out / "item2_findings.txt"
    if findings.exists():
        L.append("## Findings\n\n" + findings.read_text().strip() + "\n")
    L.append("## Setup\n")
    L.append(f"Judge {JUDGE}, temperature 0, the coherence definition and score bands of the absolute scorer. The judge sees the task prompt and two essays "
             "labelled A and B and does not know which one was steered. Every pair is judged twice, once in each order. "
             f"Reason coder {CODER}, temperature 0, one call per pair. Sample seed {SEED}. "
             "\"Steered\" always means side a of the pair (in the null stratum it is just the first of two unsteered essays). "
             "The gap is the absolute coherence score of the steered essay minus that of its unsteered partner.\n")
    n_calls_j = len(load_jsonl(args.out / "pairwise_coherence.jsonl"))
    n_calls_c = len(load_jsonl(args.out / "pairwise_reason_codes.jsonl"))
    L.append(f"Calls logged: {n_calls_j} judge calls ({len(J)} parsed), {n_calls_c} coder calls ({len(C)} parsed). "
             f"Spend from the responses' usage field: judge ${cost_j:.2f}, coder ${cost_c:.2f}, total ${cost_j + cost_c:.2f}.\n")

    L.append("## Sample\n\n| stratum | definition | pool | sampled | judged in both orders | mean coherence steered / partner |\n|---|---|---|---|---|---|")
    for s, lab in STRATA.items():
        g, d = S[S.stratum == s], D[D.stratum == s]
        L.append(f"| {s} | {lab} | {int(g.pool_n.iloc[0])} | {len(g)} | {len(d)} | {g.coh_a.mean():.1f} / {g.coh_b.mean():.1f} |")
    L.append("")

    # 1. agreement with the sign of the absolute gap, and order consistency
    L.append("## 1. Does the pairwise verdict agree with the absolute scores?\n")
    L.append("Verdict columns count single judgments (two per pair). \"Agrees with gap sign\" uses only pairs whose absolute gap is larger than 3 points in either direction, "
             "and counts a judgment as agreeing when it names the essay with the higher absolute score as more coherent (\"equal\" counts as not agreeing). "
             "\"Both orders agree with gap sign\" is the share of those pairs where both judgments agree with the sign. "
             "\"Orders consistent\" is the share of all pairs in the stratum where the two orders give the same verdict (same essay, or equal both times). "
             "\"Picked A\" is the share of judgments that chose the essay shown first.\n")
    L.append("| stratum | pairs | steered more coherent | partner more coherent | equal | pairs with gap > 3 either way | agrees with gap sign | both orders agree with gap sign | orders consistent | picked A | picked B | mean points apart (signed, steered minus partner) | mean absolute gap |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in list(STRATA) + ["all"]:
        d = D if s == "all" else D[D.stratum == s]
        if not len(d):
            continue
        v = pd.concat([d.v0, d.v1])
        picks = pd.concat([d.picked_A_0, d.picked_A_1])
        big = d[d.gap.abs() > 3]
        want = np.where(big.gap > 0, "a", "b")
        ag0, ag1 = (big.v0.values == want), (big.v1.values == want)
        agree = np.concatenate([ag0, ag1]).mean() if len(big) else float("nan")
        both = (ag0 & ag1).mean() if len(big) else float("nan")
        L.append(f"| {s} | {len(d)} | {pct((v == 'a').mean())} | {pct((v == 'b').mean())} | {pct((v == 'equal').mean())} | {len(big)} | "
                 f"{pct(agree)} | {pct(both)} | {pct(d.consistent.mean())} | {pct((picks == 'A').mean())} | {pct((picks == 'B').mean())} | "
                 f"{d.signed_pts_mean.mean():+.1f} | {d.gap.mean():+.1f} |")
    L.append("")
    from scipy.stats import spearmanr
    rho, p = spearmanr(D.gap, D.signed_pts_mean)
    L.append(f"Across all {len(D)} pairs the Spearman correlation between the absolute gap and the pairwise signed points (mean of the two orders) is {rho:.2f}.\n")
    L.append("Pair-level verdicts (both orders must name the same essay; otherwise the pair is \"split\"):\n")
    L.append("| stratum | pairs | steered more coherent | partner more coherent | equal | split |\n|---|---|---|---|---|---|")
    for s in STRATA:
        d = D[D.stratum == s]
        if len(d):
            L.append(f"| {s} | {len(d)} | " + " | ".join(f"{int((d.pair_verdict == x).sum())} ({pct((d.pair_verdict == x).mean())})" for x in ("a", "b", "equal", "split")) + " |")
    L.append("")

    # passages: are the quotes verbatim, and from which essay
    tot = hit_low = hit_other = 0
    for (key, o), j in J.items():
        if j["higher_side"] == "equal":
            continue
        low = "b" if j["higher_side"] == "a" else "a"
        for p in j["passages"]:
            tot += 1
            if passage_found(p, rows[key][f"text_{low}"]):
                hit_low += 1
            elif passage_found(p, rows[key][f"text_{j['higher_side']}"]):
                hit_other += 1
    if tot:
        L.append(f"Check on the quoted passages: the judge gave {tot} quotes in judgments that named a lower essay. {hit_low} ({pct(hit_low / tot)}) are found word for word in the lower-rated essay, "
                 f"{hit_other} ({pct(hit_other / tot)}) are found only in the higher-rated essay, and {tot - hit_low - hit_other} ({pct((tot - hit_low - hit_other) / tot)}) are not found word for word in either.\n")

    # 2. reason categories
    def rate_table(title: str, note: str, selector, keys: set | None = None) -> None:
        L.append(f"### {title}\n\n{note}\n")
        L.append("| stratum | explanations | " + " | ".join(CATS) + " |\n|---|---|" + "---|" * len(CATS))
        for s in STRATA:
            codes = []
            for key, c in C.items():
                if c["stratum"] != s or (keys is not None and key not in keys):
                    continue
                for o in (0, 1):
                    if (key, o) in J and selector(J[(key, o)]):
                        codes.append(c[f"codes_order{o}"])
            if not codes:
                L.append(f"| {s} | 0 | " + " | ".join("n/a" for _ in CATS) + " |")
                continue
            L.append(f"| {s} | {len(codes)} | " + " | ".join(pct(np.mean([cat in x for x in codes])) for cat in CATS) + " |")
        L.append("")

    L.append("## 2. What the judge points at (reason categories)\n")
    L.append("Each explanation (one per judgment) can get several categories. Rates are the share of explanations that got the category.\n")
    rate_table("Explanations where the steered essay was rated lower", "The reasons and quotes are about the steered essay (side a).", lambda j: j["higher_side"] == "b")
    rate_table("Explanations where the unsteered partner was rated lower", "The reasons and quotes are about the unsteered partner (side b).", lambda j: j["higher_side"] == "a")
    both_low = set(D[D.pair_verdict == "b"].key)
    rate_table("Only pairs where both orders rated the steered essay lower", "These verdicts do not depend on which essay was shown first, so they are the cleanest view of what is wrong with the steered essay. "
               "The explanations column is twice the number of such pairs.", lambda j: True, both_low)
    rate_table("Only pairs where the two orders disagreed (each order preferred the essay shown first or second)", "Here the verdict follows the position, so these reasons are what the judge says when it has no stable preference. "
               "Each explanation is about whichever essay that order rated lower.", lambda j: True, set(D[D.pair_verdict == "split"].key))
    rate_table("All explanations", "Includes \"equal\" verdicts, which mostly get \"none\".", lambda j: True)
    L.append("### Per pair (a category counts if either order's explanation got it)\n")
    L.append("| stratum | pairs coded | " + " | ".join(CATS) + " |\n|---|---|" + "---|" * len(CATS))
    for s in STRATA:
        cs = [set(c["codes_order0"]) | set(c["codes_order1"]) for c in C.values() if c["stratum"] == s]
        if cs:
            L.append(f"| {s} | {len(cs)} | " + " | ".join(pct(np.mean([cat in x for x in cs])) for cat in CATS) + " |")
    L.append("")
    # free check, no judge: essays that contain characters from a non-Latin script (Cyrillic, Arabic, Thai, Japanese, Chinese, Korean)
    nonlat = re.compile(r"[\u0400-\u04ff\u0600-\u06ff\u0e00-\u0e7f\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]")
    L.append("## 3. Check without any judge: essays that contain non-Latin script\n")
    L.append("Share of sampled essays with at least one Cyrillic, Arabic, Thai, Japanese, Chinese or Korean character. Strata a, b and d were selected for a low steered coherence score, so their rates are not rates for all steered essays.\n")
    L.append("| stratum | pairs | steered essay | unsteered partner |\n|---|---|---|---|")
    for s in STRATA:
        rs = [r for r in rows.values() if r["stratum"] == s]
        na, nb = sum(bool(nonlat.search(r["text_a"])) for r in rs), sum(bool(nonlat.search(r["text_b"])) for r in rs)
        L.append(f"| {s} | {len(rs)} | {na} ({pct(na / len(rs))}) | {nb} ({pct(nb / len(rs))}) |")
    L.append("")
    L.append("Files: `pairwise_sample.csv` (sample), `pairwise_coherence.jsonl` (judgments), `pairwise_reason_codes.jsonl` (categories), `pairwise_pairs.csv` (one row per pair), "
             "`stratum_a_cases.md` (all pairs of stratum a), `stratum_b_cases.md` (20 pairs of stratum b).\n")
    (args.out / "item2_summary.md").write_text("\n".join(L))

    # case files
    def cases(s: str, n: int | None, path: Path) -> None:
        g = S[S.stratum == s].sort_values("order_in_stratum")
        if n:
            g = g.head(n)
        out = [f"# Stratum {s}: {STRATA[s]}\n", f"{len(g)} pairs. Order 1 shows the steered essay as A, order 2 shows it as B. Verdicts are translated back to steered / unsteered. "
               "A quote marked [not found] does not appear word for word in the essay the judge rated lower.\n"]
        for i, r in enumerate(g.to_dict(orient="records"), 1):
            row = rows[r["key"]]
            out.append(f"## {s}{i}. layer {r['layer0']}, dose {r['r']:+.3f}, panel outcome for steered: {r['outcome']}")
            out.append(f"Topic: {row['topic']}  \nAbsolute coherence: steered {r['coh_a']:.0f}, unsteered {r['coh_b']:.0f} (gap {r['gap']:+.0f}). Words: steered {r['words_a']}, unsteered {r['words_b']}.  \nPair: `{r['key']}`\n")
            for o in (0, 1):
                j = J.get((r["key"], o))
                if not j:
                    out.append(f"Order {o + 1}: no parsed judgment.\n")
                    continue
                who = {"a": "steered", "b": "unsteered", "equal": "equal"}[j["higher_side"]]
                verdict = "equal" if who == "equal" else f"{who} more coherent by {j['points_apart']} points"
                cats = ", ".join(C[r["key"]][f"codes_order{o}"]) if r["key"] in C else "not coded"
                out.append(f"**Order {o + 1}** (steered shown as {'A' if o == 0 else 'B'}): {verdict}. Categories: {cats}.  \n{j['reasons']}\n")
                low = None if j["higher_side"] == "equal" else ("b" if j["higher_side"] == "a" else "a")
                for p in j["passages"]:
                    flag = "" if low is None or passage_found(p, row[f"text_{low}"]) else " [not found]"
                    out.append(f"> {p.strip()}{flag}\n")
            out.append("")
        path.write_text("\n".join(out))

    cases("a", None, args.out / "stratum_a_cases.md")
    cases("b", 20, args.out / "stratum_b_cases.md")
    print("\n".join(L))
    _ = all_recs


def sample_or_build(args) -> pd.DataFrame:
    p = args.out / "pairwise_sample.csv"
    if p.exists():
        return pd.read_csv(p)
    S = build_sample(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    S.to_csv(p, index=False)
    return S


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sample", "judge", "code", "analyze"])
    ap.add_argument("--out", type=Path, default=ROOT / "outputs/steering/w9_analysis")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None, help="make only the first N calls (smoke test)")
    ap.add_argument("--max-cost", type=float, default=4.0, help="stop new calls once this run's spend passes this many dollars")
    ap.add_argument("--dry-run", action="store_true", help="judge: print the first prompt (texts cut), no API calls")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.cmd == "sample":
        S = sample_or_build(args)
        print(S.groupby("stratum").agg(pool=("pool_n", "first"), n=("key", "size"), coh_a=("coh_a", "mean"), coh_b=("coh_b", "mean"), dup=("key", lambda x: x.duplicated().sum())).round(1).to_string())
        print("pairs:", len(S), "unique keys:", S.key.nunique())
    elif args.cmd == "judge":
        cmd_judge(args)
    elif args.cmd == "code":
        cmd_code(args)
    else:
        cmd_analyze(args)


if __name__ == "__main__":
    main()
