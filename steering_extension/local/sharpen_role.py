"""Week 8 follow-up, idea 2: a role vector from the responses where the cue took (Persona Vectors style filtering).

Input: an extraction directory with per-response activations (perresp.shard0.safetensors, readout "rmean", shape
[layers, N, d]) and the response texts (responses.shard0.jsonl), e.g. vectors/qwen3.5-9b_essay_role_v1 (R_id on
essays: world-class vs skilled, 300 per arm, responses cut at 300 tokens).

Step 1 (paid, resumable): one judge (claude-haiku-4.5, temperature 0) scores every response 0 to 100 for how much it
reads like the work of a world-class essayist rather than a merely competent one. Writes <out>/scores.jsonl.
Step 2 (offline): pair pos and neg responses by cid (same topic and repeat); keep the quarter of pairs with the
largest score gap (pos minus neg); R_sharp = mean(pos activations) - mean(neg activations) over those pairs, per
layer. Also R_sharp_perp (E component from --e-vectors projected out). Reports split-half cosine over pairs
(20 random splits), cosine with E and with the unfiltered R_id, and writes <out>/vectors.safetensors with
R_sharp, R_sharp_perp and the E and norm/layer keys copied from --e-vectors (so make_steering_jobs doses are on
the same scale as every other cell).
Run: .venv/bin/python -m steering_extension.local.sharpen_role --src outputs/steering/vectors/qwen3.5-9b_essay_role_v1 \
       --e-vectors outputs/steering/vectors/qwen3.5-9b_v4_role/vectors.safetensors --out outputs/steering/vectors/qwen3.5-9b_role_sharp
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from safetensors import safe_open
from safetensors.numpy import load_file, save_file

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

JUDGE = "anthropic/claude-haiku-4.5"
PROMPT = """You are rating the craft level of an essay fragment for a research audit. The text may be cut off mid-sentence; ignore that.

Score from 0 to 100 how much this reads like the work of a world-class essayist rather than a merely competent one:
- 90-100: exceptional craft: precise, original, controlled prose; arguments with real depth; striking but apt examples.
- 60-80: clearly competent, well organised, but conventional in thought and phrasing.
- 30-50: adequate but flat: generic claims, formulaic structure, stock phrasing.
- 0-20: weak: muddled, repetitive, or clumsy.

Judge craft only. Do not reward length or agreement with the position taken.

Essay prompt:
<prompt>
{prompt}
</prompt>

Essay fragment:
<response>
{response}
</response>

Reply with only an integer from 0 to 100."""


def score_all(src: Path, out: Path, workers: int) -> dict[int, int]:
    from utility_behavior_gap.openrouter import OpenRouterClient, response_text
    from steering_extension.local.keys import load_keys

    load_keys()
    rows = [json.loads(l) for l in (src / "responses.shard0.jsonl").open()]
    path = out / "scores.jsonl"
    done = {json.loads(l)["idx"]: json.loads(l)["score"] for l in path.open()} if path.exists() else {}
    todo = [(i, r) for i, r in enumerate(rows) if i not in done]
    print(f"scoring {len(todo)} responses ({len(done)} done)")
    client = OpenRouterClient(timeout_s=120, max_retries=3)

    def one(i, r):
        text = PROMPT.format(prompt=r["prompt"], response=r["response"])
        resp = client.chat_completion(model=JUDGE, messages=[{"role": "user", "content": text}], temperature=0.0, max_tokens=8, reasoning={"effort": "minimal", "exclude": True})
        raw = response_text(resp).strip()
        m = re.search(r"\d{1,3}", raw)
        return {"idx": i, "cid": r["cid"], "contrast": r["contrast"], "arm": r["arm"], "score": int(m.group()) if m else None, "raw": raw, "cost": (resp.get("usage") or {}).get("cost")}

    with ThreadPoolExecutor(max_workers=workers) as ex, path.open("a") as f:
        futs = [ex.submit(one, i, r) for i, r in todo]
        for k, fut in enumerate(as_completed(futs), 1):
            rec = fut.result()
            f.write(json.dumps(rec) + "\n")
            f.flush()
            if rec["score"] is not None:
                done[rec["idx"]] = rec["score"]
            if k % 100 == 0:
                print(f"  {k}/{len(todo)}", flush=True)
    return done


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--e-vectors", type=Path, required=True, help="safetensors with E/layer<l> and norm/layer<l> (v4)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--contrast", default="R_id")
    ap.add_argument("--quantile", type=float, default=0.25, help="share of pairs kept (largest score gap)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--no-judge", action="store_true", help="use existing scores only")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    scores = {json.loads(l)["idx"]: json.loads(l)["score"] for l in (args.out / "scores.jsonl").open()} if (args.out / "scores.jsonl").exists() and args.no_judge else score_all(args.src, args.out, args.workers)
    meta = json.loads((args.src / "perresp.shard0.json").read_text())["rows"]
    pos = {m["cid"]: i for i, m in enumerate(meta) if m["contrast"] == args.contrast and m["arm"] == "pos"}
    neg = {m["cid"]: i for i, m in enumerate(meta) if m["contrast"] == args.contrast and m["arm"] == "neg"}
    pairs = [(c, pos[c], neg[c]) for c in pos if c in neg and scores.get(pos[c]) is not None and scores.get(neg[c]) is not None]
    gaps = np.array([scores[p] - scores[n] for _, p, n in pairs])
    sp = np.array([scores[p] for _, p, n in pairs]); sn = np.array([scores[n] for _, p, n in pairs])
    print(f"{len(pairs)} pairs; score pos mean {sp.mean():.1f} (sd {sp.std():.1f}), neg mean {sn.mean():.1f} (sd {sn.std():.1f}); gap mean {gaps.mean():+.1f}, share gap > 0: {(gaps > 0).mean():.2f}")
    k = max(10, int(round(args.quantile * len(pairs))))
    keep = np.argsort(-gaps)[:k]
    print(f"keeping {k} pairs with gap >= {gaps[keep].min():+d} (mean gap {gaps[keep].mean():+.1f})")
    with safe_open(str(args.src / "perresp.shard0.safetensors"), "np") as f:
        X = f.get_tensor("rmean").astype(np.float32)  # (L, N, d)
    L = X.shape[0]
    ip = np.array([pairs[i][1] for i in keep]); ineg = np.array([pairs[i][2] for i in keep])
    vec = X[:, ip].mean(1) - X[:, ineg].mean(1)  # (L, d)
    full = X[:, [p for _, p, _ in pairs]].mean(1) - X[:, [n for _, _, n in pairs]].mean(1)
    rng = np.random.default_rng(args.seed)
    sh = np.zeros((20, L))
    for s in range(20):
        perm = rng.permutation(len(keep)); a_, b_ = keep[perm[: len(keep) // 2]], keep[perm[len(keep) // 2 :]]
        va = X[:, [pairs[i][1] for i in a_]].mean(1) - X[:, [pairs[i][2] for i in a_]].mean(1)
        vb = X[:, [pairs[i][1] for i in b_]].mean(1) - X[:, [pairs[i][2] for i in b_]].mean(1)
        sh[s] = (va * vb).sum(1) / (np.linalg.norm(va, axis=1) * np.linalg.norm(vb, axis=1) + 1e-8)
    ev = load_file(str(args.e_vectors))
    out = {k_: v for k_, v in ev.items() if k_.startswith("norm/") or k_.startswith("E/")}
    print(" layer  split_half  cos(E)  cos(R_id full)  |v|/|full|")
    for l in range(L):
        e = ev[f"E/layer{l}"].astype(np.float64); u = e / np.linalg.norm(e)
        v = vec[l].astype(np.float64)
        perp = v - (v @ u) * u
        out[f"R_sharp/layer{l}"] = v.astype(np.float32); out[f"R_sharp_perp/layer{l}"] = perp.astype(np.float32)
        cf = float(v @ full[l] / (np.linalg.norm(v) * np.linalg.norm(full[l]) + 1e-8))
        if l % 2 == 0:
            print(f" {l:5d}  {sh[:, l].mean():+.3f}     {v @ u / np.linalg.norm(v):+.2f}   {cf:+.2f}          {np.linalg.norm(v) / np.linalg.norm(full[l]):.2f}")
    save_file(out, str(args.out / "vectors.safetensors"))
    json.dump({"src": str(args.src), "pairs": len(pairs), "kept": int(k), "min_gap_kept": int(gaps[keep].min()), "split_half_by_layer": [round(float(x), 4) for x in sh.mean(0)], "judge": JUDGE}, (args.out / "report.json").open("w"), indent=1)
    print(f"wrote {args.out / 'vectors.safetensors'}")


if __name__ == "__main__":
    main()
