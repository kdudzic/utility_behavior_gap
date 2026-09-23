# Offline Paper Reproduction

## Commands

After installing `requirements.txt` in Python 3.13, from the repo root:

```bash
python paper_reproduction/reproduce.py audit
python paper_reproduction/reproduce.py run
```

To run one part, use `--step outcomes`, `--step trends`, `--step features`, or
`--step reasoning`. Multiple `--step` arguments are allowed. The default runs
all four. Each writes to its own directory under `outputs/reproduced/`.
`verification.json` records completed steps and numerical checks. Mismatches
raise errors; missing files are not silently treated as null results.

The runner blocks network connections, limits numerical libraries to one
thread, does not load spaCy, and makes no model calls. Outputs are PNG, CSV,
Markdown, and LaTeX, not PDFs. Accepted artifacts are never overwritten.
Progress appears at analysis/contrast boundaries; verbose diagnostics go to
small per-analysis logs.

## What Is Recomputed

| Step | Input | Computation |
| --- | --- | --- |
| outcomes | Frozen pair-level panel outcomes | Model/task win rates, exact adjusted intervals, lollipops, utility-domain breakouts, unified overall/task bootstrap intervals |
| trends | Outcomes, assigned utilities, item identifiers | Utility-gap and absolute-utility regressions, binned intervals, two-panel figure |
| features | Generic measurements and saved rubric ratings | All length-controlled gap and panel-association fits, four feature tables, directionality |
| reasoning | Traces, outcomes, saved local labels, Qwen follow-up | Mention/awareness analyses, reasoning-on lollipop, follow-up estimates, suspicion exclusion |

This reproduces analyses **from stored measurements and judgments**. It does
not claim that stochastic API calls regenerate the same essays or votes, or
that fit checks independently validate the original LLM judgments. Prompts,
collection code, rubric definitions, saved labels, IDs, and provenance are
preserved separately. Raw API caches are not a hidden dependency.

## Statistical Conventions

- Win rate excludes panel ties, not selected individual judge votes.
- Model/task figures use exact binomial intervals with Bonferroni family-wise
  95% coverage across 28 cells; single-task figures use seven. Holm-adjusted
  p-values are supplementary, not a name for these intervals.
- Overall/task summaries use the same two-stage equal-cell bootstrap: resample
  cells, then resolved pair outcomes within cells. Utility comparisons use
  actor/task/domain cells; direct, role, and harmful-empty use actor/task cells.
  There are 5,000 draws and fixed seeds. These are nominal 95% aggregate
  bootstrap intervals, not the figures' family-wise intervals. Historical
  aggregate files with other conventions are not primary summaries.
- Feature fits retain the existing length-control and exclusion rules. Missing
  classifier labels are reported as unclassified, not clean. The historical
  moral-specific classifier filename does not restrict exclusions by condition.
- The accepted direct table uses its documented 0.20 standardized-gap display
  threshold, including grant Flesch-Kincaid grade. Role and harmful tables use
  the later 0.25 threshold in both directions. Utility reports the direct
  table's dimensions, including nonsignificant estimates. These are explicit
  reproduction parameters, not newly selected rules.
- Feature-directionality Wilson intervals describe the included feature/task
  rows, not independent-feature or trial-level causal inference.

## Provenance and Updates

`data/processed/provenance.json` records source paths, checksums, and export
transformations. Compression-only entries retain the exact source bytes;
selected-column entries retain every row in order. Historical absolute paths
inside metadata identify original runs; the runner does not open those paths.
Current vocabulary measurements are included because the older large feature
CSV in `CURRENT_PAPER/features/` predates MATTR and rare-word rate.

`export_inputs.py` is a maintainer export tool, not a reader prerequisite.
Updating the research checkout does not update this repo automatically. To
publish: export the affected inputs, retain provenance, run checks in isolation,
review the diff, commit, push, and verify the remote commit. A private backup
does not complete this publication step.

The older `consolidated_workflow/` remains historical. Its aggregate routine is
not the paper's bootstrap implementation; use this entry point instead.

The GitHub workflow `.github/workflows/paper-reproduction.yml` runs the offline
checks on pushes and pull requests without model credentials. A future change
that alters the frozen results therefore fails verification rather than silently
publishing new numbers.
