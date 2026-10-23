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

- **Start here:** read `steering_extension/HANDOFF.md` before doing anything in `steering_extension/`.
  It holds the current state, results, open decisions, and the PI's working preferences, and replaces
  conversation history across machines. At the end of every working session, update its session log
  and any changed section, then commit and push. Keep it free of keys, account details, and personal data.

- Scope: mechanistic extension of the paper testing whether effort-exhortation (E) and
  role (R_id, R_act) steering vectors reproduce the paper's effort and role effects on
  Qwen3.5-9B (and later 27B). Design, decisions, and phase plan live in
  `steering_extension/PROPOSAL.md`; recipe justifications in
  `steering_extension/docs/literature_notes.md`. Read both before changing anything there.
- Separation: nothing under `CURRENT_PAPER/`, `paper_reproduction/`, or the offline
  reproduction path is touched by this work. All new outputs go to `outputs/steering/`
  (gitignored). Paper prompts are reused byte-for-byte via `steering_extension/local/common.py`;
  never edit the paper's prompt constants to suit the extension.
- Compute: since 2026-10-17 GPU generation runs on a rented vast.ai instance driven from the
  laptop by `steering_extension/vast/vast.py` (`search/up/push/bootstrap/run/pull/down`; state in
  `outputs/steering/vast/instance.json`). The account is the shared SPAR team account: never destroy
  instances you did not create, and `down` yours when a session ends (billing runs until then).
  `steering_extension/slurm/gpu_job.sbatch` is the Athena (Cyfronet) equivalent (account
  `plgllmpsypath-gpu-a100`, partition `plgrid-gpu-a100`, 40 GB A100s); keep both runners working.
- Environment: managed with `uv` (`steering_extension/remote/bootstrap.sh`); the steering
  extras are `steering_extension/requirements-remote.txt`. Qwen3.5 needs transformers main
  and the chat template flag `enable_thinking=False` to match the paper's `reasoning: none`.
- Paid calls: judging reuses the paper's unchanged `run_judging.py` with the paper's
  three-judge panel; coherence scoring uses one judge. Both are OpenRouter calls and require
  the PI's explicit per-phase authorization (current authorization: Phases 0-2 of the
  proposal, capped at $40 total). Keys live in `~/.config/utility_behavior_gap/secrets.env` (canonical,
  outside the tree; see `steering_extension/README.md`, Secrets), with the gitignored in-repo files
  `steering_extension/spar_*.txt`, `.openrouter.txt`, `.env` as fallbacks; never commit or print them.
  `python -m steering_extension.local.keys --check` audits this; a pre-commit hook blocks key material.
- Scientific conventions carried over: temperature 1.0, per-task max_tokens (essay 900,
  grant 1400, postmortem 3000; translation is excluded from the extension since 2026-10-17), blank system prompt, both presentation
  orders, judge flips collapse to ties, panel ties excluded, exact-binomial CIs. Steering
  doses are reported as fractions of the layer's RMS residual norm, never raw coefficients.
  Dose, layer, position-mode, and vector-recipe changes are scientific choices: discuss first.
- Phase gating: the proposal's phases run in order; Phase 4 (full grid) and beyond need a
  fresh go from the PI after the Phase 3 review.
