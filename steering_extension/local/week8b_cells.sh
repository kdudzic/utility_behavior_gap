#!/usr/bin/env bash
# Week 8 follow-up (ideas 1 to 4 for a role vector). Two modes:
#   local   (laptop, after sharpen_role.py): vectors/qwen3.5-9b_w8b/vectors.safetensors = v4 keys + R_act_perp
#           (R_act with its E component projected out) + R_sharp, R_sharp_perp from vectors/qwen3.5-9b_role_sharp;
#           manifest runs/w8b_role_local: R_act, R_act_perp, R_sharp, R_sharp_perp at layer 6 +0.1, layer 10 -0.1,
#           layer 16 -0.1 (E's three clearest cells), 30 items x 2 repeats = 60 pairs per cell, plus the null cell.
#   remote  (instance, after extracting contrasts_essay_role_v2): adds R_wide_perp and R_content_perp to
#           vectors/qwen3.5-9b_essay_role_v2/vectors.safetensors (E from v4) and builds runs/w8b_role_remote with
#           R_wide, R_wide_perp, R_content, R_content_perp at the same three cells.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
PY=.venv/bin/python
export PYTHONPATH="$PWD:$PWD/src:${PYTHONPATH:-}"
MODE="${1:-local}"
CELLS=(6:0.1 10:-0.1 16:-0.1)

perp_into() {  # perp_into <dst.safetensors> <E source.safetensors> <key>...  : adds <key>_perp for each key, writes dst
  $PY - "$@" <<'EOF'
import sys
import numpy as np
from safetensors.numpy import load_file, save_file
dst, esrc, keys = sys.argv[1], sys.argv[2], sys.argv[3:]
t = load_file(dst); e = load_file(esrc)
layers = sorted({int(k.split("layer")[1]) for k in e if k.startswith("E/")})
for L in layers:
    u = e[f"E/layer{L}"].astype(np.float64); u = u / np.linalg.norm(u)
    for key in keys:
        v = t[f"{key}/layer{L}"].astype(np.float64)
        t[f"{key}_perp/layer{L}"] = (v - (v @ u) * u).astype(np.float32)
        if L in (6, 10, 16):
            print(f"{key} layer {L}: cos(E,{key})={v @ u / np.linalg.norm(v):+.3f}")
save_file(t, dst)
print(f"wrote {dst} ({len(t)} tensors)")
EOF
}

if [[ "$MODE" == "local" ]]; then
  D=outputs/steering/vectors/qwen3.5-9b_w8b; mkdir -p "$D"
  $PY - <<'EOF'
import numpy as np
from safetensors.numpy import load_file, save_file
t = load_file("outputs/steering/vectors/qwen3.5-9b_v4_role/vectors.safetensors")
s = load_file("outputs/steering/vectors/qwen3.5-9b_role_sharp/vectors.safetensors")
for k, v in s.items():
    if k.startswith("R_sharp"):
        t[k] = v
save_file(t, "outputs/steering/vectors/qwen3.5-9b_w8b/vectors.safetensors")
print(f"combined file: {len(t)} tensors")
EOF
  perp_into "$D/vectors.safetensors" outputs/steering/vectors/qwen3.5-9b_v4_role/vectors.safetensors R_act
  args=(); for k in R_act R_act_perp R_sharp R_sharp_perp; do for c in "${CELLS[@]}"; do args+=(--cell "$k:$c"); done; done
  $PY -m steering_extension.local.make_steering_jobs --vectors "$D/vectors.safetensors" --run-name w8b_role_local --items 30 --repeats 2 --task essay "${args[@]}"
else
  D=outputs/steering/vectors/qwen3.5-9b_essay_role_v2
  perp_into "$D/vectors.safetensors" outputs/steering/vectors/qwen3.5-9b_v4_role/vectors.safetensors R_wide R_content
  args=(); for k in R_wide R_wide_perp R_content R_content_perp; do for c in "${CELLS[@]}"; do args+=(--cell "$k:$c"); done; done
  $PY -m steering_extension.local.make_steering_jobs --vectors "$D/vectors.safetensors" --run-name w8b_role_remote --items 30 --repeats 2 --task essay "${args[@]}"
fi
