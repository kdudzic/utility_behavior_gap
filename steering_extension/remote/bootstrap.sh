#!/usr/bin/env bash
# Bootstrap the steering-extension Python environment with uv and pre-download model weights.
# Works on Athena (login node) and on a vast.ai instance; set STEER_ROOT / HF_HOME to taste.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export HF_HOME="${HF_HOME:-${SCRATCH:-$HOME}/.caches/huggingface}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-${SCRATCH:-$HOME}/.caches/uv}"
mkdir -p "$HF_HOME" "$UV_CACHE_DIR"
cd "$REPO_ROOT"
if [ ! -d .venv ]; then
  uv venv --python 3.12 .venv
fi
# Repo package (offline analysis deps) without spaCy; steering extras from the extension's requirements.
uv pip install --python .venv/bin/python -e . --no-deps
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python -r steering_extension/requirements-remote.txt
MODELS="${STEER_MODELS:-Qwen/Qwen3.5-9B}"
for m in $MODELS; do
  .venv/bin/python - "$m" <<'PY'
import sys
from huggingface_hub import snapshot_download
print(snapshot_download(sys.argv[1], allow_patterns=["*.json", "*.safetensors", "*.txt", "*.py", "*.jinja", "*.model", "*.tiktoken"]))
PY
done
echo BOOTSTRAP_DONE
