"""Week 10 (18.11 todo item 2c): where in Qwen's next-token distribution do the foreign-script words come from?

Teacher-forces prompt + response through the model, without steering, at temperature 1.0 (plain softmax of the
logits), and records for every response token its probability, its rank (0 = most likely), and the probability mass
of all more likely tokens. From these:
  - in top-k 20      rank < 20
  - in nucleus p     mass of more likely tokens < p (the token survives top-p sampling at p)
For each text: number of tokens, how many fall outside top-k 20 and outside the 0.8 / 0.95 nuclei, and the same
numbers for the tokens that decode to a word in another script (CJK, Cyrillic, ... as in local/week10_tokens.py).

Two uses: (1) our local texts (sampled with top_p 1.0, top_k 0): are the foreign words tail samples that top-k or
top-p would have removed? (2) texts generated through OpenRouter with the paper's settings: if the provider truncates
the distribution, none of their tokens should lie outside the cut.

Input: run dirs (generation_jobs.jsonl + generations.jsonl); only unsteered texts unless --all; --conditions filters.
Output: --out jsonl, one row per text. Resumable. Prints the model's generation_config once.

  python -m steering_extension.steer.token_probs --run-dir outputs/steering/runs/w6_sweep --out outputs/steering/w10_token_probs/w6_sweep.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import torch

from steering_extension.steer.generate import append_jsonl, read_jsonl
from steering_extension.steer.model import chat_input_ids, load_model

FOREIGN = re.compile("[㐀-䶿一-鿿豈-﫿぀-ヿ가-힯ᄀ-ᇿЀ-ӿ֐-ۿ"
                     "ऀ-෿฀-๿Ͱ-ϿḀ-ỿ�]")


def items_from_run(rd: Path, conditions: set[str] | None, include_steered: bool) -> list[dict]:
    jobs = {j["pair_uid"]: j for j in read_jsonl(rd / "generation_jobs.jsonl")}
    out, seen = [], set()
    for g in read_jsonl(rd / "generations.jsonl"):
        text = g.get("output_text") or ""
        if g.get("alias_of") or not text.strip() or text in seen:
            continue
        if (g.get("provider") or {}).get("steering") and not include_steered:
            continue
        if conditions and g.get("condition") not in conditions:
            continue
        seen.add(text)
        side = g["output_id"].rsplit("::", 1)[1]
        job = jobs[g["pair_uid"]]
        out.append({"run": rd.name, "output_id": g["output_id"], "condition": g.get("condition", ""), "task": job.get("task", ""),
                    "system_prompt": job.get(f"system_prompt_{side}", ""), "prompt": job[f"prompt_{side}"], "response": text})
    return out


@torch.inference_mode()
def score(loaded, it: dict) -> dict:
    tok = loaded.tokenizer
    p = chat_input_ids(loaded, it.get("system_prompt", ""), it["prompt"])
    r = tok(it["response"], add_special_tokens=False)["input_ids"]
    ids = torch.tensor([p + r], device=loaded.device)
    logits = loaded.model(input_ids=ids).logits[0, len(p) - 1 : len(p) + len(r) - 1].float()
    lp = torch.log_softmax(logits, dim=-1)
    tgt = torch.tensor(r, device=lp.device)
    chosen = lp.gather(1, tgt[:, None])[:, 0]
    higher = lp > chosen[:, None]
    rank = higher.sum(1)
    mass_above = (lp.exp() * higher).sum(1)
    prob = chosen.exp()
    pieces = [tok.decode([t]) for t in r]
    foreign = [i for i, s in enumerate(pieces) if FOREIGN.search(s)]
    rank_c, mass_c, prob_c = rank.cpu(), mass_above.cpu(), prob.cpu()

    def counts(idx: list[int] | None) -> dict:
        rk = rank_c if idx is None else rank_c[idx]
        ms = mass_c if idx is None else mass_c[idx]
        return {"n": int(rk.numel()), "out_top20": int((rk >= 20).sum()), "out_p95": int((ms >= 0.95).sum()), "out_p80": int((ms >= 0.80).sum())}

    return {"run": it["run"], "output_id": it["output_id"], "condition": it["condition"], "task": it["task"],
            "all": counts(None), "foreign": counts(foreign) if foreign else {"n": 0, "out_top20": 0, "out_p95": 0, "out_p80": 0},
            "foreign_tokens": [{"pos": i, "piece": pieces[i], "prob": round(float(prob_c[i]), 6), "rank": int(rank_c[i]),
                                "mass_above": round(float(mass_c[i]), 4)} for i in foreign[:20]],
            "min_prob": round(float(prob_c.min()), 8) if len(r) else None}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, action="append", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--conditions", default=None)
    ap.add_argument("--all", action="store_true", help="include steered texts")
    ap.add_argument("--limit", type=int, default=None, help="at most N texts per run dir")
    ap.add_argument("--model", default=os.environ.get("STEER_MODEL", "Qwen/Qwen3.5-9B"))
    args = ap.parse_args()
    conds = set(args.conditions.split(",")) if args.conditions else None
    items = []
    for rd in args.run_dir:
        its = items_from_run(rd, conds, args.all)
        items += its[: args.limit] if args.limit else its
    done = {r["output_id"] + "|" + r["run"] for r in read_jsonl(args.out)} if args.out.exists() else set()
    items = [it for it in items if it["output_id"] + "|" + it["run"] not in done]
    print(f"{len(items)} texts to score -> {args.out}", flush=True)
    if not items:
        return
    loaded = load_model(args.model)
    print("generation_config:", json.dumps(loaded.model.generation_config.to_dict(), default=str), flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for i, it in enumerate(items, 1):
        append_jsonl(args.out, [score(loaded, it)])
        if i % 50 == 0 or i == len(items):
            print(f"{i}/{len(items)}", flush=True)


if __name__ == "__main__":
    main()
