#!/usr/bin/env bash
# Run a steer module as NUM_SHARDS parallel processes on one machine, each pinned to
# GPUS_PER_SHARD GPUs via CUDA_VISIBLE_DEVICES, then merge the shard outputs.
# Usage (on the GPU box): NUM_SHARDS=4 GPUS_PER_SHARD=1 bash steering_extension/vast/run_shards.sh \
#          steering_extension.steer.generate --manifest outputs/steering/runs/<run>/generation_jobs.jsonl
# Merge is automatic for generate (--merge <run_dir>) and extract (--merge --out-dir <dir>).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
MODULE="$1"; shift
NUM_SHARDS="${NUM_SHARDS:-1}"
GPUS_PER_SHARD="${GPUS_PER_SHARD:-1}"
export HF_HOME="${HF_HOME:-/workspace/.hf_cache}"
export TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONPATH="$PWD:$PWD/src:${PYTHONPATH:-}"
NAME="${JOB_NAME:-${MODULE##*.}}"
LOGDIR=outputs/steering/logs; mkdir -p "$LOGDIR"
echo "$(date -Is) start $MODULE shards=$NUM_SHARDS gpus/shard=$GPUS_PER_SHARD args: $*"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader || true
pids=()
for ((s=0; s<NUM_SHARDS; s++)); do
  devs=""
  for ((g=0; g<GPUS_PER_SHARD; g++)); do devs="${devs}${devs:+,}$((s*GPUS_PER_SHARD+g))"; done
  CUDA_VISIBLE_DEVICES="$devs" .venv/bin/python -m "$MODULE" "$@" --shard "$s" --num-shards "$NUM_SHARDS" \
    > "$LOGDIR/$NAME.shard$s.log" 2>&1 &
  pids+=($!)
done
fail=0
for p in "${pids[@]}"; do wait "$p" || fail=1; done
if [ "$fail" -ne 0 ]; then echo "$(date -Is) a shard FAILED; see $LOGDIR/$NAME.shard*.log"; exit 1; fi
# merge
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  case "${args[$i]}" in
    --manifest) RUN_DIR="$(dirname "${args[$((i+1))]}")";;
    --out-dir) OUT_DIR="${args[$((i+1))]}";;
  esac
done
if [[ "$MODULE" == *generate ]] && [ -n "${RUN_DIR:-}" ]; then
  .venv/bin/python -m "$MODULE" --merge "$RUN_DIR"
elif [[ "$MODULE" == *extract ]] && [ -n "${OUT_DIR:-}" ]; then
  .venv/bin/python -m "$MODULE" --merge --out-dir "$OUT_DIR"
fi
echo "$(date -Is) done"
