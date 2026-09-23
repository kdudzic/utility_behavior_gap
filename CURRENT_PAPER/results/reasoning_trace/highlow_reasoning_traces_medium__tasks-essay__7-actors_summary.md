# High-Low Reasoning-Medium Analysis

Exploratory analysis of high-low utility runs with actor reasoning enabled.
These outputs are not part of the canonical reasoning-off analysis.

Counting rule: all six order-specific judge votes are required for a pair; each judge's two order votes are collapsed to one judge verdict, then the three judge verdicts determine the panel outcome.

- included pairs: 2100
- model-task cells: 7
- Holm-positive model-task cells: 0
- audit statuses: `{'included': 2100}`

## Overall

| scope | pairs | high_wins | low_wins | ties | n_excluding_ties | high_win_rate_excluding_ties | pooled_high_win_rate_excluding_ties | bootstrap95_ci_low | bootstrap95_ci_high | aggregate_cells | bootstrap_seed | bootstrap_iterations | net_score_all_pairs | mean_high_reasoning_tokens | mean_low_reasoning_tokens | mean_reasoning_tokens_high_minus_low | mean_high_reasoning_trace_chars | mean_low_reasoning_trace_chars | mean_reasoning_trace_chars_high_minus_low | mean_words_high_minus_low | task | task_label | actor | actor_label | domain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| overall | 2100 | 408 | 431 | 1261 | 839 | 0.483 | 0.486 | 0.431 | 0.533 | 28 | 20260615 | 5000 | -0.011 | 1489.260 | 1514.582 | -25.323 | 12692.310 | 12885.402 | -193.092 | -0.380 |  |  |  |  |  |

## Model x Task

| actor_label | task_label | pairs | high_wins | low_wins | ties | high_win_rate_excluding_ties | fwer95_ci_low | fwer95_ci_high | holm_p | holm_positive | mean_reasoning_tokens_high_minus_low | mean_reasoning_trace_chars_high_minus_low | mean_words_high_minus_low |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DeepSeek V3.2 | Essay writing | 300 | 72 | 78 | 150 | 0.480 | 0.369 | 0.592 | 1.000 | FALSE | -13.580 | -168.597 | -1.947 |
| GLM-5.1 | Essay writing | 300 | 49 | 53 | 198 | 0.480 | 0.346 | 0.617 | 1.000 | FALSE | -5.487 | -180.300 | -1.263 |
| GPT-5.4 mini | Essay writing | 300 | 40 | 41 | 219 | 0.494 | 0.343 | 0.646 | 1.000 | FALSE | 6.417 | 80.610 | -0.587 |
| Kimi K2.5 | Essay writing | 300 | 65 | 77 | 158 | 0.458 | 0.345 | 0.574 | 1.000 | FALSE | -49.257 | -363.040 | 1.167 |
| MiMo V2.5 Pro | Essay writing | 300 | 85 | 65 | 150 | 0.567 | 0.454 | 0.675 | 0.422 | FALSE | -8.060 | -101.847 | 4.760 |
| Qwen3.5 9B | Essay writing | 300 | 49 | 69 | 182 | 0.415 | 0.295 | 0.543 | 1.000 | FALSE | -143.053 | -1135.707 | -2.907 |
| Qwen3.6 Plus | Essay writing | 300 | 48 | 48 | 204 | 0.500 | 0.361 | 0.639 | 1.000 | FALSE | 35.760 | 517.237 | -1.883 |
