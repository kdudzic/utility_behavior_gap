#!/bin/bash
#SBATCH --job-name=steer
#SBATCH --account=plgllmpsypath-gpu-a100
#SBATCH --partition=plgrid-gpu-a100
#SBATCH --cpus-per-task=8
#SBATCH --mem=60G
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --output=outputs/steering/slurm/%x-%A_%a.out
# Usage: sbatch [--array=0-3] steering_extension/slurm/gpu_job.sbatch <python module args...>
# Inside an array, SLURM_ARRAY_TASK_ID / SLURM_ARRAY_TASK_COUNT are forwarded as --shard/--num-shards.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$PWD}"
export HF_HOME="${HF_HOME:-$SCRATCH/.caches/hf}"
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
SHARD_ARGS=""
if [ -n "${SLURM_ARRAY_TASK_ID:-}" ]; then
  SHARD_ARGS="--shard ${SLURM_ARRAY_TASK_ID} --num-shards ${SLURM_ARRAY_TASK_COUNT}"
fi
echo "node=$(hostname) gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader) args=$* $SHARD_ARGS"
exec .venv/bin/python -m "$@" $SHARD_ARGS
