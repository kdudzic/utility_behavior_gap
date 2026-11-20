#!/usr/bin/env bash
# Week-10 (2026-11-20, 18.11 todo item 2c), run ON THE INSTANCE inside tmux so the laptop can disconnect:
#   vast ssh "cd /workspace/utility_behavior_gap && tmux new-session -d -s w10 'bash steering_extension/vast/w10_chain.sh'"
# Scores the unsteered texts in outputs/steering/w10_token_inputs/* (filtered copies of local runs plus the OpenRouter
# texts of runs w10_or_essay / w10_or_grant, synced by hand) with steer/token_probs.py: per-token probability, rank
# and nucleus position under Qwen3.5-9B at temperature 1.0. Writes outputs/steering/w10_token_probs/scores.jsonl and
# logs/w10.done or logs/w10.failed. The instance stops itself afterwards: after a grace period of W10_GRACE_MIN
# minutes (default 30) that ends early when the laptop touches logs/w10.pulled, and after W10_MAX_HOURS (default 3)
# at the latest. A stopped instance still bills its disk: `vast down` after the pull.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
export STEER_USE_KERNELS=0 HF_HOME="${HF_HOME:-/workspace/.hf_cache}"
L=outputs/steering/logs
mkdir -p "$L"
MAX_HOURS="${W10_MAX_HOURS:-3}"

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

( sleep "$(( MAX_HOURS * 3600 ))"; echo "$(date -Is) hard time limit of ${MAX_HOURS} h reached" >> $L/w10.failed; stop_instance >> $L/w10_stop.log 2>&1 ) &
WATCHDOG=$!

run_all() {
  set -e
  args=()
  for d in outputs/steering/w10_token_inputs/*/; do args+=(--run-dir "${d%/}"); done
  .venv/bin/python -m steering_extension.steer.token_probs "${args[@]}" --out outputs/steering/w10_token_probs/scores.jsonl > $L/w10.log 2>&1
}

if ( run_all ); then date -Is > $L/w10.done; else echo "$(date -Is) failed; see $L/w10.log" > $L/w10.failed; fi
kill "$WATCHDOG" 2>/dev/null || true
for ((i=0; i<${W10_GRACE_MIN:-30}*6; i++)); do [[ -f $L/w10.pulled ]] && break; sleep 10; done
stop_instance > $L/w10_stop.log 2>&1
