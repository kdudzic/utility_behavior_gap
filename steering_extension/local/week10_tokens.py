"""Week 10 (18.11 todo item 2): the "broken tokens" the coherence judge names in unsteered essays. What are they and
how often do they occur? Offline.

Scans every generated text of every run in outputs/steering/runs (one count per distinct text; aliased sides are
skipped) for words in another script inside English text: CJK, kana, Hangul, Cyrillic, Arabic, Hebrew, Indic scripts,
Thai, Greek, Vietnamese letters, and the Unicode replacement character. Groups texts by model, task, prompt condition and steering
(unsteered, E added or removed, random direction, other vectors) and |r|.

Then checks the coherence judge's explanations (coherence_pairwise.py, w9_analysis/pairwise_*.jsonl): for the
explanations the coder labelled broken_tokens, does a quoted passage or the lower-rated essay contain such a word?

  python -m steering_extension.local.week10_tokens   # writes outputs/steering/w10_analysis/tokens_*.{csv,txt}
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

from steering_extension.local.common import ROOT

RUNS = ROOT / "outputs" / "steering" / "runs"
W9 = ROOT / "outputs" / "steering" / "w9_analysis"
OUT = ROOT / "outputs" / "steering" / "w10_analysis"
SCRIPTS = {
    "CJK": r"㐀-䶿一-鿿豈-﫿",
    "kana": r"぀-ヿ",
    "Hangul": r"가-힯ᄀ-ᇿ",
    "Cyrillic": r"Ѐ-ӿ",
    "Arabic": r"؀-ۿ",
    "Hebrew": r"֐-׿",
    "Indic": r"ऀ-෿",
    "Thai": r"฀-๿",
    "Greek": r"Ͱ-Ͽ",
    "Vietnamese": r"Ḁ-ỿ",
    "replacement": r"�",
}
ANY = re.compile("[" + "".join(SCRIPTS.values()) + "]+")
PER = {k: re.compile("[" + v + "]") for k, v in SCRIPTS.items()}


def load(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open()] if p.exists() else []


def steer_group(st: dict | None) -> tuple[str, float]:
    if not st:
        return "unsteered", 0.0
    key, r = str(st.get("key", "?")), float(st.get("r", 0.0))
    if key == "E":
        return ("E added" if r > 0 else "E removed"), abs(r)
    if key.startswith("rand"):
        return ("random added" if r > 0 else "random removed"), abs(r)
    return f"{key} {'added' if r > 0 else 'removed'}", abs(r)


def scan_texts() -> pd.DataFrame:
    rows = []
    for rd in sorted(p for p in RUNS.iterdir() if (p / "generations.jsonl").exists()):
        seen = set()
        for g in load(rd / "generations.jsonl"):
            if g.get("alias_of") or not g.get("success", True):
                continue
            text = g.get("output_text") or ""
            if not text.strip() or text in seen:
                continue
            seen.add(text)
            st = (g.get("provider") or {}).get("steering")
            group, r = steer_group(st)
            spans = ANY.findall(text)
            task = g["output_id"].split(":")[1] if g["output_id"].count(":") >= 2 else ""
            rows.append({"run": rd.name, "model": "DeepSeek V3.2" if "deepseek" in str(g.get("actor", "")) else "Qwen3.5-9B",
                         "task": task, "condition": g.get("condition", ""), "steering": group, "abs_r": r,
                         "layer": (st or {}).get("layer", -1), "words": len(text.split()), "n_spans": len(spans),
                         "has_foreign": bool(spans), "scripts": ",".join(k for k, p in PER.items() if p.search(text)),
                         "spans": " | ".join(spans[:6]), "output_id": g["output_id"],
                         "example": "" if not spans else text[max(0, text.find(spans[0]) - 50): text.find(spans[0]) + len(spans[0]) + 30].replace("\n", " ")})
    return pd.DataFrame(rows)


def judge_check() -> pd.DataFrame:
    """For each coherence-judge explanation coded broken_tokens: does a quoted passage contain a foreign-script word,
    and does the essay it rated lower contain one at all?"""
    judged = load(W9 / "pairwise_coherence.jsonl")
    codes = {c["key"]: c for c in load(W9 / "pairwise_reason_codes.jsonl") if c.get("success")}
    texts = {}
    for run in {j["run"] for j in judged}:
        gens = load(RUNS / run / "generations.jsonl")
        for g in gens:
            texts[g["output_id"]] = g.get("output_text") or ""
        for g in gens:
            if g.get("alias_of"):
                texts[g["output_id"]] = texts.get(g["alias_of"], texts[g["output_id"]])
    rows = []
    for j in judged:
        if not j.get("success") or j.get("more_coherent") not in ("A", "B"):
            continue
        c = codes.get(f"{j['run']}:{j['pair_uid']}")
        if c is None:
            continue
        cats = c[f"codes_order{j['order']}"]
        lower_side = j["B_side"] if j["more_coherent"] == "A" else j["A_side"]
        lower_text = texts.get(f"{j['pair_uid']}::{lower_side}", "")
        rows.append({"stratum": j["stratum"], "pair_uid": j["pair_uid"], "order": j["order"], "broken_tokens": "broken_tokens" in cats,
                     "lower_is_steered": lower_side == "a", "quote_has_foreign": any(ANY.search(p or "") for p in j.get("passages") or []),
                     "lower_text_has_foreign": bool(ANY.search(lower_text)), "passages": " | ".join((j.get("passages") or [])[:3])[:300]})
    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    T = scan_texts()
    T.to_csv(OUT / "tokens_texts.csv", index=False)
    lines = ["== A. share of texts with a word in another script, by model, task and steering (distinct texts)"]
    A = T.groupby(["model", "task", "steering"]).agg(texts=("has_foreign", "size"), with_foreign=("has_foreign", "sum"), share=("has_foreign", "mean"),
                                                    spans_per_affected_text=("n_spans", lambda s: s[s > 0].mean())).reset_index()
    A.to_csv(OUT / "tokens_by_group.csv", index=False)
    lines.append(A.round(3).to_string(index=False))
    lines.append("\n== B. Qwen, by steering and |r| (all tasks)")
    q = T[T.model == "Qwen3.5-9B"]
    B = q.groupby(["steering", "abs_r"]).agg(texts=("has_foreign", "size"), share=("has_foreign", "mean")).reset_index()
    B.to_csv(OUT / "tokens_by_dose.csv", index=False)
    lines.append(B.round(3).to_string(index=False))
    lines.append("\n== C. Qwen unsteered texts, by run and prompt condition")
    C = q[q.steering == "unsteered"].groupby(["run", "task", "condition"]).agg(texts=("has_foreign", "size"), share=("has_foreign", "mean")).reset_index()
    lines.append(C.round(3).to_string(index=False))
    sc = Counter(s for x in q[q.has_foreign].scripts for s in x.split(",") if s)
    lines.append(f"\n== D. scripts in affected Qwen texts (texts containing each): {dict(sc.most_common())}")
    un = q[(q.steering == "unsteered") & q.has_foreign]
    lines.append(f"\n== E. examples, Qwen unsteered ({len(un)} texts)")
    lines += [f"  [{r.task}] ...{r.example}..." for r in un.sample(min(25, len(un)), random_state=0).itertuples()]
    J = judge_check()
    J.to_csv(OUT / "tokens_judge_check.csv", index=False)
    if not J.empty:
        lines.append("\n== F. coherence judge explanations, by stratum: coded broken_tokens, and whether a foreign-script word is in the quote / in the essay rated lower")
        F = J.groupby("stratum").agg(explanations=("broken_tokens", "size"), coded_broken=("broken_tokens", "sum")).reset_index()
        bt = J[J.broken_tokens]
        F = F.merge(bt.groupby("stratum").agg(quote_has_foreign=("quote_has_foreign", "mean"), lower_text_has_foreign=("lower_text_has_foreign", "mean")).reset_index(), on="stratum", how="left")
        lines.append(F.round(2).to_string(index=False))
        nf = bt[~bt.lower_text_has_foreign]
        lines.append(f"\nbroken_tokens explanations whose lower-rated essay has no foreign-script word: {len(nf)} of {len(bt)}; their quotes:")
        lines += [f"  [{r.stratum}] {r.passages}" for r in nf.head(15).itertuples()]
    lines.append("\n== G. unsteered Qwen texts: our local generation (top_p 1.0, top_k 0) against OpenRouter with the paper's settings")
    from scipy.stats import fisher_exact
    T["source"] = ["OpenRouter" if r.startswith("w10_or_") else "local" for r in T.run]
    u = T[(T.model == "Qwen3.5-9B") & (T.steering == "unsteered") & T.task.isin(["essay", "grant_proposal_abstract"])]
    G = u.groupby(["task", "source"]).agg(texts=("has_foreign", "size"), with_foreign=("has_foreign", "sum"), share=("has_foreign", "mean")).reset_index()
    lines.append(G.round(3).to_string(index=False))
    for task, g in u.groupby("task"):
        a = g[g.source == "local"].has_foreign
        b = g[g.source == "OpenRouter"].has_foreign
        if len(b):
            p = fisher_exact([[int(a.sum()), int((~a).sum())], [int(b.sum()), int((~b).sum())]])[1]
            lines.append(f"  {task}: local {a.mean():.3f} against OpenRouter {b.mean():.3f}, Fisher p = {p:.3f}")
    text = "\n".join(lines)
    (OUT / "tokens_tables.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
