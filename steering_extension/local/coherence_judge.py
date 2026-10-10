"""Score every output in a run's generations.jsonl for coherence (0-100) with one OpenRouter
judge (Persona Vectors style). Resumable; writes <run_dir>/coherence.jsonl.
Paid API call: run only with the PI's authorization for the phase."""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from utility_behavior_gap.openrouter import OpenRouterClient, response_text  # noqa: E402

JUDGE = "anthropic/claude-haiku-4.5"
PROMPT = """You are evaluating whether a model's response is coherent text, independent of its quality or correctness.

Score the response from 0 to 100:
- 100: fully fluent, grammatical, on-topic, internally consistent text.
- 70-90: minor oddities (slight repetition, a strange phrase) but clearly coherent.
- 40-60: noticeably degraded: repetitive loops, drifting off-topic, garbled passages mixed with normal text.
- 0-30: mostly or entirely incoherent, gibberish, wrong language, or degenerate repetition.

Do not reward or penalize the content's persuasiveness, length, or correctness. Judge only coherence.

Task prompt given to the model:
<prompt>
{prompt}
</prompt>

Model response:
<response>
{response}
</response>

Reply with only an integer from 0 to 100."""


def score_one(client: OpenRouterClient, row: dict, prompt: str) -> dict:
    text = PROMPT.format(prompt=prompt, response=row["output_text"])
    resp = client.chat_completion(model=JUDGE, messages=[{"role": "user", "content": text}], temperature=0.0, max_tokens=8, reasoning={"effort": "minimal", "exclude": True})
    raw = response_text(resp).strip()
    m = re.search(r"\d{1,3}", raw)
    return {"output_id": row["output_id"], "condition": row["condition"], "judge": JUDGE, "raw": raw, "coherence": int(m.group()) if m else None, "usage": resp.get("usage", {})}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--conditions", default=None, help="comma list; default all except aliased duplicates")
    args = ap.parse_args()
    gens = [json.loads(l) for l in (args.run_dir / "generations.jsonl").open()]
    jobs = {j["pair_uid"]: j for j in (json.loads(l) for l in (args.run_dir / "generation_jobs.jsonl").open())}
    out = args.run_dir / "coherence.jsonl"
    done = {json.loads(l)["output_id"] for l in out.open()} if out.exists() else set()
    rows = [g for g in gens if g["output_id"] not in done and not g.get("alias_of")]
    if args.conditions:
        keep = set(args.conditions.split(","))
        rows = [g for g in rows if g["condition"] in keep]
    print(f"{len(rows)} outputs to score", flush=True)
    client = OpenRouterClient()
    with out.open("a") as fh, ThreadPoolExecutor(args.workers) as ex:
        futs = {}
        for g in rows:
            job = jobs[g["pair_uid"]]
            side = g["output_id"].rsplit("::", 1)[1]
            futs[ex.submit(score_one, client, g, job[f"prompt_{side}"])] = g["output_id"]
        n = 0
        for f in as_completed(futs):
            try:
                fh.write(json.dumps(f.result()) + "\n")
                fh.flush()
            except Exception as e:  # noqa: BLE001
                print(f"fail {futs[f]}: {e}", file=sys.stderr)
            n += 1
            if n % 50 == 0:
                print(n, flush=True)


if __name__ == "__main__":
    main()
