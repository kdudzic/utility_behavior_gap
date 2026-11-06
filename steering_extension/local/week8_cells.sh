#!/usr/bin/env bash
# Week 8 (plan item 2, role direction): local prep, no GPU.
#   1. vectors/qwen3.5-9b_v4_role/vectors.safetensors: every v4 key plus R_id_perp = R_id minus its projection on E,
#      per layer (the part of the role direction that is not the effort direction).
#   2. runs/w8_role_steer: R_id and R_id_perp at E's three clearest essay cells (layer 6 +0.1, layer 10 -0.1,
#      layer 16 -0.1), 30 items x 2 repeats = 60 pairs per cell, plus the unsteered null cell.
#   3. contrasts/contrasts_essay_role_v1.jsonl: world-class vs skilled on the 30 essay items x 10 repeats
#      (300 per arm, same size as the essay-built E vector) for an essay-built R_id.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
PY=.venv/bin/python
export PYTHONPATH="$PWD:$PWD/src:${PYTHONPATH:-}"

V4=outputs/steering/vectors/qwen3.5-9b_v4/vectors.safetensors
ROLE_DIR=outputs/steering/vectors/qwen3.5-9b_v4_role
mkdir -p "$ROLE_DIR"
$PY - "$V4" "$ROLE_DIR/vectors.safetensors" <<'EOF'
import sys
import numpy as np
from safetensors.numpy import load_file, save_file
src, dst = sys.argv[1:3]
t = load_file(src)
out = dict(t)
layers = sorted({int(k.split("layer")[1]) for k in t if k.startswith("E/")})
for L in layers:
    e = t[f"E/layer{L}"].astype(np.float64)
    r = t[f"R_id/layer{L}"].astype(np.float64)
    u = e / np.linalg.norm(e)
    perp = r - (r @ u) * u
    out[f"R_id_perp/layer{L}"] = perp.astype(t[f"R_id/layer{L}"].dtype)
    if L in (6, 10, 16):
        print(f"layer {L}: cos(E,R_id)={r @ u / np.linalg.norm(r):.3f}  |R_id|={np.linalg.norm(r):.4f}  |R_id_perp|={np.linalg.norm(perp):.4f}  cos(E,R_id_perp)={perp @ u / np.linalg.norm(perp):+.2e}")
save_file(out, dst)
print(f"wrote {dst} with {len(out)} tensors")
EOF
cp outputs/steering/vectors/qwen3.5-9b_v4/layer_profile.csv "$ROLE_DIR/" 2>/dev/null || true

$PY -m steering_extension.local.make_steering_jobs --vectors "$ROLE_DIR/vectors.safetensors" --run-name w8_role_steer \
  --items 30 --repeats 2 --task essay \
  --cell R_id:6:0.1 --cell R_id:10:-0.1 --cell R_id:16:-0.1 \
  --cell R_id_perp:6:0.1 --cell R_id_perp:10:-0.1 --cell R_id_perp:16:-0.1

$PY -m steering_extension.local.make_contrast_set --tasks essay --items-per-task 30 --repeats 10 --contrasts R_id \
  --out outputs/steering/contrasts/contrasts_essay_role_v1.jsonl
wc -l outputs/steering/runs/w8_role_steer/generation_jobs.jsonl outputs/steering/contrasts/contrasts_essay_role_v1.jsonl
