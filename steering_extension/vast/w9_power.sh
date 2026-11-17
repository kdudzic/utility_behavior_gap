#!/usr/bin/env bash
# Week-9 top-up, run ON THE INSTANCE in its own tmux session while w9_chain.sh is still running:
#   tmux new-session -d -s w9p 'bash steering_extension/vast/w9_power.sh'
# Waits for w9_chain.sh to finish (logs/w9_all.done or w9_all.failed), then ends that chain's own stop timer so
# the instance stays up, generates runs/w9_sandbag_power (8 more repeats of harmful vs framed-empty and of the
# layer-10 effort and random cells, built on the laptop), projects its untouched texts, and then stops the
# instance itself: after a grace period of W9_GRACE_MIN minutes (default 30) that ends early when the laptop
# touches logs/w9p.pulled, and after W9P_MAX_HOURS (default 6) at the latest.
# Writes logs/w9_power.done or logs/w9_power.failed.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export STEER_USE_KERNELS=0 HF_HOME="${HF_HOME:-/workspace/.hf_cache}" NUM_SHARDS=1 GPUS_PER_SHARD=1
L=outputs/steering/logs
MAX_HOURS="${W9P_MAX_HOURS:-6}"

stop_instance() {
  if [[ -z "${CONTAINER_ID:-}" || -z "${CONTAINER_API_KEY:-}" ]]; then
    eval "$(tr '\0' '\n' < /proc/1/environ | grep -E '^(CONTAINER_ID|CONTAINER_API_KEY)=' | sed 's/^/export /')" || true
  fi
  echo "$(date -Is) stopping instance ${CONTAINER_ID:-unknown}"
  sync
  curl -s -m 60 -X PUT "https://console.vast.ai/api/v0/instances/${CONTAINER_ID}/" \
    -H "Authorization: Bearer ${CONTAINER_API_KEY}" -H "Content-Type: application/json" -d '{"state": "stopped"}' \
    | head -c 300 || echo "stop request failed"
  echo
}

( sleep "$(( MAX_HOURS * 3600 ))"; echo "$(date -Is) hard time limit of ${MAX_HOURS} h reached" >> $L/w9_power.failed; stop_instance >> $L/w9p_stop.log 2>&1 ) &
WATCHDOG=$!

# 1. wait for the main chain, then take over its stop
until [[ -f $L/w9_all.done || -f $L/w9_all.failed ]]; do sleep 20; done
echo "$(date -Is) main chain finished: $(ls $L/w9_all.* | tr '\n' ' ')" > $L/w9_power.log
# end the main chain's grace loop and watchdog (bash processes only; the tmux server also carries the script
# name in its command line and must stay alive, it hosts this session too). This script now owns the stop.
pkill -f '^bash steering_extension/vast/w9_chain\.sh' || true
sleep 2

run_power() {
  set -e
  JOB_NAME=w9_sandbag_power bash steering_extension/vast/run_shards.sh steering_extension.steer.generate \
    --manifest outputs/steering/runs/w9_sandbag_power/generation_jobs.jsonl --batch-size 24 >> $L/w9_power.log 2>&1
  VEC=outputs/steering/vectors/qwen3.5-9b_sandbag_v1/vectors.safetensors
  if [[ -f $VEC ]]; then
    JOB_NAME=w9_proj_w9_sandbag_power bash steering_extension/vast/run_shards.sh steering_extension.steer.project \
      --run-dir outputs/steering/runs/w9_sandbag_power --conditions harmful,framed_empty --vectors "$VEC" \
      --keys E,S,S_perp,rand0 --layers 4,6,8,10,12,14,16,18,20 --batch-size 8 >> $L/w9_power.log 2>&1
  fi
}

if ( run_power ); then date -Is > $L/w9_power.done; else echo "$(date -Is) top-up failed; see $L/w9_power.log" > $L/w9_power.failed; fi
kill "$WATCHDOG" 2>/dev/null || true
for ((i=0; i<${W9_GRACE_MIN:-30}*6; i++)); do [[ -f $L/w9p.pulled ]] && break; sleep 10; done
stop_instance > $L/w9p_stop.log 2>&1
