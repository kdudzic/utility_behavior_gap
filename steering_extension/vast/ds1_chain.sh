#!/usr/bin/env bash
# DS1 to DS5: DeepSeek V3.2 white-box sandbagging study (week9_plan.txt), run ON THE INSTANCE inside tmux so the
# laptop can disconnect:
#   vast ssh "cd /workspace/utility_behavior_gap && tmux new-session -d -s ds1 'bash steering_extension/vast/ds1_chain.sh'"
# Needs on the instance: the repo, runs/ds_base_essay and runs/ds_base_grant manifests and
# contrasts/contrasts_ds_v1.jsonl (all built on the laptop by local/week9_ds_cells.sh base).
# Steps (each logs start, exit code and duration to logs/ds1_chain.log):
#   0. ds0_chain.sh with its own stop disabled: environment, FP8 preflight, 690 GB download, smoke test (the gate)
#   1. base_essay  generate runs/ds_base_essay: harmful vs framed-empty (paper 0.10) and max-effort vs neutral
#   2. base_grant  generate runs/ds_base_grant: harmful vs framed-empty (paper 0.31)
#   3. extract     E (max-effort vs neutral, grant items) and S (harmful vs framed-empty, essay items), 150 per arm,
#                  300 new tokens -> vectors/deepseek-v3.2_v1 (+ split-half and held-out AUC by layer)
#   4. cells       week9_ds_cells.sh steer: S_perp, manifest runs/ds_steer
#   5. project     untouched texts of both base runs onto E, S, S_perp, rand0 at 9 layers
#   6. steer       generate runs/ds_steer (14 cells x 60 pairs on essays, layers 12 / 20 / 30)
# Steps 1 and 2 do not depend on each other; 4 to 6 need step 3. A failed step does not stop the independent ones.
# Marker: logs/ds1.DONE when every step succeeded, else logs/ds1.FAILED listing the failed steps.
# The instance stops itself afterwards (GPU billing ends, disk kept): after a grace period of DS1_GRACE_MIN minutes
# (default 30) that ends early when the laptop touches logs/ds1.pulled, and after DS1_MAX_HOURS (default 7) from the
# start at the latest. DS1_NO_STOP=1 leaves it running. A stopped instance still bills its disk: `vast down` after
# the pull.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
REPO="$PWD"
L=outputs/steering/logs
mkdir -p "$L"
LOG="$L/ds1_chain.log"
MAX_HOURS="${DS1_MAX_HOURS:-7}"
MODEL="${DS1_MODEL:-deepseek-ai/DeepSeek-V3.2}"
VDIR=outputs/steering/vectors/deepseek-v3.2_v1
PROJ_LAYERS="${DS1_PROJ_LAYERS:-6,12,16,20,24,30,36,42,48}"

export PATH="$HOME/.local/bin:$PATH"
export HF_HOME="${HF_HOME:-/workspace/.hf_cache}" TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONPATH="$REPO:$REPO/src:${PYTHONPATH:-}"
export STEER_USE_KERNELS=0 STEER_MODEL="$MODEL" STEER_MAX_MEMORY_GIB="${STEER_MAX_MEMORY_GIB:-86}"
export NUM_SHARDS=1 GPUS_PER_SHARD="$(nvidia-smi -L | wc -l)"
PY="$REPO/.venv/bin/python"

log() { echo "$(date -Is) $*" >> "$LOG"; }

stop_instance() {
  [[ "${DS1_NO_STOP:-0}" == "1" ]] && { log "DS1_NO_STOP=1: instance left running"; return; }
  if [[ -z "${CONTAINER_ID:-}" || -z "${CONTAINER_API_KEY:-}" ]]; then
    eval "$(tr '\0' '\n' < /proc/1/environ | grep -E '^(CONTAINER_ID|CONTAINER_API_KEY)=' | sed 's/^/export /')" || true
  fi
  log "stopping instance ${CONTAINER_ID:-unknown} ($1)"
  sync
  for attempt in 1 2 3; do
    code=$(curl -s -m 60 -o /dev/null -w '%{http_code}' -X PUT "https://console.vast.ai/api/v0/instances/${CONTAINER_ID}/" \
      -H "Authorization: Bearer ${CONTAINER_API_KEY}" -H "Content-Type: application/json" -d '{"state": "stopped"}')
    log "stop request attempt $attempt: http $code"
    [[ "$code" == "200" ]] && break
    sleep 20
  done
}

( sleep "$(( MAX_HOURS * 3600 ))"; echo "$(date -Is) hard time limit of ${MAX_HOURS} h reached" >> "$L/ds1.FAILED"; stop_instance "hard limit" ) &
WATCHDOG=$!
log "DS1 chain start: model=$MODEL max_hours=$MAX_HOURS gpus=$GPUS_PER_SHARD cap=${STEER_MAX_MEMORY_GIB}GiB"

FAILED=()
step() {  # step <name> <command...>
  local name="$1"; shift
  local t0; t0=$(date +%s)
  log "---- step $name: start"
  if "$@" >> "$L/ds1_$name.log" 2>&1; then
    log "---- step $name: ok after $(( ( $(date +%s) - t0 ) / 60 )) min"; return 0
  fi
  log "---- step $name: FAILED after $(( ( $(date +%s) - t0 ) / 60 )) min; see $L/ds1_$name.log"
  FAILED+=("$name"); return 1
}

gate() {
  # run the smoke-test chain only when it has not passed on this instance yet
  [[ -f "$L/ds0.DONE" ]] && return 0
  DS0_NO_STOP=1 bash steering_extension/vast/ds0_chain.sh
  [[ -f "$L/ds0.DONE" ]]
}
gen() {  # gen <run> <batch>
  JOB_NAME="$1" bash steering_extension/vast/run_shards.sh steering_extension.steer.generate \
    --manifest "outputs/steering/runs/$1/generation_jobs.jsonl" --batch-size "$2"
}
extract() {
  "$PY" -m steering_extension.steer.extract --contrasts outputs/steering/contrasts/contrasts_ds_v1.jsonl --out-dir "$VDIR" \
    --batch-size "${DS1_EXTRACT_BATCH:-32}" --max-new-tokens 300 --shard 0 --num-shards 1 &&
  OMP_NUM_THREADS=32 "$PY" -m steering_extension.steer.extract --merge --out-dir "$VDIR" --n-random 2 --n-splits 5 --k-folds 3
}
project() {
  local r
  for r in ds_base_essay ds_base_grant; do
    JOB_NAME="ds1_proj_$r" bash steering_extension/vast/run_shards.sh steering_extension.steer.project \
      --run-dir "outputs/steering/runs/$r" --conditions harmful,framed_empty,effort,neutral --vectors "$VDIR/vectors.safetensors" \
      --keys E,S,S_perp,rand0 --layers "$PROJ_LAYERS" --batch-size "${DS1_PROJ_BATCH:-4}" || return 1
  done
}

if step gate gate; then
  step base_essay gen ds_base_essay "${DS1_ESSAY_BATCH:-48}"
  step base_grant gen ds_base_grant "${DS1_GRANT_BATCH:-24}"
  if step extract extract && step cells bash steering_extension/local/week9_ds_cells.sh steer; then
    step project project
    step steer gen ds_steer "${DS1_ESSAY_BATCH:-48}"
  fi
fi

if [[ ${#FAILED[@]} -eq 0 ]]; then date -Is > "$L/ds1.DONE"; log "DONE"; else echo "$(date -Is) failed steps: ${FAILED[*]}" > "$L/ds1.FAILED"; log "FAILED: ${FAILED[*]}"; fi
kill "$WATCHDOG" 2>/dev/null || true
if [[ "${DS1_NO_STOP:-0}" != "1" ]]; then
  log "waiting up to ${DS1_GRACE_MIN:-30} min for the laptop to pull (touch $L/ds1.pulled to stop now)"
  for ((i=0; i<${DS1_GRACE_MIN:-30}*6; i++)); do [[ -f "$L/ds1.pulled" ]] && break; sleep 10; done
fi
stop_instance "chain finished"
