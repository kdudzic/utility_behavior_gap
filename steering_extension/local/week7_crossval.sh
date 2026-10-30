#!/usr/bin/env bash
# Week-7 item 6, step 2: cross-validation manifest. The effort vector built from ESSAY responses
# (outputs/steering/vectors/qwen3.5-9b_essay_v1/vectors.safetensors, from extract.py on contrasts_essay_v1.jsonl)
# is tested on the GRANT task: layers 6, 10, 16 x r -0.1, +0.05, +0.1, plus rand0 at layer 10 at the same doses.
# 30 grant items x 2 repeats = 60 pairs per cell, 12 cells + baseline = 720 pairs, max_tokens 1400 (paper's grant cap).
# Runs on the laptop or on the instance (needs only numpy + safetensors). Usage: bash steering_extension/local/week7_crossval.sh [vectors.safetensors]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export PYTHONPATH="$PWD:$PWD/src"
VE="${1:-outputs/steering/vectors/qwen3.5-9b_essay_v1/vectors.safetensors}"
CELLS=()
for L in 6 10 16; do for r in -0.1 0.05 0.1; do CELLS+=(--cell "E:$L:$r"); done; done
for r in -0.1 0.05 0.1; do CELLS+=(--cell "rand0:10:$r"); done
.venv/bin/python -m steering_extension.local.make_steering_jobs --vectors "$VE" --run-name w7_crossval_grant --task grant_proposal_abstract --items 30 --repeats 2 --max-tokens 1400 "${CELLS[@]}"
printf 'w7_crossval_grant %5d pairs\n' "$(wc -l < outputs/steering/runs/w7_crossval_grant/generation_jobs.jsonl)"
