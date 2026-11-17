#!/usr/bin/env bash
# Week-9 GPU chain (sandbagging and the effort direction, Qwen3.5-9B, grant), run ON THE INSTANCE inside tmux so
# the laptop can disconnect:
#   vast ssh "cd /workspace/utility_behavior_gap && tmux new-session -d -s w9 'bash steering_extension/vast/w9_chain.sh'"
# Steps:
#   1. generate runs/w9_sandbag_local (built on the laptop): harmful vs framed-empty, E added under harmful, bridges,
#      max-effort vs neutral reference
#   2. extract the sandbagging vector S (harmful minus framed-empty) -> vectors/qwen3.5-9b_sandbag_v1
#   3. week9_cells.sh remote: add E and S_perp to that file, build runs/w9_sandbag_remote
#   4. generate runs/w9_sandbag_remote
#   5. projections of the untouched harmful / framed-empty / max-effort / neutral texts onto E, S, S_perp, rand0
# Writes outputs/steering/logs/w9_all.done on success or w9_all.failed on failure. In both cases, and after
# W9_MAX_HOURS at the latest, the instance stops itself (CONTAINER_ID / CONTAINER_API_KEY), so nothing keeps
# billing for GPU time while nobody is watching (after a grace period of W9_GRACE_MIN minutes, default 30, that
# ends early when the laptop touches logs/w9.pulled). Disk is kept; pull the results after `vastai start instance`
# or directly if the instance is still up. Set W9_NO_STOP=1 to keep the instance running.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export STEER_USE_KERNELS=0 HF_HOME="${HF_HOME:-/workspace/.hf_cache}" NUM_SHARDS=1 GPUS_PER_SHARD=1
mkdir -p outputs/steering/logs
L=outputs/steering/logs
MAX_HOURS="${W9_MAX_HOURS:-8}"

stop_instance() {
  [[ "${W9_NO_STOP:-0}" == "1" ]] && { echo "W9_NO_STOP=1, instance left running"; return; }
  if [[ -z "${CONTAINER_ID:-}" || -z "${CONTAINER_API_KEY:-}" ]]; then
    # tmux may not inherit the container environment; read it from PID 1
    eval "$(tr '\0' '\n' < /proc/1/environ | grep -E '^(CONTAINER_ID|CONTAINER_API_KEY)=' | sed 's/^/export /')" || true
  fi
  echo "$(date -Is) stopping instance ${CONTAINER_ID:-unknown}"
  sync
  curl -s -m 60 -X PUT "https://console.vast.ai/api/v0/instances/${CONTAINER_ID}/" \
    -H "Authorization: Bearer ${CONTAINER_API_KEY}" -H "Content-Type: application/json" -d '{"state": "stopped"}' \
    | head -c 300 || echo "stop request failed"
  echo
}

( sleep "$(( MAX_HOURS * 3600 ))"; echo "$(date -Is) hard time limit of ${MAX_HOURS} h reached" >> $L/w9_all.failed; stop_instance >> $L/w9_stop.log 2>&1 ) &
WATCHDOG=$!

run_chain() {
  set -e
  JOB_NAME=w9_sandbag_local bash steering_extension/vast/run_shards.sh steering_extension.steer.generate \
    --manifest outputs/steering/runs/w9_sandbag_local/generation_jobs.jsonl --batch-size 24 > $L/w9_sandbag_local.log 2>&1

  JOB_NAME=w9_extract bash steering_extension/vast/run_shards.sh steering_extension.steer.extract \
    --contrasts outputs/steering/contrasts/contrasts_sandbag_v1.jsonl --out-dir outputs/steering/vectors/qwen3.5-9b_sandbag_v1 \
    --batch-size 24 --max-new-tokens 300 --n-random 2 > $L/w9_extract.log 2>&1

  bash steering_extension/local/week9_cells.sh remote > $L/w9_cells_remote.log 2>&1

  JOB_NAME=w9_sandbag_remote bash steering_extension/vast/run_shards.sh steering_extension.steer.generate \
    --manifest outputs/steering/runs/w9_sandbag_remote/generation_jobs.jsonl --batch-size 24 > $L/w9_sandbag_remote.log 2>&1

  VEC=outputs/steering/vectors/qwen3.5-9b_sandbag_v1/vectors.safetensors
  LAYERS=4,6,8,10,12,14,16,18,20
  for R in w9_sandbag_local w9_sandbag_remote; do
    JOB_NAME=w9_proj_$R bash steering_extension/vast/run_shards.sh steering_extension.steer.project \
      --run-dir outputs/steering/runs/$R --conditions harmful,framed_empty,effort,neutral --vectors "$VEC" \
      --keys E,S,S_perp,rand0 --layers "$LAYERS" --batch-size 8 > $L/w9_proj_$R.log 2>&1
  done
}

if ( run_chain ); then date -Is > $L/w9_all.done; else echo "$(date -Is) chain failed; see $L/w9_*.log" > $L/w9_all.failed; fi
kill "$WATCHDOG" 2>/dev/null || true
# grace period: give a connected laptop up to W9_GRACE_MIN minutes to pull (it touches $L/w9.pulled), then stop
for ((i=0; i<${W9_GRACE_MIN:-30}*6; i++)); do [[ -f $L/w9.pulled ]] && break; sleep 10; done
stop_instance > $L/w9_stop.log 2>&1
