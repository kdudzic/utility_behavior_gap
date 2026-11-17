#!/usr/bin/env bash
# DS0: DeepSeek-V3.2 white-box smoke test, run ON THE INSTANCE inside tmux so the laptop can disconnect.
# Background, evidence and cost estimates: steering_extension/docs/deepseek_port_notes.md.
#
# Laptop side (PAID: `up` starts billing; needs the PI's go; the account allows one recorded instance at a time):
#   vast search --num-gpus 8 --min-vram 90 --disk 900 --min-down 2000
#   vast up --offer <ID> --disk 900 --label ds0
#   vast push
#   vast ssh "cd /workspace/utility_behavior_gap && tmux new-session -d -s ds0 'bash steering_extension/vast/ds0_chain.sh'"
#   vast ssh "tail -n 20 /workspace/utility_behavior_gap/outputs/steering/logs/ds0_chain.log"      # progress
#   vast pull logs ds0                                                                              # when DONE/FAILED
#   vast ssh "touch /workspace/utility_behavior_gap/outputs/steering/logs/ds0.pulled"               # ends the grace wait
#   vast down                                                                                       # ALWAYS: stop keeps the disk billing
#
# Steps on the instance:
#   0. host check: stop credentials, GPUs, free disk
#   1. Python environment (remote/bootstrap.sh without weights) + the pins DeepSeek needs
#   2. preflight without weights: GPUs, FP8 kernel on this GPU type, tokenizer and chat prompt
#   3. download the checkpoint (about 690 GB)
#   4. smoke test (load, 4 texts, residuals at 3 layers, random-vector steering, tokens/s, peak memory)
# Outputs: outputs/steering/logs/ds0_chain.log, outputs/steering/logs/ds0.DONE or ds0.FAILED (one line each),
#          outputs/steering/ds0/preflight_report.json, outputs/steering/ds0/smoke_report.json.
#
# The instance stops itself (GPU billing ends, disk is kept) in every case:
#   - after DONE or FAILED, once the laptop has touched logs/ds0.pulled or DS0_GRACE_MIN minutes have passed;
#   - after DS0_HARD_LIMIT_MIN minutes from the start, whatever is running (a detached watchdog).
# A stopped instance cannot be reached by ssh. To read results after a stop: `vastai start instance <id>`
# (only works while the GPUs are still free), pull, then `vast down`.
#
# Environment knobs: DS0_HARD_LIMIT_MIN (180), DS0_GRACE_MIN (20), DS0_NO_STOP=1 (never stop; for debugging),
# DS0_MIN_DISK_GB (760), DS0_STRICT_KERNEL=0 (continue when the FP8 kernel micro-test fails),
# DS0_MODEL, DS0_TRANSFORMERS_REF, DS0_KERNELS_SPEC, DS0_SMOKE_ARGS (extra args for deepseek_smoke.py),
# HF_TOKEN (optional; passed through to the download, never printed).
set -uo pipefail
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"   # absolute: the watchdog re-runs it after the cd
cd "$(dirname "$SELF")/../.."
REPO="$PWD"
L="$REPO/outputs/steering/logs"
OUT="$REPO/outputs/steering/ds0"
mkdir -p "$L" "$OUT"
LOG="$L/ds0_chain.log"
MARK_DONE="$L/ds0.DONE"
MARK_FAILED="$L/ds0.FAILED"
MARK_PULLED="$L/ds0.pulled"
MARK_STOP_FAILED="$L/ds0.STOP_FAILED"
WATCHDOG_PID="$L/ds0.watchdog.pid"

HARD_LIMIT_MIN="${DS0_HARD_LIMIT_MIN:-180}"
GRACE_MIN="${DS0_GRACE_MIN:-20}"
MIN_DISK_GB="${DS0_MIN_DISK_GB:-760}"
MODEL="${DS0_MODEL:-deepseek-ai/DeepSeek-V3.2}"
# transformers main commit whose deepseek_v32 and FP8 code the port notes were written against (2026-11-17),
# and the `kernels` range that commit's setup.py asks for (requirements-remote.txt still pins <0.18 for Qwen).
TRANSFORMERS_REF="${DS0_TRANSFORMERS_REF:-0e6e6d68fb20ebffe49fe7bb30f301b24d930b05}"
KERNELS_SPEC="${DS0_KERNELS_SPEC:-kernels>=0.18.2,<0.19}"
VASTCLI_VENV=/workspace/.vastcli

export PATH="$HOME/.local/bin:$PATH"
export HF_HOME="${HF_HOME:-/workspace/.hf_cache}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.uv_cache}"
export HF_HUB_ENABLE_HF_TRANSFER=1 TOKENIZERS_PARALLELISM=false
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTHONPATH="$REPO:$REPO/src:${PYTHONPATH:-}"
export STEER_USE_KERNELS=0
PY="$REPO/.venv/bin/python"

log() { echo "$(date -Is) $*"; }

# vast sets CONTAINER_ID and CONTAINER_API_KEY for the container's first process; a tmux started over ssh
# often does not inherit them, so fall back to PID 1's environment, then /etc/environment.
vast_env() {
  local v="${!1:-}"
  if [ -z "$v" ] && [ -r /proc/1/environ ]; then v="$(tr '\0' '\n' < /proc/1/environ | sed -n "s/^$1=//p" | head -n 1)"; fi
  if [ -z "$v" ] && [ -r /etc/environment ]; then v="$(sed -n "s/^$1=//p" /etc/environment | head -n 1 | tr -d '"')"; fi
  printf '%s' "$v"
}
CID="$(vast_env CONTAINER_ID)"
CKEY="$(vast_env CONTAINER_API_KEY)"

stop_instance() {
  # $1: reason. Tries the vastai CLI, then the REST call the week-9 chain uses. Never prints the key.
  if [ "${DS0_NO_STOP:-0}" = "1" ]; then log "DS0_NO_STOP=1: instance left running ($1). It keeps billing until you run: vast down"; return 0; fi
  if [ -z "$CID" ] || [ -z "$CKEY" ]; then
    log "CANNOT STOP: CONTAINER_ID or CONTAINER_API_KEY not found. THE INSTANCE KEEPS BILLING. Run from the laptop: vast down"
    echo "$(date -Is) no stop credentials ($1)" > "$MARK_STOP_FAILED"; return 1
  fi
  sync
  local attempt out
  for attempt in 1 2 3 4 5; do
    log "stopping instance $CID ($1), attempt $attempt"
    if [ -x "$VASTCLI_VENV/bin/vastai" ]; then
      out="$("$VASTCLI_VENV/bin/vastai" stop instance "$CID" --api-key "$CKEY" 2>&1 | head -c 300)"
      log "vastai: ${out//$CKEY/[key]}"
    fi
    out="$(curl -s -m 60 -X PUT "https://console.vast.ai/api/v0/instances/${CID}/" -H "Authorization: Bearer ${CKEY}" \
      -H "Content-Type: application/json" -d '{"state": "stopped"}' 2>&1 | head -c 300)"
    log "rest: ${out//$CKEY/[key]}"
    sleep 45   # a successful stop kills this container before the sleep ends
  done
  log "STILL RUNNING after 5 stop attempts. THE INSTANCE KEEPS BILLING. Run from the laptop: vast down"
  echo "$(date -Is) stop attempts had no effect ($1)" > "$MARK_STOP_FAILED"
  return 1
}

# ---- watchdog mode: `bash ds0_chain.sh --watchdog` (started detached by the main run below)
if [ "${1:-}" = "--watchdog" ]; then
  echo $$ > "$WATCHDOG_PID"
  sleep "$(( HARD_LIMIT_MIN * 60 ))"
  {
    log "HARD LIMIT of ${HARD_LIMIT_MIN} min reached"
    if [ ! -e "$MARK_DONE" ] && [ ! -e "$MARK_FAILED" ]; then echo "$(date -Is) FAILED: hard time limit of ${HARD_LIMIT_MIN} min reached" > "$MARK_FAILED"; fi
    stop_instance "hard time limit"
  } >> "$LOG" 2>&1
  exit 0
fi

exec > >(tee -a "$LOG") 2>&1
T_START=$(date +%s)
elapsed_min() { echo $(( ( $(date +%s) - T_START ) / 60 )); }
rm -f "$MARK_DONE" "$MARK_FAILED" "$MARK_PULLED" "$MARK_STOP_FAILED" "$WATCHDOG_PID"
log "DS0 chain start: model=$MODEL hard_limit=${HARD_LIMIT_MIN}min grace=${GRACE_MIN}min no_stop=${DS0_NO_STOP:-0}"

FINISHED=0
finish() {
  # $1: DONE or FAILED, $2: message. Writes the marker, waits for the laptop to pull, stops the instance.
  [ "$FINISHED" = "1" ] && return
  FINISHED=1
  local marker="$MARK_DONE"; [ "$1" = "FAILED" ] && marker="$MARK_FAILED"
  echo "$(date -Is) $1: $2 (after $(elapsed_min) min)" > "$marker"
  log "$1: $2 (after $(elapsed_min) min)"
  nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader 2>/dev/null || true
  if [ "${DS0_NO_STOP:-0}" != "1" ]; then
    log "waiting up to ${GRACE_MIN} min for the laptop to pull (touch $MARK_PULLED to stop now)"
    local waited=0
    while [ ! -e "$MARK_PULLED" ] && [ "$waited" -lt $(( GRACE_MIN * 60 )) ]; do sleep 15; waited=$(( waited + 15 )); done
    if [ -e "$MARK_PULLED" ]; then log "laptop has pulled"; else log "grace period over, nobody pulled"; fi
  fi
  if [ -r "$WATCHDOG_PID" ]; then kill "$(cat "$WATCHDOG_PID")" 2>/dev/null || true; fi
  stop_instance "$1"
}
# any exit that did not go through finish (killed shell, bug in this script) still stops the instance
trap 'finish FAILED "chain exited unexpectedly"' EXIT
trap 'finish FAILED "chain interrupted"; exit 1' INT TERM HUP

step() {
  # step <name> <command...>: run, log the wall time, return the exit code
  local name="$1"; shift
  local t0; t0=$(date +%s)
  log "---- step $name: start"
  "$@"
  local rc=$?
  log "---- step $name: exit $rc after $(( $(date +%s) - t0 )) s (total $(elapsed_min) min)"
  return $rc
}

# ---- 0. host check (before anything slow)
host_check() {
  command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1
  command -v uv >/dev/null || { log "uv is not installed and could not be installed"; return 1; }
  if [ ! -x "$VASTCLI_VENV/bin/vastai" ]; then
    uv venv --python 3.12 "$VASTCLI_VENV" >/dev/null 2>&1 && uv pip install --python "$VASTCLI_VENV/bin/python" -q vastai
  fi
  [ -x "$VASTCLI_VENV/bin/vastai" ] && log "vastai CLI installed" || log "vastai CLI not installed; the REST stop call will be used"
  if [ "${DS0_NO_STOP:-0}" != "1" ]; then
    if [ -z "$CID" ] || [ -z "$CKEY" ]; then log "CONTAINER_ID / CONTAINER_API_KEY not found: this run could not stop itself"; return 1; fi
    log "stop credentials found for instance $CID (key length ${#CKEY})"
  fi
  nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader || { log "nvidia-smi failed"; return 1; }
  local free_kb have_kb free_gb have_gb
  mkdir -p "$HF_HOME" || { log "cannot create $HF_HOME"; return 1; }
  free_kb="$(df -Pk "$HF_HOME" | awk 'NR==2 {print $4}')"
  have_kb="$(du -sk "$HF_HOME" 2>/dev/null | awk '{print $1}')"
  free_gb=$(( ${free_kb:-0} / 1000000 ))
  have_gb=$(( ${have_kb:-0} / 1000000 ))
  log "disk: ${free_gb} GB free at $HF_HOME, ${have_gb} GB already in it"
  if [ $(( free_gb + have_gb )) -lt "$MIN_DISK_GB" ]; then log "need ${MIN_DISK_GB} GB for the checkpoint and the environment"; return 1; fi
}

# ---- 1. environment
env_setup() {
  STEER_SKIP_WEIGHTS=1 bash steering_extension/remote/bootstrap.sh || return 1
  uv pip install --python "$PY" "transformers @ git+https://github.com/huggingface/transformers.git@${TRANSFORMERS_REF}" "$KERNELS_SPEC" || return 1
  if ! "$PY" -c "import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)"; then
    # README, "Driver check after bootstrap": the newest torch wheel can be too new for the host driver
    log "torch cannot see CUDA; installing the cu128 build as the README describes"
    uv pip install --python "$PY" --index-url https://download.pytorch.org/whl/cu128 'torch<2.10' || return 1
    "$PY" -c "import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)" || { log "torch still cannot see CUDA"; return 1; }
  fi
  "$PY" -c "import torch, transformers; print('torch', torch.__version__, 'transformers', transformers.__version__, 'gpus', torch.cuda.device_count())"
}

# ---- 2. preflight without weights
preflight() {
  local extra=()
  "$PY" steering_extension/remote/deepseek_smoke.py --model "$MODEL" --preflight-only --min-gpus 8 --out "$OUT/preflight_report.json" && return 0
  if [ "${DS0_STRICT_KERNEL:-1}" = "0" ]; then
    log "preflight failed; DS0_STRICT_KERNEL=0, retrying without the FP8 kernel micro-test"
    extra=(--skip-kernel-test)
    "$PY" steering_extension/remote/deepseek_smoke.py --model "$MODEL" --preflight-only --min-gpus 8 "${extra[@]}" --out "$OUT/preflight_report.json" && return 0
  fi
  return 1
}

# ---- 3. download (same file patterns as remote/bootstrap.sh)
download() {
  "$PY" - "$MODEL" <<'PY'
import sys, time
from huggingface_hub import snapshot_download
t0 = time.time()
path = snapshot_download(sys.argv[1], allow_patterns=["*.json", "*.safetensors", "*.txt", "*.py", "*.jinja", "*.model", "*.tiktoken"], max_workers=16)
print(f"downloaded to {path} in {(time.time() - t0) / 60:.1f} min", flush=True)
PY
}

# ---- 4. smoke test
smoke() {
  # shellcheck disable=SC2086
  "$PY" steering_extension/remote/deepseek_smoke.py --model "$MODEL" --min-gpus 8 --out "$OUT/smoke_report.json" ${DS0_SMOKE_ARGS:-}
}

setsid nohup bash "$SELF" --watchdog >/dev/null 2>&1 &
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$WATCHDOG_PID" ] && break; sleep 0.5; done   # the watchdog writes its own pid
if [ -s "$WATCHDOG_PID" ] && kill -0 "$(cat "$WATCHDOG_PID")" 2>/dev/null; then
  log "watchdog started (pid $(cat "$WATCHDOG_PID")): the instance stops after ${HARD_LIMIT_MIN} min at the latest"
else
  log "the watchdog did not start; refusing to run without a hard time limit"
  finish FAILED "watchdog did not start"; exit 1
fi

step host_check host_check || { finish FAILED "host check failed; see $LOG"; exit 1; }
step env_setup env_setup   || { finish FAILED "environment setup failed; see $LOG"; exit 1; }
step preflight preflight   || { finish FAILED "preflight failed before the download; see $OUT/preflight_report.json"; exit 1; }
step download download     || { finish FAILED "checkpoint download failed; see $LOG"; exit 1; }
step smoke smoke           || { finish FAILED "smoke test failed; see $OUT/smoke_report.json"; exit 1; }
finish DONE "smoke test passed; report in $OUT/smoke_report.json"
exit 0
