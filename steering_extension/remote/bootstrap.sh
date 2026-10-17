#!/usr/bin/env bash
# Bootstrap the steering-extension Python environment with uv and pre-download model weights.
# Works on a vast.ai instance (default caches under /workspace) and on Athena (login node, $SCRATCH);
# override HF_HOME / UV_CACHE_DIR / STEER_MODELS to taste.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"
if [ -d /workspace ]; then CACHE_BASE=/workspace; else CACHE_BASE="${SCRATCH:-$HOME}/.caches"; fi
export HF_HOME="${HF_HOME:-$CACHE_BASE/.hf_cache}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$CACHE_BASE/.uv_cache}"
export HF_HUB_ENABLE_HF_TRANSFER=1
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
mkdir -p "$HF_HOME" "$UV_CACHE_DIR"
cd "$REPO_ROOT"
if [ ! -d .venv ]; then
  uv venv --python 3.12 .venv
fi
uv pip install --python .venv/bin/python -q hf_transfer huggingface_hub
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
