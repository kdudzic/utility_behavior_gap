# Steering-vector extension: how to run

Design and decisions: `PROPOSAL.md`. Pilot results: `docs/mini_pilot_report.md`. Rules: repo `AGENTS.md`
(steering section). All outputs land in `outputs/steering/` (gitignored). Paths below are relative to the
repo root. Since 2026-10-17 GPU work runs on vast.ai; the laptop builds jobs, drives the instance, judges
via OpenRouter, and analyses. The SLURM runner for Athena is kept at the end.

## Laptop setup (once)

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e . --no-deps
uv pip install --python .venv/bin/python -r requirements.txt vastai safetensors scipy python-dotenv requests
export PYTHONPATH=$PWD:$PWD/src
```

### Secrets

Keys live outside the repo tree in `~/.config/utility_behavior_gap/secrets.env` (file mode 600, directory
700; `XDG_CONFIG_HOME` honoured, `UBG_SECRETS_FILE` overrides the path):
```
OPENROUTER_API_KEY=sk-or-v1-...   # SPAR team key (default)
VAST_API_KEY=...                  # vast.ai, SPAR team account
```
`steering_extension/local/keys.py` (`load_keys()`, used by the Python tools and `vast.py`) and
`steering_extension/local/env.sh` (`source`d by `judge.sh`) load them, printing only the source name.
Precedence per variable: process environment > `secrets.env` > the gitignored in-repo files
`steering_extension/spar_openrouter.txt` / `steering_extension/spar_vastai.txt` > `.env`. The PI's personal
OpenRouter key (`.openrouter.txt`, or `OPENROUTER_API_KEY_PERSONAL=` in `secrets.env`) is used only when
`OPENROUTER_KEY_SOURCE=personal` is exported, and is never a silent fallback. Nothing prints a key value.

Audit the setup (sources, lengths, permissions, gitignore status, key material in tracked files, hook):
```bash
.venv/bin/python -m steering_extension.local.keys --check     # exits non-zero on any problem
```
A pre-commit hook refuses commits that stage a key file, contain the OpenRouter key pattern, or contain the
literal value of a loaded key; it reports path and line only. Versioned at
`steering_extension/local/hooks/pre-commit`; install once per clone with
`bash steering_extension/local/hooks/install_hooks.sh` (`--check` verifies it is installed and current).
`vast push` excludes `spar_*.txt`, `.openrouter.txt` and `.env`, so no key reaches a rented box.

## vast.ai workflow

`vast` below means `.venv/bin/python -m steering_extension.vast.vast`. One instance at a time; its id and ssh
endpoint are recorded in `outputs/steering/vast/instance.json`. Billing runs from `up` to `down`.

```bash
vast search --gpu A100_PCIE                 # rank offers by $/h (40 GB is enough for the 9B)
vast search --min-vram 79                   # 80 GB class for the 27B (or --num-gpus 2 --gpu A100_PCIE)
vast up --gpu A100_PCIE --disk 100          # cheapest matching offer; or: vast up --offer <ID>
vast push                                   # rsync code, data/inputs, manifests, vectors
vast bootstrap --wait                       # uv env + transformers main + Qwen/Qwen3.5-9B weights (~10 min)
vast run --name phase0 steering_extension.steer.generate --manifest outputs/steering/runs/<run>/generation_jobs.jsonl --batch-size 32
vast tail --name phase0                     # shard logs; [finished] when the tmux session ends
vast pull                                   # rsync outputs/steering/{runs,vectors,contrasts,logs} back
vast down                                   # destroy; asks you to type the instance id
```
`vast run` starts `NUM_SHARDS` processes (default: one per GPU) under tmux, each pinned to its GPUs, and merges
shard files when all finish. Re-running the same command resumes: `generate.py` skips `output_id`s already in
its shard file, so `vast pull` often and `vast push --full` after an instance loss. `vast ssh` opens a shell;
`vast jobs` lists tmux sessions and GPU use; `vast status` lists every instance on the account (the account is
shared: do not `down` instances you did not create).

Multi-GPU models: `vast up --num-gpus 2 --gpu A100_PCIE` then `vast run --gpus-per-shard 2 ...` (one shard
spanning both GPUs with `device_map=auto`). Set `STEER_MODEL=<hf id>` in the module args via `--model`.

## Phase 0: replication of the paper's framed-neutral essay effort cell

```bash
.venv/bin/python -m steering_extension.local.make_phase0_jobs --repeats 2 --run-name phase0_mini
vast push && vast run --name phase0 steering_extension.steer.generate --manifest outputs/steering/runs/phase0_mini/generation_jobs.jsonl --batch-size 32
vast pull
bash steering_extension/local/judge.sh outputs/steering/runs/phase0_mini 8        # paid: PI authorization required
.venv/bin/python -m steering_extension.local.analyze_cells --run-dir outputs/steering/runs/phase0_mini --group-by comparison
```

## Phase 1: vectors

```bash
.venv/bin/python -m steering_extension.local.make_contrast_set --items-per-task 30 --repeats 2 --contrasts E,R_id,R_act
vast push && vast run --name extract steering_extension.steer.extract --contrasts outputs/steering/contrasts/contrasts.jsonl --out-dir outputs/steering/vectors/qwen3.5-9b_v2
vast pull vectors
```
`vectors.safetensors` keys: `E/layer{L}`, `R_id/layer{L}`, `R_act/layer{L}`, `rand{k}/layer{L}` (norm-matched to E),
`norm/layer{L}` (RMS residual norm, dose unit). `vectors_report.json` has norms, relative norms, cosines.

## Phase 2: steered vs baseline cells

```bash
.venv/bin/python -m steering_extension.local.make_steering_jobs --vectors outputs/steering/vectors/qwen3.5-9b_v2/vectors.safetensors \
  --run-name pilot_full --items 30 --repeats 2 --cell E:16:0.05 --cell E:16:-0.1 --cell rand0:16:-0.2 ...
vast push && vast run --name pilot steering_extension.steer.generate --manifest outputs/steering/runs/pilot_full/generation_jobs.jsonl
vast pull
bash steering_extension/local/judge.sh outputs/steering/runs/pilot_full 8                         # paid
.venv/bin/python -m steering_extension.local.coherence_judge --run-dir outputs/steering/runs/pilot_full  # paid
.venv/bin/python -m steering_extension.local.analyze_cells --run-dir outputs/steering/runs/pilot_full
```
Cell spec `KEY:LAYER:R[:MODE]`; `R` is the signed dose as a fraction of the layer's RMS residual norm;
`MODE` is `response` (default) or `all`. Each manifest includes a `steer_baseline` cell (two independent
unsteered samples) as the null comparison; steered cells alias the baseline sample `b`.

## Athena (SLURM) runner, kept for reference

```bash
bash steering_extension/remote/bootstrap.sh     # on the login node; HF cache under $SCRATCH/.caches
sbatch --array=0-3 steering_extension/slurm/gpu_job.sbatch steering_extension.steer.generate --manifest <manifest> --batch-size 32
.venv/bin/python -m steering_extension.steer.generate --merge <run_dir>
```
Compute nodes are offline there: weights and `kernels-community/mamba-ssm` must be cached from the login node first.
Account `plgllmpsypath-gpu-a100`, partition `plgrid-gpu-a100`, 40 GB A100s. Login nodes were closed by the
admins on 2026-10-17 (security update, no ETA); the Phase 0-2 raw outputs still sit on `$SCRATCH` there.
