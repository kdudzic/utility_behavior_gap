#!/usr/bin/env bash
# Week-9 follow-up (2026-11-18), run ON THE INSTANCE inside tmux so the laptop can disconnect:
#   vast ssh "cd /workspace/utility_behavior_gap && tmux new-session -d -s w9l 'bash steering_extension/vast/w9l_chain.sh'"
# Generates runs/w9_sandbag_late (Qwen3.5-9B, grant, repeats 10 to 17, built on the laptop): harmful vs framed-empty,
# the essay-built effort vector and a random direction added under the harmful prompt at layers 16, 18, 20
# (r = +0.05), each also paired with the framed-empty text, and the effort vector under the framed-empty prompt at
# layers 18 and 20 (does it improve abstracts at all there). Then projects the untouched texts.
# Writes logs/w9l.done or logs/w9l.failed. The instance stops itself afterwards: after a grace period of
# W9_GRACE_MIN minutes (default 30) that ends early when the laptop touches logs/w9l.pulled, and after
# W9L_MAX_HOURS (default 5) at the latest. A stopped instance still bills its disk: `vast down` after the pull.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export STEER_USE_KERNELS=0 HF_HOME="${HF_HOME:-/workspace/.hf_cache}" NUM_SHARDS=1 GPUS_PER_SHARD=1
L=outputs/steering/logs
mkdir -p "$L"
MAX_HOURS="${W9L_MAX_HOURS:-5}"
RUN=w9_sandbag_late

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

( sleep "$(( MAX_HOURS * 3600 ))"; echo "$(date -Is) hard time limit of ${MAX_HOURS} h reached" >> $L/w9l.failed; stop_instance >> $L/w9l_stop.log 2>&1 ) &
WATCHDOG=$!

run_all() {
  set -e
  JOB_NAME=$RUN bash steering_extension/vast/run_shards.sh steering_extension.steer.generate \
    --manifest outputs/steering/runs/$RUN/generation_jobs.jsonl --batch-size 24 > $L/w9l.log 2>&1
  VEC=outputs/steering/vectors/qwen3.5-9b_sandbag_v1/vectors.safetensors
  JOB_NAME=w9_proj_$RUN bash steering_extension/vast/run_shards.sh steering_extension.steer.project \
    --run-dir outputs/steering/runs/$RUN --conditions harmful,framed_empty --vectors "$VEC" \
    --keys E,S,S_perp,rand0 --layers 4,6,8,10,12,14,16,18,20 --batch-size 8 >> $L/w9l.log 2>&1
}

if ( run_all ); then date -Is > $L/w9l.done; else echo "$(date -Is) failed; see $L/w9l.log" > $L/w9l.failed; fi
kill "$WATCHDOG" 2>/dev/null || true
for ((i=0; i<${W9_GRACE_MIN:-30}*6; i++)); do [[ -f $L/w9l.pulled ]] && break; sleep 10; done
stop_instance > $L/w9l_stop.log 2>&1
