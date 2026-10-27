#!/usr/bin/env bash
# Build every week-6 manifest (plan items 1, 3, 4, 5, 6) from the v4 vectors. Essay task, 30 items x 2 repeats.
# Usage: bash steering_extension/local/week6_cells.sh [v4_vectors.safetensors] [v3_vectors.safetensors]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export PYTHONPATH="$PWD:$PWD/src"
V4="${1:-outputs/steering/vectors/qwen3.5-9b_v4/vectors.safetensors}"
V3="${2:-outputs/steering/vectors/qwen3.5-9b_v3/vectors.safetensors}"
PY=.venv/bin/python
M=steering_extension.local.make_steering_jobs

# item 1: full signed dose grid x every second layer, old (rmean) vector, v4
CELLS=""
for L in 6 8 10 12 14 16 18 20 22 24 26 28; do
  for r in -0.2 -0.1 -0.05 0.025 0.05 0.075 0.1; do CELLS="$CELLS --cell E:$L:$r"; done
done
CELLS="$CELLS --cell rand0:16:-0.1 --cell rand0:16:0.05 --cell rand1:16:-0.1 --cell rand1:16:0.05"
$PY -m $M --vectors "$V4" --run-name w6_sweep --task essay --items 30 --repeats 2 $CELLS

# bridge: the v3 vector at the pilot's cells, so v4 and v3 are compared on the same items and day
$PY -m $M --vectors "$V3" --run-name w6_bridge_v3 --task essay --items 30 --repeats 2 --cell E:16:-0.1 --cell E:16:0.05

# item 3: multi-layer injection (dose split evenly across layers)
$PY -m $M --vectors "$V4" --run-name w6_multilayer --task essay --items 30 --repeats 2 \
  --cell E:12+16+20:-0.1 --cell E:12+16+20:0.05 --cell E:14+16+18:0.05 \
  --cell E:8+10+12+14+16+18+20+22+24:-0.1 --cell E:8+10+12+14+16+18+20+22+24:0.05

# item 6: injection positions at layer 16
$PY -m $M --vectors "$V4" --run-name w6_positions --task essay --items 30 --repeats 2 \
  --cell E:16:-0.1:prompt --cell E:16:0.05:prompt --cell E:16:-0.1:all --cell E:16:0.05:all

# item 5: other pre-response readouts (tail tokens and first generated token) at layer 16, two signed doses
CELLS=""
for K in E_astart E_tail2 E_tail3 E_tail4 E_tail5 E_tail6 E_gen1; do CELLS="$CELLS --cell $K:16:-0.1 --cell $K:16:0.1"; done
$PY -m $M --vectors "$V4" --run-name w6_readouts --task essay --items 30 --repeats 2 $CELLS

# item 4: ablation under the real max-effort prompt (all layers) + a local variant (layers 8-16 only)
$PY -m steering_extension.local.make_ablation_jobs --vectors "$V4" --run-name w6_ablation --items 30 --repeats 2 --keys E,rand0
$PY -m steering_extension.local.make_ablation_jobs --vectors "$V4" --run-name w6_ablation_local --items 30 --repeats 2 --keys E --layers 8,10,12,14,16 --cells vs_effort

for R in w6_sweep w6_bridge_v3 w6_multilayer w6_positions w6_readouts w6_ablation w6_ablation_local; do
  printf '%-18s %5d pairs\n' "$R" "$(wc -l < outputs/steering/runs/$R/generation_jobs.jsonl)"
done
