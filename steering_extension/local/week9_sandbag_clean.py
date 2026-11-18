"""Week 9: is the near-zero cosine between Qwen's sandbagging vector S and the effort vector E an effect of the
refusals among the extraction responses?

S (vectors/qwen3.5-9b_sandbag_v1) is the mean response-token residual of 300 harmful-prompt responses minus 300
framed-empty responses, refusals and objection texts included. This script labels the 300 harmful-prompt extraction
responses with the paper's refusal classifier (paid, about $0.11, resumable; labels in
<vectors dir>/refusal_labels.jsonl) and rebuilds the vector from subsets of the harmful arm, from the stored
per-response activations (no GPU):

  S_all     all harmful responses minus framed-empty (must reproduce S)
  S_clean   clean harmful responses minus framed-empty
  S_nonclean  refusals and objection texts minus framed-empty

Per layer: cosine with E, the shift along unit E as a fraction of the residual RMS (comparable with the readout
tables of week9_sandbag.py), the size relative to the residual RMS, cosine with S, and the split-half cosine.

  python -m steering_extension.local.week9_sandbag_clean [--no-classify]
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from safetensors import safe_open

from steering_extension.local.common import ROOT

VDIR = ROOT / "outputs" / "steering" / "vectors" / "qwen3.5-9b_sandbag_v1"
OUT = ROOT / "outputs" / "steering" / "w9_analysis"
LAYERS = [4, 6, 8, 10, 12, 14, 16, 18, 20]
BAD = {"full_refusal", "partial_refusal", "degenerate"}


def label_responses(responses: list[dict], path: Path) -> dict[str, str]:
    from utility_behavior_gap.openrouter import OpenRouterClient
    from steering_extension.local.keys import load_keys
    from steering_extension.local.sandbag_refusals import classify

    done = {}
    if path.exists():
        done = {r["cid"]: r for r in map(json.loads, path.open()) if r.get("label") != "parse_error"}
    todo = [r for r in responses if r["arm"] == "pos" and r["cid"] not in done]
    if todo:
        load_keys()
        client = OpenRouterClient()
        units = [{"cid": r["cid"], "task": "grant_proposal_abstract", "text": r["response"]} for r in todo]
        with ThreadPoolExecutor(8) as ex, path.open("a") as f:
            for rec in ex.map(lambda u: classify(client, u), units):
                f.write(json.dumps(rec) + "\n")
                done[rec["cid"]] = rec
    return {c: r["label"] for c, r in done.items()}


def cos(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.nn.functional.cosine_similarity(a, b, dim=0))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-classify", action="store_true", help="use existing labels only (no paid calls)")
    args = ap.parse_args()
    responses = [json.loads(l) for l in (VDIR / "responses.shard0.jsonl").open()]
    lab_path = VDIR / "refusal_labels.jsonl"
    if args.no_classify:
        labels = {r["cid"]: r["label"] for r in map(json.loads, lab_path.open())}
    else:
        labels = label_responses(responses, lab_path)
    rows = json.loads((VDIR / "perresp.shard0.json").read_text())["rows"]
    arm = np.array([r["arm"] for r in rows])
    lab = np.array([labels.get(r["cid"], "") if r["arm"] == "pos" else "" for r in rows])
    neg = arm == "neg"
    clean = (arm == "pos") & (lab == "clean")
    nonclean = (arm == "pos") & np.isin(lab, list(BAD))
    print("harmful extraction responses by label:", pd.Series(lab[arm == "pos"]).value_counts().to_dict())

    acts = safe_open(VDIR / "perresp.shard0.safetensors", "pt")
    vecs = safe_open(VDIR / "vectors.safetensors", "pt")
    rng = np.random.default_rng(0)
    half = rng.permutation(len(rows)) % 2 == 0
    out = []
    for layer in LAYERS:
        X = acts.get_slice("rmean")[layer].float()  # (N, d)
        E, S = vecs.get_tensor(f"E/layer{layer}").float(), vecs.get_tensor(f"S/layer{layer}").float()
        rms = float(vecs.get_tensor(f"norm/layer{layer}")[0])
        u = E / E.norm()
        base = X[torch.from_numpy(neg)].mean(0)
        for name, mask in [("S_all", arm == "pos"), ("S_clean", clean), ("S_nonclean", nonclean)]:
            v = X[torch.from_numpy(mask)].mean(0) - base
            h = [X[torch.from_numpy(mask & m)].mean(0) - X[torch.from_numpy(neg & m)].mean(0) for m in (half, ~half)]
            out.append({"vector": name, "layer": layer, "n_harmful": int(mask.sum()), "cos_E": cos(v, E), "shift_along_E_over_rms": float(v @ u) / rms,
                        "size_over_rms": float(v.norm()) / rms, "cos_S": cos(v, S), "split_half_cos": cos(h[0], h[1])})
    T = pd.DataFrame(out)
    T.to_csv(OUT / "sandbag_clean_vector.csv", index=False)
    text = "\n\n".join(f"== {n}\n" + g.drop(columns="vector").round(4).to_string(index=False) for n, g in T.groupby("vector", sort=False))
    (OUT / "sandbag_clean_vector.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
