#!/usr/bin/env bash
# Week-10 tail check (2026-11-21), run ON THE INSTANCE inside tmux so the laptop can disconnect:
#   vast ssh "cd /workspace/utility_behavior_gap && tmux new-session -d -s w10t 'bash steering_extension/vast/w10t_chain.sh'"
# Generates runs/w10_tail95 (built on the laptop: the week-6 essay cells E at layers 6 and 14, +0.05 and +0.1, and
# random direction 0 at layers 6 and 14, +0.1, plus unsteered pairs; same prompts and vectors) with a nucleus cut of
# top-p 0.95 instead of the full distribution, then scores the new texts with steer/token_probs.py to confirm the
# cut. Writes logs/w10t.done or logs/w10t.failed; stops the instance after a grace period of W10T_GRACE_MIN minutes
# (default 30, ends early on logs/w10t.pulled) and after W10T_MAX_HOURS (default 3) at the latest.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export STEER_USE_KERNELS=0 HF_HOME="${HF_HOME:-/workspace/.hf_cache}"
L=outputs/steering/logs
mkdir -p "$L"
MAX_HOURS="${W10T_MAX_HOURS:-3}"

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

( sleep "$(( MAX_HOURS * 3600 ))"; echo "$(date -Is) hard time limit of ${MAX_HOURS} h reached" >> $L/w10t.failed; stop_instance >> $L/w10t_stop.log 2>&1 ) &
WATCHDOG=$!

run_all() {
  set -e
  export NUM_SHARDS=1 GPUS_PER_SHARD=1 STEER_TOP_P=0.95
  JOB_NAME=w10_tail95 bash steering_extension/vast/run_shards.sh steering_extension.steer.generate \
    --manifest outputs/steering/runs/w10_tail95/generation_jobs.jsonl --batch-size 32 > $L/w10t.log 2>&1
  .venv/bin/python -m steering_extension.steer.token_probs --run-dir outputs/steering/runs/w10_tail95 --all \
    --out outputs/steering/w10_token_probs/tail95.jsonl >> $L/w10t.log 2>&1
}

if ( run_all ); then date -Is > $L/w10t.done; else echo "$(date -Is) failed; see $L/w10t.log" > $L/w10t.failed; fi
kill "$WATCHDOG" 2>/dev/null || true
for ((i=0; i<${W10T_GRACE_MIN:-30}*6; i++)); do [[ -f $L/w10t.pulled ]] && break; sleep 10; done
stop_instance > $L/w10t_stop.log 2>&1
