# Reasoning Mentions vs Performance

Pair-level analysis joining returned readable reasoning-trace incentive mentions to panel outcomes.

Primary filter: both high and low outputs must have readable trace text.

- included pairs: 2062
- high wins: 399
- low wins: 425
- ties: 1238

## Directional Test

Among pairs where exactly one side mentions the feature, this asks whether the mentioning side wins more often than the non-mentioning side, excluding ties.

| feature | asymmetric_pairs | mention_side_wins | mention_side_loses | ties | n_excluding_ties | mention_side_win_rate_excluding_ties | exact95_ci_low | exact95_ci_high | net_alignment_score_all_pairs | two_sided_binomial_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mentions_any_incentive | 164 | 18 | 30 | 116 | 48 | 0.375 | 0.240 | 0.526 | -0.073 | 0.111 |
| mentions_scaffold | 169 | 19 | 33 | 117 | 52 | 0.365 | 0.236 | 0.510 | -0.083 | 0.070 |
| mentions_target_terms | 350 | 74 | 68 | 208 | 142 | 0.521 | 0.436 | 0.606 | 0.017 | 0.675 |
| mentions_exact_assigned_target | 209 | 29 | 49 | 131 | 78 | 0.372 | 0.265 | 0.489 | -0.096 | 0.031 |
| mentions_meta_recognition | 302 | 72 | 68 | 162 | 140 | 0.514 | 0.428 | 0.600 | 0.013 | 0.800 |

## Pattern Summary

| feature | mention_pattern | pairs | high_wins | low_wins | ties | n_excluding_ties | high_win_rate_excluding_ties | exact95_ci_low | exact95_ci_high | two_sided_binomial_p | net_score_all_pairs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mentions_any_incentive | both | 1823 | 367 | 389 | 1067 | 756 | 0.485 | 0.449 | 0.522 | 0.445 | -0.012 |
| mentions_any_incentive | high_only | 66 | 6 | 14 | 46 | 20 | 0.300 | 0.119 | 0.543 | 0.115 | -0.121 |
| mentions_any_incentive | low_only | 98 | 16 | 12 | 70 | 28 | 0.571 | 0.372 | 0.755 | 0.572 | 0.041 |
| mentions_any_incentive | neither | 75 | 10 | 10 | 55 | 20 | 0.500 | 0.272 | 0.728 | 1.000 | 0.000 |
| mentions_scaffold | both | 1814 | 365 | 387 | 1062 | 752 | 0.485 | 0.449 | 0.522 | 0.444 | -0.012 |
| mentions_scaffold | high_only | 67 | 7 | 16 | 44 | 23 | 0.304 | 0.132 | 0.529 | 0.093 | -0.134 |
| mentions_scaffold | low_only | 102 | 17 | 12 | 73 | 29 | 0.586 | 0.389 | 0.765 | 0.458 | 0.049 |
| mentions_scaffold | neither | 79 | 10 | 10 | 59 | 20 | 0.500 | 0.272 | 0.728 | 1.000 | 0.000 |
| mentions_target_terms | both | 821 | 141 | 169 | 511 | 310 | 0.455 | 0.398 | 0.512 | 0.125 | -0.034 |
| mentions_target_terms | high_only | 172 | 43 | 33 | 96 | 76 | 0.566 | 0.447 | 0.679 | 0.302 | 0.058 |
| mentions_target_terms | low_only | 178 | 35 | 31 | 112 | 66 | 0.530 | 0.403 | 0.654 | 0.712 | 0.022 |
| mentions_target_terms | neither | 891 | 180 | 192 | 519 | 372 | 0.484 | 0.432 | 0.536 | 0.569 | -0.013 |
| mentions_exact_assigned_target | both | 22 | 2 | 4 | 16 | 6 | 0.333 | 0.043 | 0.777 | 0.688 | -0.091 |
| mentions_exact_assigned_target | high_only | 66 | 7 | 17 | 42 | 24 | 0.292 | 0.126 | 0.511 | 0.064 | -0.152 |
| mentions_exact_assigned_target | low_only | 143 | 32 | 22 | 89 | 54 | 0.593 | 0.450 | 0.724 | 0.220 | 0.070 |
| mentions_exact_assigned_target | neither | 1831 | 358 | 382 | 1091 | 740 | 0.484 | 0.447 | 0.520 | 0.398 | -0.013 |
| mentions_meta_recognition | both | 1212 | 222 | 247 | 743 | 469 | 0.473 | 0.427 | 0.520 | 0.268 | -0.021 |
| mentions_meta_recognition | high_only | 151 | 33 | 34 | 84 | 67 | 0.493 | 0.368 | 0.618 | 1.000 | -0.007 |
| mentions_meta_recognition | low_only | 151 | 34 | 39 | 78 | 73 | 0.466 | 0.348 | 0.586 | 0.640 | -0.033 |
| mentions_meta_recognition | neither | 548 | 110 | 105 | 333 | 215 | 0.512 | 0.443 | 0.580 | 0.785 | 0.009 |

## Correlations

| feature | pairs | n_asymmetric | pearson_r_mention_diff_vs_panel_score | pearson_p | spearman_r_mention_diff_vs_panel_score | spearman_p |
| --- | --- | --- | --- | --- | --- | --- |
| mentions_any_incentive | 2062 | 164 | -0.034 | 0.125 | -0.034 | 0.125 |
| mentions_scaffold | 2062 | 169 | -0.039 | 0.078 | -0.039 | 0.078 |
| mentions_target_terms | 2062 | 350 | 0.011 | 0.617 | 0.011 | 0.624 |
| mentions_exact_assigned_target | 2062 | 209 | -0.051 | 0.021 | -0.051 | 0.021 |
| mentions_meta_recognition | 2062 | 302 | 0.008 | 0.716 | 0.008 | 0.713 |