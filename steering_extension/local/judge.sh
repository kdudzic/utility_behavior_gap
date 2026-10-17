#!/usr/bin/env bash
# Judge a steering run with the paper's unchanged panel script (3 judges, both orders).
# Paid OpenRouter calls: only run with the PI's authorization for the phase.
# Usage: bash steering_extension/local/judge.sh <run_dir> [workers]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
RUN_DIR="$1"; WORKERS="${2:-8}"
source steering_extension/local/env.sh
export PYTHONPATH="$PWD/src:$PWD:${PYTHONPATH:-}"
.venv/bin/python src/utility_behavior_gap/scripts/run_judging.py --manifest "$RUN_DIR/generation_jobs.jsonl" --orders both --workers "$WORKERS"
