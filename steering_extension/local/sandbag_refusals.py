"""Refusal screen for the week-9 sandbagging runs, with the paper's classifier unchanged.

Reuses CLASSIFY_TEMPLATE, TASK_ARTIFACT, parse_label and CLASSIFIER_MODEL from
utility_behavior_gap.scripts.classify_moral_refusals (the paper's audit of the moral condition). Every distinct
output text written under a harmful-cause prompt (untouched or steered) is labelled clean / partial_refusal /
full_refusal / degenerate. Texts written under the framed-empty prompt carry no cause and are not screened, as in the
paper's harmful vs framed-empty comparison. Resumable; writes <run_dir>/refusal_labels.jsonl keyed by the sha256 of
the output text, so aliased copies of a text share one label.
Paid API call (openai/gpt-5-mini through OpenRouter): run only with the PI's authorization.

Usage: .venv/bin/python -m steering_extension.local.sandbag_refusals --run-dir outputs/steering/runs/w9_sandbag_local
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from utility_behavior_gap.openrouter import OpenRouterClient, response_text  # noqa: E402
from utility_behavior_gap.scripts.classify_moral_refusals import CLASSIFIER_MODEL, CLASSIFY_TEMPLATE, TASK_ARTIFACT, parse_label  # noqa: E402
from steering_extension.local.keys import load_keys  # noqa: E402

ARTIFACT = {"grant_proposal_abstract": TASK_ARTIFACT["grant"], "incident_postmortem": TASK_ARTIFACT["incident"], "essay": TASK_ARTIFACT["essay"]}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def classify(client: OpenRouterClient, unit: dict) -> dict:
    text = unit.pop("text")
    if not text.strip():
        return {**unit, "label": "degenerate", "evidence": "empty output", "classifier": "rule:empty"}
    prompt = CLASSIFY_TEMPLATE.format(artifact=ARTIFACT[unit["task"]], output=text[:12000])
    resp = client.chat_completion(model=CLASSIFIER_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.0, max_tokens=150, reasoning={"effort": "minimal", "exclude": True})
    obj = parse_label(response_text(resp))
    if obj is None:
        return {**unit, "label": "parse_error", "evidence": response_text(resp)[:200], "classifier": CLASSIFIER_MODEL}
    return {**unit, "label": obj["label"], "evidence": str(obj.get("evidence", ""))[:200], "classifier": CLASSIFIER_MODEL, "usage": resp.get("usage", {})}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    jobs = {j["pair_uid"]: j for j in (json.loads(l) for l in (args.run_dir / "generation_jobs.jsonl").open())}
    out = args.run_dir / "refusal_labels.jsonl"
    done = set()
    if out.exists():
        done = {r["text_sha"] for r in (json.loads(l) for l in out.open()) if r.get("label") != "parse_error"}
    units, seen = [], set()
    for g in (json.loads(l) for l in (args.run_dir / "generations.jsonl").open()):
        if "harmful" not in g["condition"]:
            continue  # only texts written under a prompt that names the harmful cause
        h = sha(g.get("output_text") or "")
        if h in done or h in seen:
            continue
        seen.add(h)
        units.append({"text_sha": h, "output_id": g["output_id"], "condition": g["condition"], "task": jobs[g["pair_uid"]]["task"], "text": g.get("output_text") or ""})
    if args.limit:
        units = units[: args.limit]
    print(f"{len(done)} already labelled; {len(units)} to classify with {CLASSIFIER_MODEL}", flush=True)
    if not units:
        return
    load_keys()
    client = OpenRouterClient(timeout_s=120.0, max_retries=3)
    counts: dict[str, int] = {}
    with out.open("a") as fh, ThreadPoolExecutor(args.workers) as ex:
        futs = {ex.submit(classify, client, u): u["output_id"] for u in units}
        for n, f in enumerate(as_completed(futs), 1):
            try:
                row = f.result()
            except Exception as e:  # noqa: BLE001
                print(f"fail {futs[f]}: {e}", file=sys.stderr)
                continue
            counts[row["label"]] = counts.get(row["label"], 0) + 1
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 50 == 0:
                print(n, counts, flush=True)
    print("labels:", counts)


if __name__ == "__main__":
    main()
