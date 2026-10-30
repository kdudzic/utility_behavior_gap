#!/usr/bin/env bash
# Week-7 GPU chain, run ON THE INSTANCE inside one tmux session (started from the laptop with
#   vast ssh "cd /workspace/utility_behavior_gap && tmux new-session -d -s w7 'bash steering_extension/vast/w7_chain.sh'").
# Steps, each through run_shards.sh (which merges shards and writes outputs/steering/logs/<name>.log):
#   1. extract the effort vector from essay responses (contrasts_essay_v1.jsonl -> vectors/qwen3.5-9b_essay_v1)
#   2. build the grant cross-validation manifest from that vector (week7_crossval.sh)
#   3. generate the four week-7 runs: random controls, role cues, necessity test, cross-validation on grant
# Writes outputs/steering/logs/w7_all.done at the end; a failed step stops the chain (set -e) and leaves no marker.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export STEER_USE_KERNELS=1 HF_HOME="${HF_HOME:-/workspace/.hf_cache}" NUM_SHARDS=1 GPUS_PER_SHARD=1
mkdir -p outputs/steering/logs
L=outputs/steering/logs

JOB_NAME=w7_extract bash steering_extension/vast/run_shards.sh steering_extension.steer.extract \
  --contrasts outputs/steering/contrasts/contrasts_essay_v1.jsonl --out-dir outputs/steering/vectors/qwen3.5-9b_essay_v1 \
  --batch-size 24 --max-new-tokens 300 --n-random 2 > $L/w7_extract.log 2>&1

bash steering_extension/local/week7_crossval.sh outputs/steering/vectors/qwen3.5-9b_essay_v1/vectors.safetensors > $L/w7_crossval_manifest.log 2>&1

for R in w7_random w7_role w7_necessity w7_crossval_grant; do
  JOB_NAME=$R bash steering_extension/vast/run_shards.sh steering_extension.steer.generate \
    --manifest outputs/steering/runs/$R/generation_jobs.jsonl --batch-size 32 > $L/$R.log 2>&1
done
date -Is > $L/w7_all.done
