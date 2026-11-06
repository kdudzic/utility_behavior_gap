#!/usr/bin/env bash
# Week-8 GPU chain, run ON THE INSTANCE inside one tmux session (started from the laptop with
#   vast ssh "cd /workspace/utility_behavior_gap && tmux new-session -d -s w8 'bash steering_extension/vast/w8_chain.sh'").
# Steps:
#   1. projections (plan 2a): re-encode the untouched world-class / skilled essays (w7_role) and the untouched
#      max-effort / neutral essays (w6_ablation) and record their response-mean projection onto unit E, R_id,
#      R_id_perp and rand0 at layers 4 to 20 -> <run>/projections.shard0.jsonl
#   2. generate w8_role_steer (plan 2b, 2c): R_id and R_id_perp at layer 6 +0.1, layer 10 -0.1, layer 16 -0.1
#   3. extract an essay-built R_id (plan 2d) from contrasts_essay_role_v1.jsonl -> vectors/qwen3.5-9b_essay_role_v1
# Writes outputs/steering/logs/w8_all.done at the end; a failed step stops the chain (set -e) and leaves no marker.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
# STEER_USE_KERNELS=0 since 2026-10-30 (hub kernel kernels-community/fla fails to import under transformers 5.23.dev)
export STEER_USE_KERNELS=0 HF_HOME="${HF_HOME:-/workspace/.hf_cache}" NUM_SHARDS=1 GPUS_PER_SHARD=1
mkdir -p outputs/steering/logs
L=outputs/steering/logs
VEC=outputs/steering/vectors/qwen3.5-9b_v4_role/vectors.safetensors
LAYERS=4,6,8,10,12,14,16,18,20

JOB_NAME=w8_proj_role bash steering_extension/vast/run_shards.sh steering_extension.steer.project \
  --run-dir outputs/steering/runs/w7_role --conditions world_class,skilled --vectors "$VEC" --keys E,R_id,R_id_perp,rand0 --layers "$LAYERS" --batch-size 16 > $L/w8_proj_role.log 2>&1
JOB_NAME=w8_proj_effort bash steering_extension/vast/run_shards.sh steering_extension.steer.project \
  --run-dir outputs/steering/runs/w6_ablation --conditions effort,neutral --vectors "$VEC" --keys E,R_id,R_id_perp,rand0 --layers "$LAYERS" --batch-size 16 > $L/w8_proj_effort.log 2>&1

JOB_NAME=w8_role_steer bash steering_extension/vast/run_shards.sh steering_extension.steer.generate \
  --manifest outputs/steering/runs/w8_role_steer/generation_jobs.jsonl --batch-size 32 > $L/w8_role_steer.log 2>&1

JOB_NAME=w8_extract_role bash steering_extension/vast/run_shards.sh steering_extension.steer.extract \
  --contrasts outputs/steering/contrasts/contrasts_essay_role_v1.jsonl --out-dir outputs/steering/vectors/qwen3.5-9b_essay_role_v1 \
  --batch-size 24 --max-new-tokens 300 --n-random 2 > $L/w8_extract_role.log 2>&1

date -Is > $L/w8_all.done
