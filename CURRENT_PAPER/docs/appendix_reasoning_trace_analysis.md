# Appendix: Reasoning-Trace Analysis (essay high-low utility, reasoning enabled)

## Question and data

The main high-low experiment ran actors with reasoning disabled. We therefore
reran the essay condition with medium actor reasoning and requested readable
reasoning fields. This asks whether the high-low result remains null when actors
can reason about the success-contingent consequence, and whether explicit
reasoning about that consequence predicts panel preference.

The final dataset contains seven models, 300 pairs per model, 2,100 pairs and
4,200 generation outputs. Of these, 4,159 outputs contain readable
provider-returned reasoning text (2,080 high-side and 2,079 low-side). The text
may be a provider-generated reasoning summary rather than a model's complete
private chain of thought; every result below concerns only the returned text.

The reasoning-enabled high-low result remained null. The panel selected the
high side in 408 pairs, the low side in 431, and tied in 1,261. The primary
equal-cell estimate was 48.3% (two-stage bootstrap 95% CI: 43.1--53.3); the
corresponding pooled tie-excluded rate was 48.6%. No model passed the
familywise-adjusted positive-effect criterion. This experiment establishes a
null with reasoning enabled; it did not estimate a formal reasoning-on versus
reasoning-off interaction.

### Dataset reconciliation

An earlier trace summary was generated before the final Qwen3.5 run had been
fully incorporated. It contained 3,937 outputs, 3,896 readable traces, and 168
exact assigned-consequence mentions. The corrected dataset contains 4,200
outputs, 4,159 readable traces, and 253 exact mentions. The difference is 263
Qwen3.5 outputs, all with readable traces; 85 of those traces contain an exact
assigned-consequence mention. The portable trace dataset was built by streaming
the seven final run files directly from the archived raw runs. The registered
workflow fails unless exactly 4,200 outputs are recovered from that portable
dataset. The sorted output identifiers have SHA-256 digest
`0b8ebd6f8c0c07f84940966184f7b7fd863247639fddfaba08c466101684364f`.

## Lexical mention analysis

A deterministic lexical audit classified whether each readable trace mentioned
the competition/funding scaffold, generic consequence terms, the exact
consequence assigned to that output, or language explicitly identifying the
prompt as a hidden-context or evaluation setup. The complete audit found
ordinary scaffold language in 3,820 of 4,159 traces (91.8%): 90.9% of high-side
traces and 92.7% of low-side traces. Exact assigned-consequence mentions were
much rarer: 253 traces (6.1%), comprising 88 high-side and 165 low-side traces.

The performance analysis retained the 2,062 pairs with readable traces on both
sides. Its exact-consequence results were:

| Exact-consequence mention pattern | Pairs | High | Low | Tie | High win rate (95% exact CI) |
| --- | ---: | ---: | ---: | ---: | ---: |
| High side only | 66 | 7 | 17 | 42 | 29.2% (12.6--51.1) |
| Low side only | 143 | 32 | 22 | 89 | 59.3% (45.0--72.4) |
| Both sides | 22 | 2 | 4 | 16 | 33.3% (4.3--77.7) |
| Neither side | 1,831 | 358 | 382 | 1,091 | 48.4% (44.7--52.0) |

If explicit consequence reasoning amplified the utility manipulation, the high
side should win more often both when only the high side mentions its consequence
and when only the low side mentions its consequence. The low-only point estimate
is in that direction but is not distinguishable from chance (two-sided exact
`p = .220`); the high-only estimate points in the opposite direction and also
does not reach the conventional threshold (`p = .064`). Thus the complete data
do not show the predicted consistent amplification pattern. In the secondary
side-agnostic comparison, the sole mentioning side won 29 and lost 49 resolved
comparisons (37.2%, 95% CI: 26.5--48.9; unadjusted `p = .031`), which is more
consistent with distraction than improved performance but remains exploratory.

## Reproducible awareness-language audit

A separate deterministic regex audit over all 4,159 readable traces
separated ordinary scaffold recognition from stronger forms of awareness:

| Category | High | Low | Total | Percent of readable traces |
| --- | ---: | ---: | ---: | ---: |
| Ordinary scaffold awareness | 1,892 | 1,928 | 3,820 | 91.8% |
| Explicit evaluation/prompt awareness | 236 | 307 | 543 | 13.1% |
| Scenario disbelief or denied real-world causality | 65 | 112 | 177 | 4.3% |
| Strategic hidden-agenda reasoning | 184 | 160 | 344 | 8.3% |
| Refusal or resistance | 13 | 44 | 57 | 1.4% |
| Any category beyond ordinary awareness | 384 | 416 | 800 | 19.2% |

These categories overlap. Their role is descriptive: regex matches identify
language in the returned traces, not latent mental states. Exploratory
pair-level tests did not show that such language improved the matching side's
performance. Because several categories and subgroup tests were examined, their
unadjusted p-values should not be treated as confirmatory evidence.

## Manual audit of exact mentions

Every one of the 253 exact-consequence mentions has a manual code. The initial
168 records were read in full. After Qwen3.5 completed, the 85 omitted records
were manually reviewed using their prompt-analysis sections and all contextual
passages containing evaluation, disbelief, hidden-goal, or refusal language.
The audit found explicit evaluation awareness in 154/253 exact-mention traces
(60.9%), prompt-injection or jailbreak framing in 143/253 (56.5%), scenario
disbelief in 47/253 (18.6%), and strategic hidden-agenda reasoning in 16/253
(6.3%). These are rates within the selected exact-mention subset and must not be
generalized to all traces.

## LLM stance classification

A Claude workflow classified 2,620 lexically gated traces using four
non-exclusive flags. The classification ran in 66 batches of at most 40 traces
using the recorded model identifier `claude-opus-4-8[1m]` at medium reasoning
effort. The exact prompt, lexical gate, batch design, response schema, and fixed
labels are preserved in the repository; see
`analysis_specs/reasoning_trace_stance_classifier.md`.

Of the 2,620 classified traces, 1,422 received at least one stance flag:

| Saved stance label | n | % of stance-takers | High | Low |
| --- | ---: | ---: | ---: | ---: |
| Believes | 185 | 13.0% | 101 | 84 |
| Disbelieves | 96 | 6.8% | 36 | 60 |
| Suspicious | 675 | 47.5% | 285 | 390 |
| Dismisses | 931 | 65.5% | 447 | 484 |

The flags overlap. Four records are marked as identifier mismatches in the saved
workflow output; the summary uses their corrected source-side metadata and
retains that warning.

Conditioning on the saved high-side label also provides no evidence that stated
belief improves performance:

| High-side saved label | High | Low | Tie | Resolved | High win rate (95% exact CI) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Believes | 18 | 24 | 59 | 42 | 42.9% (27.7--59.0) |
| Disbelieves | 8 | 12 | 16 | 20 | 40.0% (19.1--63.9) |
| Suspicious | 44 | 72 | 169 | 116 | 37.9% (29.1--47.4) |
| Dismisses | 76 | 97 | 274 | 173 | 43.9% (36.4--51.7) |
| Neither believes nor disbelieves among classified traces | 227 | 233 | 707 | 460 | 49.3% (44.7--54.0) |

The belief subset is small and heavily concentrated in GLM-5.1, so these are
correlational descriptive results rather than a causal test of belief.

### Sensitivity analysis excluding suspicion or disbelief

We also excluded every comparison in which either returned actor trace was
classified as expressing suspicion about the setup or explicit disbelief in
its real-world causality. The outcome is the panel's high-side win rate after
ties are excluded. Intervals are exact 95% familywise confidence intervals
across the seven model estimates (Bonferroni-adjusted Clopper-Pearson
intervals); significance tests are one-sided exact binomial tests with Holm
correction across models.

| Model | Pairs removed | Retained pairs | Resolved | Full win rate [FWER 95% CI] | After exclusion [FWER 95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek V3.2 | 11 | 289 | 145 | 48.0% [36.9%, 59.2%] | 47.6% [36.3%, 59.0%] |
| GPT-5.4 mini | 8 | 292 | 79 | 49.4% [34.3%, 64.6%] | 49.4% [34.1%, 64.7%] |
| GLM-5.1 | 50 | 250 | 84 | 48.0% [34.6%, 61.7%] | 48.8% [34.0%, 63.8%] |
| Kimi K2.5 | 64 | 236 | 109 | 45.8% [34.5%, 57.4%] | 42.2% [29.7%, 55.5%] |
| MiMo V2.5 Pro | 43 | 257 | 123 | 56.7% [45.4%, 67.5%] | 56.1% [43.6%, 68.1%] |
| Qwen3.5 9B | 1,757 | 163 | 63 | 48.9% [44.0%, 53.8%] | 49.2% [32.1%, 66.4%] |
| Qwen3.6 Plus | 47 | 253 | 78 | 50.0% [36.1%, 63.9%] | 48.7% [33.4%, 64.2%] |

The filter removes 1,980 of 3,720 comparisons. All seven model estimates change
by no more than 3.6 percentage points. For Qwen3.5, the expanded estimate changes
from 48.9% to 49.2%; the filter retains 163 of 1,920 comparisons and leaves 63
resolved comparisons. No filtered model is significantly above chance. Thus
the null result is not explained by comparisons in which the returned trace
expresses suspicion or disbelief.

This is a sensitivity analysis rather than a replacement causal estimand:
suspicion and disbelief are post-treatment responses to the prompt, so
conditioning on them can introduce selection bias. For the original six model
runs, saved LLM labels exist only for traces selected by the documented lexical
gate; gate-negative traces count as having no recorded suspicion or disbelief.
The Qwen3.5 row incorporates the fixed 1,620-comparison follow-up and its
preserved local stance labels, combined with the original 300 comparisons.

### Targeted Qwen3.5 follow-up

Because the original Qwen3.5 exclusion estimate was based on only 15 resolved
comparisons, we ran a fixed essay-only follow-up containing 1,620 additional
comparisons. Combined with the archived 300, the design contains 1,920
comparisons, balances all 80 utility pairs per domain over six distinct essay
topics, and does not duplicate a utility-pair/topic combination.

The apparent Qwen reversal did not replicate. In the new cohort alone, the
high-utility side won 322 resolved comparisons and lost 319, for a 50.2% win
rate (exact 95% CI: 46.3--54.2). After excluding every comparison with any
recorded suspicion or disbelief, it won 20 and lost 28, for a 41.7% win rate
(27.6--56.8). In the combined 1,920-comparison dataset, the corresponding
results are:

| Qwen3.5 sample | Pairs | High | Low | Tie | High win rate (exact 95% CI) | Crossed pair/topic bootstrap 95% CI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All comparisons | 1,920 | 371 | 388 | 1,161 | 48.9% (45.3--52.5) | 43.1--54.4 |
| Excluding recorded disbelief | 1,280 | 257 | 243 | 780 | 51.4% (46.9--55.9) | 44.3--58.6 |
| Excluding recorded suspicion or disbelief | 163 | 31 | 32 | 100 | 49.2% (36.4--62.1) | 28.1--71.8 |

The final stance analysis uses only locally produced Opus labels: 577/600
archived Qwen traces and 3,138/3,240 follow-up traces have returned labels. As
in the original analysis, traces without a returned label count as having no
recorded positive flag. Requiring returned labels on both sides produces the
same conclusion: after excluding suspicion or disbelief, the high-side win
rate is 48.9% (23 wins, 24 losses; exact 95% CI: 34.1--63.9). No labels from
the incomplete API-Opus workflow are used.

This follow-up removes the only conspicuous model-level reversal in the
original sensitivity table. The retained sample remains sparse because Qwen3.5
frequently describes the scenario as suspicious and the judging panel often
ties, but neither the full sample nor either exclusion analysis supports a
positive high-utility effect.

## Bottom line

The reasoning-enabled replication remains null even though the returned traces
usually represent the incentive scaffold. Explicit discussion of the assigned
consequence does not produce the directional pattern expected if reasoning
amplifies motivation: discussion on the high side is not associated with better
high-side performance, while the suggestive low-side pattern is imprecise. The
sensitivity analysis further shows that removing comparisons with recorded
suspicion or disbelief does not make the utility effect positive. The evidence
therefore does not support scenario disbelief as an explanation for the null.

## Reproduction and provenance

- Raw generation runs: `outputs/api_runs_archive_2026-07-17.tar.gz` (seven named
  archive members recorded in
  `outputs/analysis/reasoning_trace_raw_archive_provenance.json`).
- Portable local-analysis input:
  `outputs/analysis/reasoning_trace_inputs.jsonl.gz` (6.6 MB; the provenance
  file records its SHA-256 digest).
- Complete lexical audit and provenance:
  `outputs/analysis/reasoning_incentive_mentions__success_only_*`.
- Pair-level mention analysis:
  `outputs/analysis/reasoning_mentions_vs_performance__both_traces_required_*`.
- Complete regex audit: `outputs/analysis/reasoning_trace_awareness_regex_*`.
- Manual codebooks: `analysis_specs/reasoning_trace_manual_codes_initial_168.csv`
  and `analysis_specs/reasoning_trace_manual_codes_addendum.csv`.
- Compiled manual audit:
  `outputs/analysis/reasoning_trace_manual_audit_exact_consequence_mentions.*`.
- Saved stance-label summary:
  `outputs/analysis/reasoning_trace_saved_stance_labels_*`.
  The 95 KB `reasoning_trace_saved_stance_labels.jsonl.gz` file contains the
  saved labels without duplicating trace text.
- Classifier protocol:
  `analysis_specs/reasoning_trace_stance_classifier.md`.
- Suspicion/disbelief exclusion analysis:
  `CURRENT_PAPER/results/reasoning_trace/reasoning_suspicion_disbelief_exclusion.*`.
- Targeted Qwen3.5 follow-up:
  `CURRENT_PAPER/results/reasoning_trace/qwen35_reasoning_stance_summary.*` and
  `CURRENT_PAPER/results/reasoning_trace/qwen35_reasoning_stance_label_audit.json`.
- Scripts: `analyze_highlow_reasoning.py`,
  `analyze_reasoning_incentive_mentions.py`,
  `analyze_reasoning_mentions_vs_performance.py`,
  `analyze_reasoning_trace_awareness.py`, and
  `analyze_saved_reasoning_stance_labels.py`, and
  `analyze_reasoning_suspicion_exclusion.py`.
- Registered local-only workflow: `paper_reproduction/workflow.yaml`, step
  `reasoning_appendix`. It makes no API calls.
