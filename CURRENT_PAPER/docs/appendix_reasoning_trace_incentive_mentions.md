# Appendix Finding: Reasoning About Incentives Does Not Amplify the Utility Effect

This is the concise pair-level report. The consolidated methods, awareness
audit, manual review, and saved exploratory stance-label analysis are documented
in `appendix_reasoning_trace_analysis.md`.

## Question

If explicit incentive reasoning amplifies the utility contrast, then the
high-utility output should win more often both when only the high side discusses
its assigned consequence and when only the low side discusses its assigned
consequence. The latter prediction follows because reasoning about the less
preferred consequence should reduce low-side effort.

## Complete dataset

The reasoning-enabled essay run contains 2,100 pairs and 4,200 outputs across
seven models. Readable provider-returned reasoning text was available for 4,159
outputs. The pair-level mention analysis requires readable text on both sides,
leaving 2,062 pairs (399 high wins, 425 low wins, and 1,238 ties).

The deterministic lexical audit found ordinary competition/funding scaffold
language in 3,820/4,159 traces (91.8%). Exact mentions of the consequence
assigned to that output were uncommon: 253/4,159 traces (6.1%; 88 high-side and
165 low-side).

## Exact-consequence results

| Mention pattern | Pairs | High wins | Low wins | Ties | High win rate excluding ties (95% exact CI) | Net high-minus-low score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| High side only | 66 | 7 | 17 | 42 | 29.2% (12.6--51.1) | -15.2 pp |
| Low side only | 143 | 32 | 22 | 89 | 59.3% (45.0--72.4) | +7.0 pp |
| Both sides | 22 | 2 | 4 | 16 | 33.3% (4.3--77.7) | -9.1 pp |
| Neither side | 1,831 | 358 | 382 | 1,091 | 48.4% (44.7--52.0) | -1.3 pp |

The low-only point estimate is in the predicted direction but is not
distinguishable from chance (`p = .220`). The high-only estimate points in the
opposite direction and is also imprecise (`p = .064`). The complete data
therefore do not show the consistent directional pattern predicted by incentive
amplification. Broader target-term and meta-recognition categories were also
null in the side-specific performance analysis.

## Interpretation and scope

The result is not that noticing the incentive is rare: ordinary scaffold
recognition appears in approximately 92% of readable traces. Rather, explicit
discussion of the assigned consequence does not predict the pattern expected if
reasoning caused actors to work harder for higher-utility outcomes or sandbag
lower-utility outcomes.

This is exploratory appendix evidence. The analyses concern readable returned
reasoning fields, which may contain provider-generated summaries rather than a
model's complete private chain of thought. Exact binomial intervals and p-values
in this targeted analysis are unadjusted.

## Reproduction

- `src/utility_behavior_gap/scripts/analyze_reasoning_incentive_mentions.py`
- `src/utility_behavior_gap/scripts/analyze_reasoning_mentions_vs_performance.py`
- `outputs/analysis/reasoning_incentive_mentions__success_only_provenance.json`
- `outputs/analysis/reasoning_incentive_mentions__success_only_per_output.csv`
- `outputs/analysis/reasoning_mentions_vs_performance__both_traces_required_*`
