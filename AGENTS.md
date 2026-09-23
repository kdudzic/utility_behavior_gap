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
