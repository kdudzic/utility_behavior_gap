#!/usr/bin/env bash
# Week 9, sandbagging and the effort direction (week9_plan.txt item 4), grant task. Two modes:
#   local   (laptop): runs/w9_sandbag_local = harmful vs framed-empty untouched (replication of the paper cell),
#           essay-built E added under the harmful prompt at layers 6, 10, 16 with r = +0.05, a random direction at
#           layer 10, the same steered texts paired with the framed-empty text, and untouched max-effort vs neutral
#           (readout reference). 30 items x 2 repeats = 60 pairs per cell. Also writes the extraction prompts for
#           the sandbagging vector S (harmful minus framed-empty, 30 grant items x 10 repeats = 300 per arm).
#   remote  (instance, after extracting S): copies E from the essay-built file into vectors/qwen3.5-9b_sandbag_v1,
#           adds S_perp (S with its E component projected out), and builds runs/w9_sandbag_remote: S and S_perp
#           removed under the harmful prompt (layer 10, r = -0.1, also paired with framed-empty) and added under
#           the framed-empty prompt (layer 10, r = +0.1).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
PY=.venv/bin/python
export PYTHONPATH="$PWD:$PWD/src:${PYTHONPATH:-}"
MODE="${1:-local}"
EVEC=outputs/steering/vectors/qwen3.5-9b_essay_v1/vectors.safetensors
SDIR=outputs/steering/vectors/qwen3.5-9b_sandbag_v1

if [[ "$MODE" == "local" ]]; then
  $PY -m steering_extension.local.make_sandbag_jobs --vectors "$EVEC" --run-name w9_sandbag_local --items 30 --repeats 2 \
    --cell E:6:0.05:harmful --cell E:10:0.05:harmful --cell E:16:0.05:harmful --cell rand0:10:0.05:harmful --bridge --effort-ref
  $PY - <<'PYEOF'
import json
from pathlib import Path
from steering_extension.local.common import ROOT, task_items
from steering_extension.local.make_sandbag_jobs import cause_for, empty_prompt, harmful_prompt
from utility_behavior_gap.io_utils import read_csv_rows
from utility_behavior_gap.paths import INPUTS
causes = read_csv_rows(INPUTS / "moral_cause_pairs.csv")
pool = task_items("grant_proposal_abstract")
out = ROOT / "outputs" / "steering" / "contrasts" / "contrasts_sandbag_v1.jsonl"
rows = []
for pos, row in enumerate(pool[:30]):
    for rep in range(10):
        cid = f"{row['task']}:{row['item_index']}:r{rep}"
        cause = cause_for(causes, len(pool), pos, rep)
        rows.append({"contrast": "S", "arm": "pos", "cid": cid, "prompt": harmful_prompt(row, cause)})
        rows.append({"contrast": "S", "arm": "neg", "cid": cid, "prompt": empty_prompt(row)})
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
print(f"wrote {len(rows)} contrast prompts -> {out} ({len({r['prompt'] for r in rows if r['arm']=='pos'})} distinct harmful prompts)")
PYEOF
else
  $PY - "$SDIR/vectors.safetensors" "$EVEC" <<'PYEOF'
import sys
import numpy as np
from safetensors.numpy import load_file, save_file
dst, esrc = sys.argv[1], sys.argv[2]
t = load_file(dst); e = load_file(esrc)
layers = sorted({int(k.split("layer")[1]) for k in t if k.startswith("S/")})
for L in layers:
    ev = e[f"E/layer{L}"].astype(np.float64); u = ev / np.linalg.norm(ev)
    s = t[f"S/layer{L}"].astype(np.float64)
    t[f"E/layer{L}"] = e[f"E/layer{L}"]
    t[f"S_perp/layer{L}"] = (s - (s @ u) * u).astype(np.float32)
    if L in (4, 6, 10, 14, 16, 20):
        print(f"layer {L}: cos(S,E)={s @ u / np.linalg.norm(s):+.3f}  |S|={np.linalg.norm(s):.3f}  |E|={np.linalg.norm(ev):.3f}  rms(S file)={float(t[f'norm/layer{L}'][0]):.2f}  rms(E file)={float(e[f'norm/layer{L}'][0]):.2f}")
save_file(t, dst)
print(f"wrote {dst} ({len(t)} tensors)")
PYEOF
  $PY -m steering_extension.local.make_sandbag_jobs --vectors "$SDIR/vectors.safetensors" --run-name w9_sandbag_remote --items 30 --repeats 2 \
    --cell S:10:-0.1:harmful --cell S_perp:10:-0.1:harmful --cell S:10:0.1:empty --cell S_perp:10:0.1:empty --bridge
fi
