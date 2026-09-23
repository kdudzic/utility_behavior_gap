# Sensitivity Analysis Excluding Suspicion or Disbelief

A comparison is excluded when either returned actor reasoning trace was classified as expressing suspicion about the setup or explicit disbelief in its real-world causality. The outcome is the panel's high-side win rate after ties are excluded. Intervals are exact 95% familywise confidence intervals across the seven model estimates (Bonferroni-adjusted Clopper-Pearson intervals); significance tests are one-sided exact binomial tests with Holm correction across models.

| Model | Pairs removed | Retained pairs | Resolved | Full win rate [FWER 95% CI] | After exclusion [FWER 95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek V3.2 | 11 | 289 | 145 | 48.0% [36.9%, 59.2%] | 47.6% [36.3%, 59.0%] |
| GPT-5.4 mini | 8 | 292 | 79 | 49.4% [34.3%, 64.6%] | 49.4% [34.1%, 64.7%] |
| GLM-5.1 | 50 | 250 | 84 | 48.0% [34.6%, 61.7%] | 48.8% [34.0%, 63.8%] |
| Kimi K2.5 | 64 | 236 | 109 | 45.8% [34.5%, 57.4%] | 42.2% [29.7%, 55.5%] |
| MiMo V2.5 Pro | 43 | 257 | 123 | 56.7% [45.4%, 67.5%] | 56.1% [43.6%, 68.1%] |
| Qwen3.5 9B | 1757 | 163 | 63 | 48.9% [44.0%, 53.8%] | 49.2% [32.1%, 66.4%] |
| Qwen3.6 Plus | 47 | 253 | 78 | 50.0% [36.1%, 63.9%] | 48.7% [33.4%, 64.2%] |

The filter removes 1,980 of 3,720 comparisons. Across all seven models, the filtered point estimate changes by at most 3.6 percentage points. The expanded Qwen3.5 estimate changes from 48.9% to 49.2%; its filter retains 163 of 1,920 comparisons and leaves 63 resolved comparisons. No filtered model is significantly above chance under the familywise analysis.

This is a sensitivity analysis, not a replacement causal estimand: suspicion and disbelief are post-treatment responses to the prompt, so conditioning on them can introduce selection bias. For the original six model runs, saved LLM labels exist only for traces selected by the documented lexical gate; gate-negative traces count as having no recorded suspicion or disbelief. The Qwen3.5 row incorporates the fixed 1,620-comparison follow-up and its preserved local stance labels, combined with the original 300 comparisons.
