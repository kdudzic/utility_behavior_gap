# Steering-vector extension: how to run

Design and decisions: `PROPOSAL.md`. Rules: repo `AGENTS.md` (steering section).
All outputs land in `outputs/steering/` (gitignored). Paths below are relative to the repo root.

## Environment (uv)

```bash
bash steering_extension/remote/bootstrap.sh        # .venv via uv, installs base + steering deps, downloads Qwen/Qwen3.5-9B
export PYTHONPATH=$PWD:$PWD/src
```
On Athena the HF cache is `$SCRATCH/.caches/hf`; compute nodes are offline, so anything from the
Hub (weights, `kernels-community/mamba-ssm` v3 for causal_conv1d) must be cached from the login node first.

## GPU runners

- SLURM (Athena): `sbatch [--array=0-3] steering_extension/slurm/gpu_job.sbatch <module> <args>`; array
  index becomes `--shard/--num-shards`.
- vast.ai / any GPU box: `SHARD=0 NUM_SHARDS=1 bash steering_extension/vast/run_gpu.sh <module> <args>`.

## Phase 0: replication of the paper's framed-neutral essay effort cell

```bash
.venv/bin/python -m steering_extension.local.make_phase0_jobs --repeats 2 --run-name phase0_mini
sbatch --array=0-3 steering_extension/slurm/gpu_job.sbatch steering_extension.steer.generate --manifest outputs/steering/runs/phase0_mini/generation_jobs.jsonl --batch-size 32
.venv/bin/python -m steering_extension.steer.generate --merge outputs/steering/runs/phase0_mini
bash steering_extension/local/judge.sh outputs/steering/runs/phase0_mini 8        # paid: PI authorization required
.venv/bin/python -m steering_extension.local.analyze_cells --run-dir outputs/steering/runs/phase0_mini --group-by comparison
```

## Phase 1: vectors

```bash
.venv/bin/python -m steering_extension.local.make_contrast_set --items-per-task 14 --contrasts E,R_id,R_act
sbatch --array=0-3 steering_extension/slurm/gpu_job.sbatch steering_extension.steer.extract --contrasts outputs/steering/contrasts/contrasts.jsonl --out-dir outputs/steering/vectors/qwen3.5-9b_v1
.venv/bin/python -m steering_extension.steer.extract --merge --out-dir outputs/steering/vectors/qwen3.5-9b_v1
```
`vectors.safetensors` keys: `E/layer{L}`, `R_id/layer{L}`, `R_act/layer{L}`, `rand{k}/layer{L}` (norm-matched to E),
`norm/layer{L}` (RMS residual norm, dose unit). `vectors_report.json` has norms, relative norms, cosines.

## Phase 2: steered vs baseline cells

```bash
.venv/bin/python -m steering_extension.local.make_steering_jobs --vectors outputs/steering/vectors/qwen3.5-9b_v1/vectors.safetensors \
  --run-name sweep_mini --items 10 --cell E:12:0.1 --cell E:16:0.1 --cell E:20:0.1 --cell E:16:0.2 ...
sbatch --array=0-3 steering_extension/slurm/gpu_job.sbatch steering_extension.steer.generate --manifest outputs/steering/runs/sweep_mini/generation_jobs.jsonl
.venv/bin/python -m steering_extension.steer.generate --merge outputs/steering/runs/sweep_mini
bash steering_extension/local/judge.sh outputs/steering/runs/sweep_mini 8                         # paid
.venv/bin/python -m steering_extension.local.coherence_judge --run-dir outputs/steering/runs/sweep_mini  # paid
.venv/bin/python -m steering_extension.local.analyze_cells --run-dir outputs/steering/runs/sweep_mini
```
Cell spec `KEY:LAYER:R[:MODE]`; `R` is the signed dose as a fraction of the layer's RMS residual norm;
`MODE` is `response` (default) or `all`. Each manifest includes a `steer_baseline` cell (two independent
unsteered samples) as the null comparison; steered cells alias the baseline sample `b`.
