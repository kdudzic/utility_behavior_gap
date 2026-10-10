# Public Scientific Replication Repository

- Do not read or edit `CLAUDE.md`.
- No paid API calls without the user's explicit authorization. The standard
  paper reproduction must remain offline.
- `paper_reproduction/ARTIFACTS.md` selects the paper analyses. Historical
  filenames and timestamps do not establish authority. Preserve the exact
  conditions, prompt channel, competition scaffold, outcomes, panel, exclusions,
  and statistical conventions. Do not substitute similar experiments.
- Preserve source evidence and existing user changes. Do not delete raw data,
  labels, or historical outputs to fix filtering or publication problems.
- A private backup and a local public checkout are not remote publication.
  For a requested public update, package the necessary portable inputs, run
  the affected offline checks, inspect the diff, commit/push when authorized,
  and verify the actual remote commit. Report any unfinished part explicitly.
- Run `python paper_reproduction/reproduce.py run` in an isolated copy before
  claiming the documented analyses reproduce. A rendering-only check, copied
  summary table, or successful checksum does not verify statistical reproduction.
- Write verification outputs separately from `CURRENT_PAPER`. Do not create
  PDFs or large duplicate raw API logs. Avoid spaCy or parallel heavy local
  jobs for the offline fit workflow.
- Changes to scientific choices require discussion, not silent adjustments to
  make a regression test pass. Document mismatches; do not overwrite references
  with newly generated answers merely to obtain a passing check.

## Steering-vector extension (`steering_extension/`, added 2026-10-10)

- Scope: mechanistic extension of the paper testing whether effort-exhortation (E) and
  role (R_id, R_act) steering vectors reproduce the paper's effort and role effects on
  Qwen3.5-9B (and later 27B). Design, decisions, and phase plan live in
  `steering_extension/PROPOSAL.md`; recipe justifications in
  `steering_extension/docs/literature_notes.md`. Read both before changing anything there.
- Separation: nothing under `CURRENT_PAPER/`, `paper_reproduction/`, or the offline
  reproduction path is touched by this work. All new outputs go to `outputs/steering/`
  (gitignored). Paper prompts are reused byte-for-byte via `steering_extension/local/common.py`;
  never edit the paper's prompt constants to suit the extension.
- Compute: GPU generation runs as SLURM jobs on Athena (Cyfronet) via
  `steering_extension/slurm/gpu_job.sbatch` (account `plgllmpsypath-gpu-a100`, partition
  `plgrid-gpu-a100`, 40 GB A100s); `steering_extension/vast/run_gpu.sh` is the equivalent
  for a plain GPU box. Keep both runners working. Weights and caches live under `$SCRATCH`.
- Environment: managed with `uv` (`steering_extension/remote/bootstrap.sh`); the steering
  extras are `steering_extension/requirements-remote.txt`. Qwen3.5 needs transformers main
  and the chat template flag `enable_thinking=False` to match the paper's `reasoning: none`.
- Paid calls: judging reuses the paper's unchanged `run_judging.py` with the paper's
  three-judge panel; coherence scoring uses one judge. Both are OpenRouter calls and require
  the PI's explicit per-phase authorization (current authorization: Phases 0-2 of the
  proposal, capped at $40 total). The key lives in `.env` / `.openrouter.txt` (gitignored);
  never commit or print it.
- Scientific conventions carried over: temperature 1.0, per-task max_tokens (essay 900,
  grant 1400, translation 600, postmortem 3000), blank system prompt, both presentation
  orders, judge flips collapse to ties, panel ties excluded, exact-binomial CIs. Steering
  doses are reported as fractions of the layer's RMS residual norm, never raw coefficients.
  Dose, layer, position-mode, and vector-recipe changes are scientific choices: discuss first.
- Phase gating: the proposal's phases run in order; Phase 4 (full grid) and beyond need a
  fresh go from the PI after the Phase 3 review.
