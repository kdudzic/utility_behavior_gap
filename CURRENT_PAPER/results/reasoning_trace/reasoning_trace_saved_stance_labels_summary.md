# Saved Reasoning-Trace Stance Labels

This is a reproducible summary of the fixed LLM-classification artifact. It makes no API calls.

- lexically gated traces classified: 2620
- traces assigned at least one non-exclusive stance: 1422
- rows marked `flag_mismatch`: 4

## Classifier provenance

The classification used a 66-batch Claude workflow at medium reasoning effort (`wf_f3a7fe17-901`) and the recorded model identifier `claude-opus-4-8[1m]`. The exact prompt, lexical gate, batch design, response schema, and preserved inputs are documented in `analysis_specs/reasoning_trace_stance_classifier.md`.

The four `flag_mismatch` rows retain their saved labels and corrected source metadata. Counts below use the corrected `cond` field in the saved artifact.

## Stance counts

| stance | n | percent_of_stance_takers | high | low | flag_mismatch_rows |
| --- | --- | --- | --- | --- | --- |
| believes | 185 | 13.010 | 101 | 84 | 0 |
| disbelieves | 96 | 6.751 | 36 | 60 | 2 |
| suspicious | 675 | 47.468 | 285 | 390 | 4 |
| dismisses | 931 | 65.471 | 447 | 484 | 3 |

Flags are non-exclusive, so percentages do not sum to 100%.

## Panel outcomes conditioned on the high-side trace

| high_side_trace_category | pairs | high_wins | low_wins | ties | n_excluding_ties | high_win_rate_excluding_ties | exact95_ci_low | exact95_ci_high | two_sided_binomial_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| believes | 101 | 18 | 24 | 59 | 42 | 0.429 | 0.277 | 0.590 | 0.441 |
| disbelieves | 36 | 8 | 12 | 16 | 20 | 0.400 | 0.191 | 0.639 | 0.503 |
| suspicious | 285 | 44 | 72 | 169 | 116 | 0.379 | 0.291 | 0.474 | 0.012 |
| dismisses | 447 | 76 | 97 | 274 | 173 | 0.439 | 0.364 | 0.517 | 0.128 |
| neither_believes_nor_disbelieves_among_classified | 1167 | 227 | 233 | 707 | 460 | 0.493 | 0.447 | 0.540 | 0.816 |
| all_pairs | 2100 | 408 | 431 | 1261 | 839 | 0.486 | 0.452 | 0.521 | 0.448 |

Confidence intervals and p-values are unadjusted exact binomial quantities and are descriptive exploratory analyses.
