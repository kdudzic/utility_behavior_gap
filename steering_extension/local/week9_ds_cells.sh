#!/usr/bin/env bash
# Week 9, DeepSeek V3.2 hosted white-box (week9_plan.txt, steps DS1 to DS5). Two modes:
#   base   (laptop or instance, no vectors needed):
#          runs/ds_base_essay  harmful vs framed-empty on essays (paper cell 0.10) + untouched max-effort vs neutral
#          runs/ds_base_grant  harmful vs framed-empty on grant abstracts (paper cell 0.31)
#          contrasts/contrasts_ds_v1.jsonl  extraction prompts: E = max-effort vs neutral on grant items (held out
#          for the essay steering cells), S = harmful vs framed-empty on essay items; 30 items x 5 repeats = 150
#          responses per arm each.
#   steer  (instance, after extraction into vectors/deepseek-v3.2_v1): adds S_perp (S with its E component
#          projected out) and builds runs/ds_steer on essays, 60 pairs per cell, at layers 12, 20, 30 of 61:
#          E added under the harmful prompt at r = +0.05 and +0.1, S removed under the harmful prompt at r = -0.1,
#          S added under the framed-empty prompt at r = +0.1; at layer 20 also a random direction (+0.1, harmful)
#          and S_perp (-0.1, harmful). Harmful cells are also paired with the framed-empty text.
#          Nothing is known about this model's dose scale, so the grid spans layers and two doses of E; the cells
#          to judge are chosen afterwards from coherence.
# Manifests carry actor deepseek-v3.2-or (the paper's id) through STEER_ACTOR / STEER_MODEL_LABEL.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
PY=.venv/bin/python
export PYTHONPATH="$PWD:$PWD/src:${PYTHONPATH:-}"
export STEER_ACTOR=deepseek-v3.2-or STEER_MODEL_LABEL="deepseek-ai/DeepSeek-V3.2 (local hf, fp8)"
MODE="${1:-base}"
VDIR=outputs/steering/vectors/deepseek-v3.2_v1

if [[ "$MODE" == "base" ]]; then
  $PY -m steering_extension.local.make_sandbag_jobs --run-name ds_base_essay --task essay --items 30 --repeats 2 --effort-ref
  $PY -m steering_extension.local.make_sandbag_jobs --run-name ds_base_grant --task grant_proposal_abstract --items 30 --repeats 2
  $PY - <<'PYEOF'
import json
from steering_extension.local.common import ROOT, effort_prompt, framed_neutral_prompt, task_items
from steering_extension.local.make_sandbag_jobs import cause_for, empty_prompt, harmful_prompt
from utility_behavior_gap.io_utils import read_csv_rows
from utility_behavior_gap.paths import INPUTS
causes = read_csv_rows(INPUTS / "moral_cause_pairs.csv")
rows = []
for row in task_items("grant_proposal_abstract")[:30]:
    for rep in range(5):
        cid = f"{row['task']}:{row['item_index']}:r{rep}"
        rows.append({"contrast": "E", "arm": "pos", "cid": cid, "prompt": effort_prompt(row)})
        rows.append({"contrast": "E", "arm": "neg", "cid": cid, "prompt": framed_neutral_prompt(row)})
pool = task_items("essay")
for pos, row in enumerate(pool[:30]):
    for rep in range(5):
        cid = f"{row['task']}:{row['item_index']}:r{rep}"
        cause = cause_for(causes, len(pool), pos, rep + 2)   # repeats 2 to 6: other causes than the judged pairs use
        rows.append({"contrast": "S", "arm": "pos", "cid": cid, "prompt": harmful_prompt(row, cause)})
        rows.append({"contrast": "S", "arm": "neg", "cid": cid, "prompt": empty_prompt(row)})
out = ROOT / "outputs" / "steering" / "contrasts" / "contrasts_ds_v1.jsonl"
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
print(f"wrote {len(rows)} contrast prompts -> {out}")
PYEOF
else
  $PY - "$VDIR/vectors.safetensors" <<'PYEOF'
import sys
import numpy as np
from safetensors.numpy import load_file, save_file
dst = sys.argv[1]
t = load_file(dst)
layers = sorted({int(k.split("layer")[1]) for k in t if k.startswith("S/")})
for L in layers:
    e = t[f"E/layer{L}"].astype(np.float64); u = e / np.linalg.norm(e)
    s = t[f"S/layer{L}"].astype(np.float64)
    t[f"S_perp/layer{L}"] = (s - (s @ u) * u).astype(np.float32)
    if L % 6 == 0:
        print(f"layer {L}: cos(S,E)={s @ u / np.linalg.norm(s):+.3f}  |S|={np.linalg.norm(s):.3f}  |E|={np.linalg.norm(e):.3f}  rms={float(t[f'norm/layer{L}'][0]):.2f}")
save_file(t, dst)
print(f"wrote {dst} ({len(t)} tensors)")
PYEOF
  args=()
  for L in 12 20 30; do
    args+=(--cell "E:$L:0.05:harmful" --cell "E:$L:0.1:harmful" --cell "S:$L:-0.1:harmful" --cell "S:$L:0.1:empty")
  done
  args+=(--cell "rand0:20:0.1:harmful" --cell "S_perp:20:-0.1:harmful")
  $PY -m steering_extension.local.make_sandbag_jobs --vectors "$VDIR/vectors.safetensors" --run-name ds_steer --task essay --items 30 --repeats 2 --bridge "${args[@]}"
fi
