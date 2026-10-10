#!/usr/bin/env bash
# vast.ai / plain-GPU-box equivalent of slurm/gpu_job.sbatch: run one shard of a steer module directly.
# Usage: SHARD=0 NUM_SHARDS=1 bash steering_extension/vast/run_gpu.sh steering_extension.steer.generate --manifest ...
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export HF_HOME="${HF_HOME:-$PWD/.hf_cache}"
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
exec .venv/bin/python -m "$@" --shard "${SHARD:-0}" --num-shards "${NUM_SHARDS:-1}"
