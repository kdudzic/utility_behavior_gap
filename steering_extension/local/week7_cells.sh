#!/usr/bin/env bash
# Build the week-7 manifests (week7_plan.txt items 5-8) from the v4 vectors. Essay task, 30 items x 2 repeats.
# Item 6 (cross-validation on grant) needs the essay-built vector first; see week7_crossval.sh.
# Usage: bash steering_extension/local/week7_cells.sh [v4_vectors.safetensors]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export PYTHONPATH="$PWD:$PWD/src"
V4="${1:-outputs/steering/vectors/qwen3.5-9b_v4/vectors.safetensors}"
PY=.venv/bin/python

# item 5: random controls on the sweep grid (two norm-matched random directions)
CELLS=()
for K in rand0 rand1; do for L in 6 10 14 20; do for r in -0.1 0.05 0.1; do CELLS+=(--cell "$K:$L:$r"); done; done; done
$PY -m steering_extension.local.make_steering_jobs --vectors "$V4" --run-name w7_random --task essay --items 30 --repeats 2 "${CELLS[@]}"

# item 7: role cues (world-class / skilled): E ablated at layers 8-16, and E added at layer 6 r=+0.1, each vs the untouched role essay;
# plus the paper's role contrast (world-class vs skilled, both untouched) as a bridge
$PY -m steering_extension.local.make_role_jobs --vectors "$V4" --run-name w7_role --items 30 --repeats 2 --ablate-layers 8,10,12,14,16 --add-layer 6 --add-r 0.1 --bridge

# item 8: clean necessity test: max-effort prompt with E (or rand0) ablated at layers 8-16, vs the neutral-prompt essay untouched
$PY -m steering_extension.local.make_ablation_jobs --vectors "$V4" --run-name w7_necessity --items 30 --repeats 2 --keys E,rand0 --layers 8,10,12,14,16 --cells vs_neutral --neutral-all-keys

# item 6, step 1: extraction prompts for the essay-built effort vector (30 essay items x 10 repeats = 300 responses per arm)
$PY -m steering_extension.local.make_contrast_set --tasks essay --items-per-task 30 --repeats 10 --contrasts E --out outputs/steering/contrasts/contrasts_essay_v1.jsonl

for R in w7_random w7_role w7_necessity; do
  printf '%-14s %5d pairs\n' "$R" "$(wc -l < outputs/steering/runs/$R/generation_jobs.jsonl)"
done
