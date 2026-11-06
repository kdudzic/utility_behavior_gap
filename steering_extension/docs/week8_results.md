# Week 8 results (2026-11-06): coherence vs random, win rate vs coherence, the paper's rubric coder, the role direction

Plan: repo-root `week8_plan.txt`, from `steering_extension/3110_meeting_notes.md`. Raw tables and figures in
`docs/results/2026-11-06_w8/`. Sections 1 to 3 are offline re-analyses of weeks 6 and 7 plus one new coder pass;
section 4 is the week-8 GPU batch (role direction).

## 0. How to read the tables

Every number is a pairwise comparison. For each topic and repeat the model writes one essay with the intervention
(side a) and one without (side b), from the same prompt, unless the row says otherwise. The paper's three judges pick
the better one in both orders; a judge whose orders disagree counts as a tie, panel ties are excluded. W / L = pairs
won / lost by side a; win rate = W / (W + L); 0.50 = no effect; the null cells (unsteered vs unsteered) pooled over
all runs give 71 / 69. Coherence is a separate 0 to 100 score from claude-haiku-4.5 at temperature 0 for each
essay (fluent, on topic, consistent; told to ignore quality). Unsteered essays score 87 to 89. The effort vector is
the week-6 v4 vector (response-token mean, max-effort minus neutral, grant + postmortem, 300 per arm); dose r is a
fraction of the layer's RMS residual norm; r < 0 removes the direction.

## 1. Coherence: effort direction vs random direction (note item 4)

Essay, neutral prompt, side a steered, side b the unsteered essay from the same topic and repeat. Effort cells from
the week-6 sweep (60 pairs each), random cells from week 7 (two directions pooled, 120 pairs each). "coh a / b" =
mean coherence of the steered and the unsteered essay. Figure: `coherence_grid.png`.

| layer | r | steered with | W / L | win rate | coh a / b | share a >= 80 |
|---|---|---|---|---|---|---|
| 6 | -0.1 | effort | 7 / 30 | 0.19 | 88.7 / 88.7 | 0.85 |
| 6 | -0.1 | random | 12 / 28 | 0.30 | 88.8 / 89.0 | 0.89 |
| 6 | +0.05 | effort | 15 / 9 | 0.62 | 88.0 / 88.7 | 0.82 |
| 6 | +0.05 | random | 10 / 22 | 0.31 | 88.0 / 89.0 | 0.84 |
| 6 | +0.1 | effort | 22 / 3 | 0.88 | 89.2 / 88.7 | 0.88 |
| 6 | +0.1 | random | 16 / 25 | 0.39 | 87.9 / 89.0 | 0.86 |
| 10 | -0.1 | effort | 2 / 29 | 0.06 | 88.9 / 88.7 | 0.90 |
| 10 | -0.1 | random | 13 / 27 | 0.32 | 88.6 / 89.0 | 0.88 |
| 10 | +0.05 | effort | 12 / 6 | 0.67 | 88.0 / 88.7 | 0.87 |
| 10 | +0.05 | random | 16 / 16 | 0.50 | 87.6 / 89.0 | 0.82 |
| 10 | +0.1 | effort | 18 / 4 | 0.82 | 86.1 / 88.7 | 0.77 |
| 10 | +0.1 | random | 11 / 22 | 0.33 | 88.2 / 89.0 | 0.83 |
| 14 | -0.1 | effort | 3 / 37 | 0.08 | 90.0 / 88.7 | 0.93 |
| 14 | -0.1 | random | 16 / 14 | 0.53 | 88.4 / 89.0 | 0.84 |
| 14 | +0.05 | effort | 17 / 4 | 0.81 | 88.3 / 88.7 | 0.83 |
| 14 | +0.05 | random | 9 / 26 | 0.26 | 88.0 / 89.0 | 0.84 |
| 14 | +0.1 | effort | 13 / 12 | 0.52 | 84.3 / 88.7 | 0.63 |
| 14 | +0.1 | random | 18 / 20 | 0.47 | 88.6 / 89.0 | 0.84 |
| 20 | -0.1 | effort | 7 / 25 | 0.22 | 88.8 / 88.7 | 0.83 |
| 20 | -0.1 | random | 8 / 23 | 0.26 | 88.4 / 89.0 | 0.84 |
| 20 | +0.05 | effort | 13 / 7 | 0.65 | 86.6 / 88.7 | 0.77 |
| 20 | +0.05 | random | 6 / 22 | 0.21 | 88.5 / 89.0 | 0.85 |
| 20 | +0.1 | effort | 10 / 20 | 0.33 | 83.9 / 88.7 | 0.70 |
| 20 | +0.1 | random | 13 / 20 | 0.39 | 88.1 / 89.0 | 0.85 |
| 8 to 16 | ablate | effort, max-effort prompt vs untouched max-effort | 3 / 17 | 0.15 | 82.3 / 87.7 | 0.63 |
| 8 to 16 | ablate | random, max-effort prompt vs neutral prompt | 12 / 8 | 0.60 | 89.1 / 88.1 | 0.90 |
| all 32 | ablate | effort, max-effort vs untouched max-effort | 0 / 60 | 0.00 | 2.4 / 86.7 | 0.00 |

Pooled over the 12 grid cells: effort 87.5 vs its unsteered twin 88.7 (delta -1.1, SE 0.4); random 88.3 vs 89.0
(delta -0.7, SE 0.2).

- Random directions at r up to +0.1 leave coherence where it is: 87.6 to 89.2 at every cell, never more than 1.4
  below the unsteered twin.
- The effort direction is the same at removal (88.7 to 90.0, slightly above unsteered at layer 14) and at +0.05 in
  layers 6 to 14. It costs coherence only at +0.1 from layer 10 on (86.1, 84.3, 83.9) and at +0.05 from layer 20.
- Ablation of the effort direction is the only intervention with a clear coherence cost at the dose used: -5.4
  points at layers 8 to 16, total breakdown at all 32 layers. Ablating a random direction costs nothing (+1.0).
- So coherence does not separate effort from random where the win rates do (removal 0.06 to 0.19 vs random 0.26
  to 0.53 at layers 6 to 14; addition 0.62 to 0.88 vs 0.26 to 0.50). The win-rate differences are not coherence
  differences.

## 2. Win rate and coherence (note item 5)

### 2.1 Pair level: the panel almost always picks the more coherent essay

Resolved pairs only, both essays scored. "gap" = coherence of side a minus coherence of side b. Figure:
`pairs_winrate_by_coherence_gap.png`.

| side a | pairs | gap < -10 | -10 to -3 | -3 to +3 | +3 to +10 | > +10 | higher-coherence essay wins |
|---|---|---|---|---|---|---|---|
| unsteered (null cells) | 121 | 0.06 (33) | 0.00 (7) | 0.50 (46) | 0.93 (14) | 1.00 (21) | 0.96 |
| random, r -0.1 or -0.05 | 182 | 0.04 (53) | 0.31 (13) | 0.41 (83) | 0.90 (10) | 0.87 (23) | 0.89 |
| random, r +0.025 to +0.1 | 311 | 0.02 (87) | 0.00 (25) | 0.47 (150) | 0.85 (20) | 0.90 (29) | 0.95 |
| effort removed, r -0.1 or -0.05 | 671 | 0.02 (133) | 0.07 (43) | 0.10 (346) | 0.86 (63) | 0.81 (86) | 0.91 |
| effort added, r +0.025 to +0.1 | 1071 | 0.10 (373) | 0.33 (60) | 0.71 (302) | 0.97 (160) | 0.99 (176) | 0.92 |
| effort, abs(r) = 0.2 | 567 | 0.00 (161) | 0.00 (86) | 0.01 (234) | 0.10 (52) | 0.35 (34) | 0.79 |
| effort ablated 8-16 or all layers | 233 | 0.01 (204) | 0.00 (5) | 0.50 (16) | 1.00 (2) | 1.00 (6) | 0.99 |

Cells: win rate of side a within each gap bin (pairs in brackets). Last column: among pairs with unequal coherence,
share where the panel chose the essay with the higher coherence score.

- Whenever the two essays differ in coherence by more than 3 points, the panel picks the more coherent one 85 to
  100% of the time, in null cells as much as in steered cells. The coherence judge is told to ignore quality, but
  its score tracks the panel's quality judgement closely. A logistic fit gives +2.3 to +2.9 log-odds per 10
  coherence points in every group, also within cells.
- The effort effect survives at equal coherence. Among pairs within 3 points of each other: effort removal wins
  0.10 (346 pairs), random removal 0.41, null 0.50; effort addition wins 0.71 (302 pairs), random addition 0.47.
  Restricting to layers 6 to 14: removal at -0.1 wins 0.00 of 99 equal-coherence pairs, addition at +0.1 wins
  0.90 of 40 (`coherence_asymmetry.csv`).
- Random directions lose through small coherence losses the panel punishes: the random essay is the less coherent
  one (gap below -3) in 36% of random-addition pairs against 16% the other way (null cells: 33% vs 29%), and
  those pairs go 0.02. At equal coherence random is near null (0.41 to 0.47 vs 0.50).
- Ablation and high doses (abs(r) = 0.2) lose through coherence: 88% of ablation pairs have a gap below -10.

### 2.2 Cell level

One point per cell (126 essay cells with at least 10 resolved pairs): win rate against the steered side's mean
coherence. Figure: `winrate_vs_coherence.png`.

| cells | n | Spearman rho (win rate, coherence a) | p |
|---|---|---|---|
| effort, all doses | 84 | -0.20 | 0.08 |
| effort, r < 0 | 36 | +0.53 | 0.001 |
| effort, r > 0 | 48 | +0.62 | 0.000003 |
| random | 28 | +0.03 | 0.86 |
| ablation | 6 | +0.81 | 0.05 |

- Across all effort cells there is no overall relation (rho -0.20): the removal cells have high coherence and low
  win rates, the addition cells the reverse. Within each sign the relation is positive: the cells that lose
  coherence (late layers, high dose) also lose pairs.
- Random cells show no relation (rho +0.03): their coherence hardly varies (87.6 to 89.2).

## 3. The paper's rubric coder on our pairs (note item 2)

The paper's blind task-rubric coder, code unchanged (`run_task_rubric_feature_coding.code_sample_row`):
google/gemini-2.5-flash at temperature 0 sees the task and the two essays as A and B (sides random) and for each
of six markers says which is better, tie, or not applicable. delta = share of pairs where the intervened essay was
coded better minus share where the opponent was; CI bootstrapped over pairs; 60 pairs per cell, the same pairs the
panel judged. Script `local/rubric_judge.py`; full tables with the CIs in `rubric_summary.md`. 660 calls, $1.08.

Paper's row for Qwen3.5-9B essays (17 pairs): exhortation raises argument depth +0.41, rhetorical coherence
+0.29, concrete example +0.29; role (world-class vs skilled) raises thesis framing +0.47, concrete example +0.41.

| side a vs side b (panel W / L) | thesis framing | argument depth | concrete example | counterargument | rhetorical closure | plausibility |
|---|---|---|---|---|---|---|
| max-effort prompt vs neutral prompt (14 / 7) | +0.38 | +0.33 | +0.27 | +0.12 | +0.32 | 0.00 |
| add E layer 6 +0.1 vs unsteered (22 / 3) | +0.10 | +0.45 | +0.42 | -0.02 | +0.08 | -0.10 |
| add E layer 14 +0.05 vs unsteered (17 / 4) | +0.08 | +0.40 | +0.10 | +0.17 | +0.03 | -0.10 |
| add E layer 6 +0.1 under "skilled" vs untouched (17 / 5) | +0.42 | +0.70 | +0.43 | +0.23 | +0.48 | -0.03 |
| remove E layer 10 -0.1 vs unsteered (2 / 29) | -0.65 | -0.75 | -0.55 | -0.37 | -0.50 | -0.02 |
| remove E layer 16 -0.1 vs unsteered (5 / 37) | -0.73 | -0.83 | -0.60 | -0.30 | -0.65 | -0.05 |
| E ablated 8-16 under max-effort vs untouched max-effort (3 / 17) | +0.27 | +0.35 | +0.07 | -0.25 | +0.15 | -0.28 |
| random 0, layer 6 +0.1 vs unsteered (7 / 15) | -0.20 | -0.28 | -0.27 | +0.02 | -0.32 | -0.05 |
| random 1, layer 6 +0.1 vs unsteered (9 / 10) | +0.02 | +0.02 | +0.02 | +0.02 | +0.12 | -0.02 |
| world-class vs skilled prompt, untouched (8 / 6) | +0.10 | +0.05 | -0.03 | -0.10 | +0.08 | -0.03 |

Grant (7 markers), remove essay-built E at layer 16 -0.1 vs unsteered (0 / 49): every marker -0.77 to -0.93
(problem significance -0.82, intervention specificity -0.88, evaluation rigor -0.93, feasibility -0.77, risks
-0.88, measurable impact -0.88, stakeholder fit -0.78).

- Our exhortation replication matches the paper's rubric profile: argument depth, thesis, example and closure up
  by 0.3 to 0.4, counterargument and plausibility unchanged.
- Adding the effort direction raises the two content markers the exhortation raises most, argument depth (+0.40 to
  +0.45) and concrete example (+0.42 at layer 6), but not thesis framing or rhetorical closure (+0.03 to +0.10).
  The prompt improves framing and flow as well; the vector improves reasoning and examples only. Under the
  "skilled" prompt the vector lifts every marker (+0.42 to +0.70).
- Removing the direction lowers every content marker by 0.5 to 0.8 while plausibility stays at 0: the essays are
  emptier, not wrong. The grant version is the same picture at -0.8 to -0.9.
- Ablation under the exhortation keeps argument depth and thesis above the untouched exhortation (+0.35, +0.27)
  but loses on plausibility (-0.28, the only cell where this marker moves) and counterargument (-0.25). The
  coder sees what the qualitative read found: more claims, invented specifics.
- Random direction 0 lowers the markers by 0.2 to 0.3 (panel 7 / 15); random direction 1 does nothing (9 / 10).
  The two random directions differ, as their panel results do.
- World-class vs skilled: nothing moves (-0.10 to +0.10), in line with the panel's 8 / 6 and unlike the paper's
  Qwen row (+0.47 thesis, 17 pairs).

## 4. The role direction (note item 3)

(GPU batch running; filled in when judged.)
