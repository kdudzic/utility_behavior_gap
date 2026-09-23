# Qwen3.5 Reasoning-Stance Follow-up

The fixed follow-up adds 1,620 comparisons to the archived 300. The combined design presents every one of 80 utility pairs per domain on six distinct essay topics and contains 16 comparisons in every topic-by-domain cell.

Win rates exclude panel ties. Exact 95% intervals are the targeted Qwen-only intervals. The combined overall rows also report a crossed utility-pair/topic bootstrap interval. Seven-model familywise intervals remain available in the CSV for comparison with the original lollipop figure.

Suspicion/disbelief exclusions are post-treatment sensitivity analyses, not causal estimands.
All stance labels in this analysis were produced locally. No API-Opus classifications were used. The archived cohort has 577/600 classified traces; the follow-up has 3138/3240. As in the original appendix, the primary exclusion rows treat traces without a returned classifier label as having no recorded positive flag. Rows prefixed `classified_` instead require both traces in a pair to have returned labels.

## Overall

| cohort | sample | pairs | high_wins | low_wins | ties | resolved | high_win_rate | exact95_ci_low | exact95_ci_high | crossed_cluster95_ci_low | crossed_cluster95_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| archived_300 | all_pairs | 300 | 49 | 69 | 182 | 118 | 0.415 | 0.325 | 0.510 |  |  |
| archived_300 | both_traces_classified | 278 | 44 | 62 | 172 | 106 | 0.415 | 0.320 | 0.515 |  |  |
| archived_300 | exclude_explicit_disbelief | 227 | 37 | 50 | 140 | 87 | 0.425 | 0.320 | 0.536 |  |  |
| archived_300 | exclude_suspicion_or_disbelief | 27 | 11 | 4 | 12 | 15 | 0.733 | 0.449 | 0.922 |  |  |
| archived_300 | classified_exclude_explicit_disbelief | 206 | 32 | 43 | 131 | 75 | 0.427 | 0.313 | 0.546 |  |  |
| archived_300 | classified_exclude_suspicion_or_disbelief | 22 | 9 | 4 | 9 | 13 | 0.692 | 0.386 | 0.909 |  |  |
| followup_1620 | all_pairs | 1620 | 322 | 319 | 979 | 641 | 0.502 | 0.463 | 0.542 |  |  |
| followup_1620 | both_traces_classified | 1520 | 303 | 300 | 917 | 603 | 0.502 | 0.462 | 0.543 |  |  |
| followup_1620 | exclude_explicit_disbelief | 1053 | 220 | 193 | 640 | 413 | 0.533 | 0.483 | 0.582 |  |  |
| followup_1620 | exclude_suspicion_or_disbelief | 136 | 20 | 28 | 88 | 48 | 0.417 | 0.276 | 0.568 |  |  |
| followup_1620 | classified_exclude_explicit_disbelief | 964 | 205 | 175 | 584 | 380 | 0.539 | 0.488 | 0.590 |  |  |
| followup_1620 | classified_exclude_suspicion_or_disbelief | 93 | 14 | 20 | 59 | 34 | 0.412 | 0.246 | 0.593 |  |  |
| combined_1920 | all_pairs | 1920 | 371 | 388 | 1161 | 759 | 0.489 | 0.453 | 0.525 | 0.431 | 0.544 |
| combined_1920 | both_traces_classified | 1798 | 347 | 362 | 1089 | 709 | 0.489 | 0.452 | 0.527 | 0.431 | 0.548 |
| combined_1920 | exclude_explicit_disbelief | 1280 | 257 | 243 | 780 | 500 | 0.514 | 0.469 | 0.559 | 0.443 | 0.586 |
| combined_1920 | exclude_suspicion_or_disbelief | 163 | 31 | 32 | 100 | 63 | 0.492 | 0.364 | 0.621 | 0.281 | 0.718 |
| combined_1920 | classified_exclude_explicit_disbelief | 1170 | 237 | 218 | 715 | 455 | 0.521 | 0.474 | 0.568 | 0.441 | 0.599 |
| combined_1920 | classified_exclude_suspicion_or_disbelief | 115 | 23 | 24 | 68 | 47 | 0.489 | 0.341 | 0.639 | 0.250 | 0.754 |

## Combined By Domain

| domain | sample | pairs | high_wins | low_wins | ties | resolved | high_win_rate | exact95_ci_low | exact95_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| animals | all_pairs | 480 | 102 | 90 | 288 | 192 | 0.531 | 0.458 | 0.603 |
| countries | all_pairs | 480 | 80 | 94 | 306 | 174 | 0.460 | 0.384 | 0.537 |
| political | all_pairs | 480 | 103 | 98 | 279 | 201 | 0.512 | 0.441 | 0.583 |
| religions | all_pairs | 480 | 86 | 106 | 288 | 192 | 0.448 | 0.376 | 0.521 |
| animals | both_traces_classified | 412 | 86 | 79 | 247 | 165 | 0.521 | 0.442 | 0.599 |
| countries | both_traces_classified | 457 | 76 | 88 | 293 | 164 | 0.463 | 0.385 | 0.543 |
| political | both_traces_classified | 453 | 100 | 90 | 263 | 190 | 0.526 | 0.453 | 0.599 |
| religions | both_traces_classified | 476 | 85 | 105 | 286 | 190 | 0.447 | 0.375 | 0.521 |
| animals | exclude_explicit_disbelief | 367 | 76 | 64 | 227 | 140 | 0.543 | 0.457 | 0.627 |
| countries | exclude_explicit_disbelief | 290 | 54 | 52 | 184 | 106 | 0.509 | 0.410 | 0.608 |
| political | exclude_explicit_disbelief | 349 | 73 | 73 | 203 | 146 | 0.500 | 0.416 | 0.584 |
| religions | exclude_explicit_disbelief | 274 | 54 | 54 | 166 | 108 | 0.500 | 0.402 | 0.598 |
| animals | exclude_suspicion_or_disbelief | 125 | 23 | 20 | 82 | 43 | 0.535 | 0.377 | 0.688 |
| countries | exclude_suspicion_or_disbelief | 22 | 7 | 6 | 9 | 13 | 0.538 | 0.251 | 0.808 |
| political | exclude_suspicion_or_disbelief | 16 | 1 | 6 | 9 | 7 | 0.143 | 0.004 | 0.579 |
| animals | classified_exclude_explicit_disbelief | 302 | 62 | 53 | 187 | 115 | 0.539 | 0.444 | 0.632 |
| countries | classified_exclude_explicit_disbelief | 271 | 51 | 46 | 174 | 97 | 0.526 | 0.422 | 0.628 |
| political | classified_exclude_explicit_disbelief | 326 | 71 | 65 | 190 | 136 | 0.522 | 0.435 | 0.608 |
| religions | classified_exclude_explicit_disbelief | 271 | 53 | 54 | 164 | 107 | 0.495 | 0.397 | 0.594 |
| animals | classified_exclude_suspicion_or_disbelief | 85 | 18 | 15 | 52 | 33 | 0.545 | 0.364 | 0.719 |
| countries | classified_exclude_suspicion_or_disbelief | 16 | 4 | 5 | 7 | 9 | 0.444 | 0.137 | 0.788 |
| political | classified_exclude_suspicion_or_disbelief | 14 | 1 | 4 | 9 | 5 | 0.200 | 0.005 | 0.716 |

## Side-Specific Stance Patterns

| flag | pattern | pairs | high_wins | low_wins | ties | resolved | high_win_rate | exact95_ci_low | exact95_ci_high | seven_model_fwer95_ci_low | seven_model_fwer95_ci_high | two_sided_exact_p | crossed_cluster95_ci_low | crossed_cluster95_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| believes | neither | 1781 | 341 | 361 | 1079 | 702 | 0.486 | 0.448 | 0.523 | 0.435 | 0.537 | 0.473 |  |  |
| believes | high_only | 9 | 5 | 0 | 4 | 5 | 1.000 | 0.478 | 1.000 | 0.324 | 1.000 | 0.062 |  |  |
| believes | low_only | 8 | 1 | 1 | 6 | 2 | 0.500 | 0.013 | 0.987 | 0.002 | 0.998 | 1.000 |  |  |
| believes | both | 0 | 0 | 0 | 0 | 0 |  |  |  |  |  |  |  |  |
| disbelieves | neither | 1170 | 237 | 218 | 715 | 455 | 0.521 | 0.474 | 0.568 | 0.457 | 0.584 | 0.399 |  |  |
| disbelieves | high_only | 258 | 34 | 66 | 158 | 100 | 0.340 | 0.248 | 0.442 | 0.219 | 0.478 | 0.002 |  |  |
| disbelieves | low_only | 297 | 55 | 62 | 180 | 117 | 0.470 | 0.377 | 0.565 | 0.345 | 0.598 | 0.579 |  |  |
| disbelieves | both | 73 | 21 | 16 | 36 | 37 | 0.568 | 0.395 | 0.729 | 0.339 | 0.777 | 0.511 |  |  |
| suspicious | neither | 137 | 30 | 26 | 81 | 56 | 0.536 | 0.397 | 0.670 | 0.351 | 0.713 | 0.689 |  |  |
| suspicious | high_only | 260 | 43 | 63 | 154 | 106 | 0.406 | 0.311 | 0.505 | 0.280 | 0.541 | 0.064 |  |  |
| suspicious | low_only | 291 | 66 | 38 | 187 | 104 | 0.635 | 0.534 | 0.727 | 0.499 | 0.757 | 0.008 |  |  |
| suspicious | both | 1110 | 208 | 235 | 667 | 443 | 0.470 | 0.422 | 0.517 | 0.405 | 0.534 | 0.217 |  |  |

## High-Only Versus Low-Only Stance

If explicit belief amplifies the assigned incentive, the high-side win rate should be higher when only the high trace believes than when only the low trace believes.

| flag | high_only_resolved | high_only_high_win_rate | low_only_resolved | low_only_high_win_rate | high_only_minus_low_only | fisher_exact_odds_ratio | fisher_exact_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| believes | 5 | 1.000 | 2 | 0.500 | 0.500 | inf | 0.286 |
| disbelieves | 100 | 0.340 | 117 | 0.470 | -0.130 | 0.581 | 0.054 |
| suspicious | 106 | 0.406 | 104 | 0.635 | -0.229 | 0.393 | 0.001 |

## Flagged Versus Unflagged Resolved Comparisons

| flag | flagged_resolved | flagged_high_win_rate | unflagged_resolved | unflagged_high_win_rate | difference_flagged_minus_unflagged | fisher_exact_odds_ratio | fisher_exact_p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| explicit_disbelief | 254 | 0.433 | 455 | 0.521 | -0.088 | 0.703 | 0.028 |
| suspicion_or_disbelief | 662 | 0.489 | 47 | 0.489 | 0.000 | 1.000 | 1.000 |
