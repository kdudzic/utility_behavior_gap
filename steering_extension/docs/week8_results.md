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

What was known before this week (v4 layer profile, `mini_pilot_report.md`, `layer_selection.md`): the role vectors
R_id (world-class minus skilled) and R_act were extracted alongside E but never used for steering. In the
response-mean readout R_id does not replicate (split-half cosine -0.55 over layers 6 to 20 at 300 responses per
arm, held-out AUC 0.42); E in the same readout is also weak by that measure (0.18, 0.57) yet steers, so the
split-half is not the test. cos(E, R_id) is 0.48 at layer 6, 0.51 at 10, 0.56 at 16. The role effect itself is
small in this model: paper 0.57 n.s., our replication 0.55 (31 / 25) and 8 / 6.

### 4.1 Do the role prompts move the model along the effort direction? (2a)

Untouched essays re-encoded without steering; the response-token-mean residual is projected onto each unit vector
at layers 4 to 20 (`steer/project.py`, `local/week8_role.py`). 60 world-class and 60 skilled essays (week 7), 180
max-effort and 120 neutral essays (week 6). Numbers: Cohen's d of the shift and the AUC for telling the two
conditions apart from the projection alone; "ratio" = role shift divided by exhortation shift along the same
direction. Full table `proj_role_vs_effort.csv`.

| direction | layer | world-class minus skilled: d, AUC | max-effort minus neutral: d, AUC | ratio |
|---|---|---|---|---|
| E | 6 | 0.54, 0.65 | 1.04, 0.77 | 0.52 |
| E | 10 | 0.37, 0.60 | 0.70, 0.69 | 0.51 |
| E | 14 | 0.52, 0.64 | 0.94, 0.75 | 0.53 |
| E | 16 | 0.59, 0.66 | 0.98, 0.76 | 0.56 |
| E | 18 | 0.93, 0.74 | 1.41, 0.84 | 0.59 |
| R_id | 6 | 0.36, 0.60 | 0.42, 0.61 | 0.86 |
| R_id | 16 | 0.36, 0.59 | 0.51, 0.64 | 0.68 |
| R_id minus its E part | 6 | 0.21, 0.56 | 0.01, 0.50 | |
| R_id minus its E part | 16 | 0.13, 0.54 | 0.05, 0.51 | |
| random | 6 to 20 | -0.17 to +0.13, 0.43 to 0.54 | -0.14 to +0.18, 0.46 to 0.55 | |

- The "world-class" prompt moves the model along E at every layer, by half to two thirds of what the exhortation
  does (ratio 0.51 to 0.65; AUC 0.60 to 0.74 against 0.67 to 0.84). E was built from grant and postmortem
  responses, so this is a held-out task and a held-out prompt.
- The part of R_id that is not E separates world-class from skilled essays barely (d 0.11 to 0.25, AUC 0.53 to
  0.57) and the exhortation not at all (AUC 0.50 to 0.52). Along a random direction nothing moves.
- So the role cue's trace in the residual stream is mostly the effort direction. This fits week 7: adding E
  under "world-class" gave nothing (11 / 13), under "skilled" 17 / 5, because the strong cue already pushes
  along E.

### 4.2 An essay-built role vector (2d)

World-class vs skilled on the 30 essay topics, 10 repeats, 300 responses per arm, the recipe of the essay-built E
(`vectors/qwen3.5-9b_essay_role_v1`). Split-half cosine over layers 6 to 20: -0.34 to +0.26 (only layers 4, 5 and
18 above 0.25); held-out AUC 0.41 to 0.63. Cosine with the grant-and-postmortem R_id 0.34 to 0.40; cosine with E
0.43 to 0.50. The essay-built role vector agrees with E more than with the old role vector. Not used for
steering: it would be a noisier E.

### 4.3 Steering with the role direction (2b, 2c)

Essay, neutral prompt, side a steered with the v4 role vector R_id (world-class minus skilled, response mean,
grant + postmortem) or with R_id minus its E component ("R_id perp"), side b the unsteered essay from the same
topic and repeat. 30 topics x 2 repeats = 60 pairs per cell, the three cells where E is clearest. Comparison
columns: the E cell and the pooled random cell at the same layer and dose, with Fisher p. "equal coh." = win rate
among resolved pairs whose coherence differs by at most 3 points. Run `w8_role_steer`; null cell 12 / 10.

| steered with | layer | r | W / L | win rate | ties | coh a / b | E cell (p) | random cell (p) | equal coh. |
|---|---|---|---|---|---|---|---|---|---|
| R_id | 6 | +0.1 | 11 / 6 | 0.65 | 43 | 86.7 / 88.0 | 22 / 3 (0.12) | 16 / 25 (0.09) | 1.00 (7) |
| R_id perp | 6 | +0.1 | 11 / 5 | 0.69 | 44 | 89.4 / 88.0 | 22 / 3 (0.23) | 16 / 25 (0.08) | 0.83 (6) |
| R_id | 10 | -0.1 | 6 / 19 | 0.24 | 35 | 88.6 / 88.0 | 2 / 29 (0.12) | 13 / 27 (0.58) | 0.09 (11) |
| R_id perp | 10 | -0.1 | 11 / 15 | 0.42 | 34 | 89.5 / 88.0 | 2 / 29 (0.002) | 13 / 27 (0.44) | 0.31 (16) |
| R_id | 16 | -0.1 | 7 / 29 | 0.19 | 24 | 88.5 / 88.0 | 5 / 37 (0.53) | 20 / 21 (0.009) | 0.21 (19) |
| R_id perp | 16 | -0.1 | 4 / 15 | 0.21 | 41 | 86.2 / 88.0 | 5 / 37 (0.44) | 20 / 21 (0.05) | 0.22 (9) |

- The role vector steers, in the direction E does and more weakly: removal loses at layers 10 and 16 (0.24,
  0.19; E 0.06, 0.12; random 0.32, 0.49), addition at layer 6 wins 0.65 (E 0.88, random 0.39). None of the
  three differs from the E cell at p < 0.1, and the layer-16 removal differs from random at p = 0.009.
- Take the E component out and the layer-10 removal effect is gone: 11 / 15, at the random level and different
  from the E cell (p = 0.002). This is the cleanest cell: the role vector's removal effect at layer 10 is its
  effort component.
- At layer 16 the orthogonal remainder still loses (4 / 15) but with 41 ties and a coherence drop (86.2, share
  >= 80 0.75; the only cell here that loses coherence), so part of that is damage, not role.
- At layer 6 addition, R_id and R_id perp both win about 0.65 to 0.69 over 16 to 17 resolved pairs with 43 to 44
  ties: too few resolved pairs to tell them from each other, from E, or from random (p 0.08 to 0.23).

### 4.4 Four more recipes for a role vector (PI request after 4.3)

All essay task, steered at the same three cells (layer 6 +0.1, layer 10 -0.1, layer 16 -0.1) against the unsteered
essay, 60 pairs per cell, each vector also with its E component projected out ("perp"). Runs `w8b_role_local`,
`w8b_role_remote`.

| vector | contrast (pos vs neg) | source | before steering |
|---|---|---|---|
| R_act | "pretend you are a world-class ... and act as that person would" vs the direct world-class cue | v4, grant + postmortem, 300 per arm | split-half -0.47, cos(E) 0.26 to 0.30 |
| R_sharp | world-class vs skilled on essays, keeping the quarter of (pos, neg) pairs with the largest judge-scored craft gap | essay_role_v1 responses, haiku craft score 0 to 100 | judge barely separates the arms: 73.4 vs 72.4, only 19% of pairs with a positive gap; cos with the unfiltered R_id 0.85 to 0.93, cos(E) 0.41 to 0.58 |
| R_wide | 20 world-class-essayist paraphrases vs 20 novice-essay-writer paraphrases | new extraction (essay, 300 per arm), response mean | the first reliable role vector: split-half 0.87 / 0.70 / 0.84 at layers 6 / 10 / 16, held-out AUC 0.93 / 0.88 / 0.95 (R_id on essays: -0.55); cos(E) 0.41 to 0.48, cos(R_id) 0.43 to 0.47 |
| R_content | "You are a world-class essayist." vs "You are a world-class <one of 20 other professions>." | new extraction (essay, 300 per arm), response mean | weak: split-half 0.48 / 0.34 / 0.65, AUC 0.62 / 0.56 / 0.74; cos(E) -0.27 to -0.20 (points slightly away from effort), cos(R_wide) -0.24 to -0.21 |

Steering results. Runs `w8b_role_local` (R_act, R_sharp) and `w8b_role_remote` (R_wide, R_content), judged by the
same panel; pooled null cell 20 / 16 with 84 ties. Comparison columns as in 4.3: E cell and pooled random cell at
the same layer and dose (Fisher p), "equal coh." = win rate among resolved pairs within 3 coherence points.
Table `results/2026-11-06_w8/role_recipes_vs_E_random.csv`.

| steered with | layer | r | W / L | win rate | ties | coh a / b | E cell (p) | random cell (p) | equal coh. |
|---|---|---|---|---|---|---|---|---|---|
| R_act | 6 | +0.1 | 10 / 7 | 0.59 | 43 | 89.2 / 88.5 | 22 / 3 (0.06) | 16 / 25 (0.25) | 0.71 (7) |
| R_act perp | 6 | +0.1 | 7 / 11 | 0.39 | 42 | 88.0 / 88.5 | 22 / 3 (0.001) | 16 / 25 (1.0) | 0.33 (3) |
| R_act | 10 | -0.1 | 7 / 13 | 0.35 | 40 | 88.6 / 88.5 | 2 / 29 (0.02) | 13 / 27 (1.0) | 0.22 (9) |
| R_act perp | 10 | -0.1 | 8 / 13 | 0.38 | 39 | 86.9 / 88.5 | 2 / 29 (0.009) | 13 / 27 (0.78) | 0.40 (5) |
| R_act | 16 | -0.1 | 8 / 15 | 0.35 | 37 | 89.7 / 88.5 | 5 / 37 (0.05) | 20 / 21 (0.31) | 0.18 (11) |
| R_act perp | 16 | -0.1 | 2 / 12 | 0.14 | 46 | 86.8 / 88.5 | 5 / 37 (1.0) | 20 / 21 (0.03) | 0.00 (3) |
| R_sharp | 6 | +0.1 | 6 / 12 | 0.33 | 42 | 85.6 / 88.5 | 22 / 3 (<0.001) | 16 / 25 (0.78) | 0.50 (6) |
| R_sharp perp | 6 | +0.1 | 7 / 12 | 0.37 | 41 | 86.0 / 88.5 | 22 / 3 (0.001) | 16 / 25 (1.0) | 0.75 (4) |
| R_sharp | 10 | -0.1 | 2 / 29 | 0.06 | 29 | 87.8 / 88.5 | 2 / 29 (1.0) | 13 / 27 (0.009) | 0.00 (16) |
| R_sharp perp | 10 | -0.1 | 7 / 18 | 0.28 | 35 | 89.5 / 88.5 | 2 / 29 (0.06) | 13 / 27 (0.79) | 0.14 (14) |
| R_sharp | 16 | -0.1 | 1 / 30 | 0.03 | 29 | 90.0 / 88.5 | 5 / 37 (0.23) | 20 / 21 (<0.001) | 0.00 (21) |
| R_sharp perp | 16 | -0.1 | 6 / 20 | 0.23 | 34 | 89.3 / 88.5 | 5 / 37 (0.31) | 20 / 21 (0.04) | 0.08 (12) |
| R_wide | 6 | +0.1 | 12 / 5 | 0.71 | 43 | 86.8 / 87.2 | 22 / 3 (0.24) | 16 / 25 (0.04) | 0.86 (7) |
| R_wide perp | 6 | +0.1 | 6 / 9 | 0.40 | 45 | 87.0 / 87.2 | 22 / 3 (0.003) | 16 / 25 (1.0) | 0.80 (5) |
| R_wide | 10 | -0.1 | 0 / 56 | 0.00 | 4 | 80.2 / 87.2 | 2 / 29 (0.12) | 13 / 27 (<0.001) | 0.00 (12) |
| R_wide perp | 10 | -0.1 | 0 / 57 | 0.00 | 3 | 78.1 / 87.2 | 2 / 29 (0.12) | 13 / 27 (<0.001) | 0.00 (11) |
| R_wide | 16 | -0.1 | 2 / 55 | 0.04 | 3 | 81.7 / 87.2 | 5 / 37 (0.13) | 20 / 21 (<0.001) | 0.00 (12) |
| R_wide perp | 16 | -0.1 | 0 / 54 | 0.00 | 6 | 81.0 / 87.2 | 5 / 37 (0.01) | 20 / 21 (<0.001) | 0.00 (8) |
| R_content | 6 | +0.1 | 7 / 15 | 0.32 | 38 | 89.3 / 87.2 | 22 / 3 (<0.001) | 16 / 25 (0.78) | 0.00 (9) |
| R_content perp | 6 | +0.1 | 8 / 14 | 0.36 | 38 | 88.4 / 87.2 | 22 / 3 (<0.001) | 16 / 25 (1.0) | 0.50 (8) |
| R_content | 10 | -0.1 | 6 / 16 | 0.27 | 38 | 85.1 / 87.2 | 2 / 29 (0.05) | 13 / 27 (0.78) | 0.43 (7) |
| R_content perp | 10 | -0.1 | 9 / 10 | 0.47 | 41 | 87.2 / 87.2 | 2 / 29 (0.001) | 13 / 27 (0.39) | 0.33 (6) |
| R_content | 16 | -0.1 | 8 / 13 | 0.38 | 39 | 85.9 / 87.2 | 5 / 37 (0.02) | 20 / 21 (0.59) | 0.71 (7) |
| R_content perp | 16 | -0.1 | 4 / 15 | 0.21 | 41 | 85.8 / 87.2 | 5 / 37 (0.44) | 20 / 21 (0.05) | 0.17 (6) |

- R_act (pretend-and-act-as vs the direct cue) and R_content (essayist vs other world-class profession) do
  nothing: every cell sits at the random level (p vs random 0.25 to 1.0, except R_act perp at layer 16, 2 / 12
  with 46 ties), and all removal cells differ from the E cell. Their perps are the same. R_content also lost
  coherence at layers 10 and 16 (85 to 86).
- R_sharp (judge-filtered world-class vs skilled, essays) behaves like E at removal: layer 10 2 / 29 (E 2 / 29),
  layer 16 1 / 30 (E 5 / 37), both with 29 ties and no coherence cost; at layer 6 addition it loses (6 / 12,
  coherence 85.6), where E wins 22 / 3. With E projected out the removal effect shrinks to 7 / 18 and 6 / 20
  (0.28, 0.23; equal-coherence 0.14 and 0.08) and is no longer different from E (p 0.06, 0.31) or clearly from
  random (p 0.79, 0.04). Its cosine with E is 0.41 to 0.58, so most of this is E again, and the filter kept only
  75 pairs with a judge that barely separates the arms (section above), so the remainder is noisy.
- R_wide (20 world-class paraphrases vs 20 novice paraphrases) is the first reliable role vector and the only
  one that steers on its own. Removal (pushing toward "novice") loses almost every pair: 0 / 56 and 2 / 55 with
  3 to 4 ties, far below E (2 / 29, 5 / 37) and random (13 / 27, 20 / 21), and this survives projecting E out
  (0 / 57, 0 / 54). The essays are not broken: mean coherence 80 (10th percentile 72, no truncation), and the
  lowest-scored one is a plain, correct, student-style essay ("It helps employees stay healthy and happy ...").
  The novice direction turns the prose plain and simple, the coherence judge marks that down, and the panel
  never picks it. Addition at layer 6 wins 12 / 5 (0.71; E 22 / 3, random 16 / 25, p 0.04 vs random) but the
  perp version does not (6 / 9), so the gain from adding R_wide at layer 6 is its E component.
- So R_wide-minus-E is a direction that is not effort and that the judges care about, but in one direction
  only: removing it makes writing worse (simpler), adding it does nothing. It is a competence or register
  direction, not the "world-class essayist identity" we were looking for. Whether it adds anything over E when
  added at layers 10 to 16, or at smaller doses, was not tested.

## 5. Takeaways

- The win-rate effects of the effort direction are not coherence effects. Random directions keep coherence
  (section 1); the panel does track coherence closely wherever the two essays differ (section 2.1), but at equal
  coherence removal still loses 0.00 of 99 pairs at layers 6 to 14 and addition at +0.1 still wins 0.90 of 40,
  while random directions sit at 0.41 to 0.47 and null at 0.50.
- The paper's own rubric coder sees the vector doing part of what the prompt does: argument depth and concrete
  examples up when E is added, every content marker down when it is removed, plausibility flat. The prompt also
  improves thesis framing and flow; the vector does not. Ablation under the exhortation is the one intervention
  the coder marks as less plausible.
- The role cue rides on the effort direction. "World-class" shifts the residual along E by half of the
  exhortation's shift; the role vector steers like a weak E; the part of it that is not E does nothing at the
  cleanest cell (layer 10 removal) and only damages at layer 16. An essay-built role vector is again mostly E
  plus noise. A role direction separate from effort is not extractable with this recipe in this model, where the
  role effect itself is 0.55 to 0.57.
- Four more recipes (4.4): act-as-the-person and essayist-vs-other-profession give nothing; judge-filtered
  world-class vs skilled is E again. World-class vs novice paraphrases gives the first reliable role vector
  (split-half 0.70 to 0.87), and the part of it that is not E does steer: removing it makes the essay plain
  and simple and loses 0 / 57 and 0 / 54 at layers 10 and 16, while adding it at layer 6 does nothing (6 / 9).
  It is a competence direction with a downward lever only, not the role identity.
- Cost this week: $1.08 rubric, $0.44 craft judge, $6.88 judging (420 + 1,560 pairs), $1.93 coherence, about
  $2.65 vast (three instances, one dead on arrival). About $10.33 OpenRouter in all.
