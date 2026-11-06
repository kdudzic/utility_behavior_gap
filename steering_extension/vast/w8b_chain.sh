#!/usr/bin/env bash
# Week-8 follow-up GPU chain (role vector ideas 1 to 4), run ON THE INSTANCE inside one tmux session:
#   vast ssh "cd /workspace/utility_behavior_gap && tmux new-session -d -s w8b 'bash steering_extension/vast/w8b_chain.sh'"
# Steps:
#   1. extract R_wide (world-class vs novice paraphrases) and R_content (essayist vs other world-class profession)
#      from contrasts_essay_role_v2.jsonl -> vectors/qwen3.5-9b_essay_role_v2
#   2. week8b_cells.sh remote: add the E-orthogonal versions and build runs/w8b_role_remote
#   3. generate runs/w8b_role_local (R_act, R_act_perp, R_sharp, R_sharp_perp; built on the laptop) and w8b_role_remote
# Writes outputs/steering/logs/w8b_all.done at the end; a failed step stops the chain (set -e) and leaves no marker.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export STEER_USE_KERNELS=0 HF_HOME="${HF_HOME:-/workspace/.hf_cache}" NUM_SHARDS=1 GPUS_PER_SHARD=1
mkdir -p outputs/steering/logs
L=outputs/steering/logs

JOB_NAME=w8b_extract bash steering_extension/vast/run_shards.sh steering_extension.steer.extract \
  --contrasts outputs/steering/contrasts/contrasts_essay_role_v2.jsonl --out-dir outputs/steering/vectors/qwen3.5-9b_essay_role_v2 \
  --batch-size 24 --max-new-tokens 300 --n-random 2 > $L/w8b_extract.log 2>&1

bash steering_extension/local/week8b_cells.sh remote > $L/w8b_cells_remote.log 2>&1

for R in w8b_role_local w8b_role_remote; do
  JOB_NAME=$R bash steering_extension/vast/run_shards.sh steering_extension.steer.generate \
    --manifest outputs/steering/runs/$R/generation_jobs.jsonl --batch-size 32 > $L/$R.log 2>&1
done
date -Is > $L/w8b_all.done
