---
title: "SPAR Week 8 Progress Report"
subtitle: "Is the effort vector's effect a coherence effect? Is there a role direction separate from effort?"
author: "Kacper"
date: "2026-11-07"
---

## This week's goals and how to read every number

Goals from the 31.10 meeting:

1. Show coherence under the effort vector against a random direction, clearly (note item 4).
2. Show how the judges' win rate relates to coherence (note item 5).
3. Run the paper's rubric coder (argument depth, closure, ...) on our steered essays (note item 2).
4. Deep study of the role direction: is there one that is not the effort direction? (note item 3).

How to read every number in this deck:

- Every result is a pairwise comparison on the essay task. For each topic and repeat the model writes one essay with the intervention (side a) and one without (side b). The paper's three judges pick the better one in both orders. Flipped judges count as ties, and pairs the panel ties are dropped. W / L is pairs won / lost by side a. 0.50 means no effect. Unsteered vs unsteered gives 71 / 69.
- Coherence is a separate 0 to 100 score from claude-haiku-4.5 at temperature 0, told to ignore quality. Unsteered essays score 87 to 89.
- E is the effort vector (max-effort minus neutral, response-token mean). The dose r is a fraction of the layer's residual size. r < 0 removes the direction, r > 0 adds it.

## Takeaways

- **The effort vector's win-rate effects are not coherence effects.** Random directions never change coherence. The effort vector changes it only at +0.1 from layer 10 on. The win rates differ where coherence does not.
- **The panel prefers the more coherent essay, yet at equal coherence the effort vector still wins or loses.** Among pairs within 3 coherence points of each other, removal at layers 6 to 14 wins 0 of 99, addition wins 0.90 of 40, random 0.41 to 0.47, null 0.50.
- **The paper's rubric coder sees the vector doing part of what the prompt does.** Adding E raises argument depth and concrete examples, not thesis framing or closure. Removing E lowers every content marker. Plausibility stays flat.
- **The "world-class essayist" prompt leaves its trace in the model along the effort direction.** Half to two thirds of the exhortation's shift. Along the rest of the role vector, nothing.
- **Five role-vector recipes give no role direction that improves essays on its own.** One recipe (world-class vs novice) gives a reliable vector whose non-effort part does steer, but only downward: removing it makes the prose plain and loses 0 / 57.

## 1. Coherence: effort vector vs random direction

![Mean coherence (0 to 100) of the steered essay, by layer and dose. Blue is the effort vector, orange a random direction of the same size. Unsteered essays score 88.7. Random directions stay at 87.6 to 89.2 in every cell. The effort vector costs coherence only at +0.1 from layer 10 on (86.1, 84.3, 83.9). Ablating E at layers 8 to 16 costs 5.4 points; ablating a random direction costs nothing.](results/2026-11-06_w8/coherence_grid.png)

## 1. Coherence does not explain the win rates

Essay task, neutral prompt. Side a steered, side b the unsteered essay from the same topic and repeat. 60 pairs per effort cell, 120 per random cell (two directions pooled). "coh a / b" is mean coherence of the steered and the unsteered essay.

| layer | dose r | steered with | W / L | win rate | coh a / b |
|---|---|---|---|---|---|
| 6 | -0.1 | effort | 7 / 30 | 0.19 | 88.7 / 88.7 |
| 6 | -0.1 | random | 12 / 28 | 0.30 | 88.8 / 89.0 |
| 6 | +0.1 | effort | 22 / 3 | 0.88 | 89.2 / 88.7 |
| 6 | +0.1 | random | 16 / 25 | 0.39 | 87.9 / 89.0 |
| 10 | -0.1 | effort | 2 / 29 | 0.06 | 88.9 / 88.7 |
| 10 | -0.1 | random | 13 / 27 | 0.32 | 88.6 / 89.0 |
| 10 | +0.1 | effort | 18 / 4 | 0.82 | 86.1 / 88.7 |
| 10 | +0.1 | random | 11 / 22 | 0.33 | 88.2 / 89.0 |
| 14 | -0.1 | effort | 3 / 37 | 0.08 | 90.0 / 88.7 |
| 14 | -0.1 | random | 16 / 14 | 0.53 | 88.4 / 89.0 |
| 14 | +0.1 | effort | 13 / 12 | 0.52 | 84.3 / 88.7 |
| 14 | +0.1 | random | 18 / 20 | 0.47 | 88.6 / 89.0 |

- At layers 6 to 14 the effort vector and the random direction have the same coherence, yet removal wins 0.06 to 0.19 against random's 0.30 to 0.53, and addition wins 0.82 to 0.88 against 0.33 to 0.39.
- The one cell where the effort vector loses coherence (layer 14, +0.1, 84.3) is also the one where its win rate falls to 0.52.

## 2. At equal coherence, removing E still loses and adding E still wins

![Win rate of side a against the coherence gap (side a minus side b), over 9,120 judged pairs, all layers and doses pooled (effort: layers 6 to 28 from the week-6 sweep; random: layers 6, 10, 14, 20). Wherever the gap is larger than 3 points, the panel picks the more coherent essay 85 to 100% of the time, in every group, null cells too. In the equal-coherence bin (-3 to +3) effort removal still loses (0.10 over 346 pairs) and effort addition still wins (0.71 over 302 pairs), while random sits at 0.41 to 0.47 and null at 0.50. Restricted to layers 6 to 14: removal 0.00 of 99 pairs, addition at +0.1 0.90 of 40.](results/2026-11-06_w8/pairs_winrate_by_coherence_gap.png)

## 3. The paper's rubric coder on our pairs

The paper's blind coder (gemini-2.5-flash, temperature 0, code unchanged) sees the task and both essays in random order and says which is better on each marker. Each cell is the share of pairs where the coder preferred side a minus the share where it preferred side b, over the same 60 pairs the panel judged. Panel W / L in brackets.

| side a vs side b (panel W / L) | thesis | depth | example | counter-arg. | closure | plausibility |
|---|---|---|---|---|---|---|
| max-effort prompt vs neutral prompt (14 / 7) | +0.38 | +0.33 | +0.27 | +0.12 | +0.32 | 0.00 |
| add E, layer 6 +0.1, vs unsteered (22 / 3) | +0.10 | +0.45 | +0.42 | -0.02 | +0.08 | -0.10 |
| add E, layer 14 +0.05, vs unsteered (17 / 4) | +0.08 | +0.40 | +0.10 | +0.17 | +0.03 | -0.10 |
| remove E, layer 10 -0.1, vs unsteered (2 / 29) | -0.65 | -0.75 | -0.55 | -0.37 | -0.50 | -0.02 |
| remove E, layer 16 -0.1, vs unsteered (5 / 37) | -0.73 | -0.83 | -0.60 | -0.30 | -0.65 | -0.05 |
| E ablated 8 to 16 under max-effort, vs untouched max-effort (3 / 17) | +0.27 | +0.35 | +0.07 | -0.25 | +0.15 | -0.28 |
| random direction, layer 6 +0.1, vs unsteered (7 / 15) | -0.20 | -0.28 | -0.27 | +0.02 | -0.32 | -0.05 |
| world-class vs skilled prompt, untouched (8 / 6) | +0.10 | +0.05 | -0.03 | -0.10 | +0.08 | -0.03 |

- Our exhortation matches the paper's profile (thesis, depth, example, closure up 0.3 to 0.4).
- Adding E raises depth and examples like the exhortation does, but not thesis framing or closure. The vector improves reasoning and examples. The prompt also improves framing and flow.
- Removing E lowers every content marker by 0.5 to 0.8 with plausibility flat. The essays are emptier, not wrong.
- Ablation under the exhortation is the only cell the coder marks less plausible (-0.28). That matches the invented statistics seen in week 7.

## 4a. The "world-class" prompt leaves its trace along the effort direction

We took essays written with no steering under four prompts (world-class, skilled, max-effort, neutral), re-encoded them, and measured each essay's position along a direction, like a ruler. Rows are rulers, columns are pairs of prompt groups, and every row uses the same 420 untouched essays. AUC is the chance that a random essay from the first group sits further along the ruler than a random essay from the second (0.50 is chance, 1.00 is a perfect split). Ratio is the world-class shift divided by the exhortation shift on that ruler. 60 essays per role prompt, 180 max-effort, 120 neutral.

| ruler (direction measured along) | layer | AUC: world-class essays vs skilled essays | AUC: max-effort essays vs neutral essays | ratio |
|---|---|---|---|---|
| E (effort vector) | 6 | 0.65 | 0.77 | 0.52 |
| E | 10 | 0.60 | 0.69 | 0.51 |
| E | 16 | 0.66 | 0.76 | 0.56 |
| E | 18 | 0.74 | 0.84 | 0.59 |
| role vector minus its E part | 6 | 0.56 | 0.50 | |
| role vector minus its E part | 16 | 0.54 | 0.51 | |
| random direction | 6 to 20 | 0.43 to 0.54 | 0.46 to 0.55 | |

- "World-class" moves essays along E in the same direction as the exhortation does, half to two thirds as far. E was built from grant and postmortem responses, so this is a held-out task and prompt.
- Along the part of the role vector that is not E, world-class and skilled essays are nearly indistinguishable (AUC 0.54 to 0.56), and the exhortation does not move at all (0.50).
- So whatever the role prompt does inside the model, it does mostly through the effort direction. This fits week 7: adding E under "world-class" gave nothing (11 / 13), under "skilled" 17 / 5.

## 4b. Five role-vector recipes: none gives a role direction that improves essays on its own

Each vector steered at the three clearest effort cells (layer 6 +0.1, layer 10 -0.1, layer 16 -0.1) against the unsteered essay, 60 pairs per cell. Each also run with its E component projected out ("minus E"). E at those cells: 22 / 3, 2 / 29, 5 / 37. Random: 16 / 25, 13 / 27, 20 / 21.

| vector | contrast (positive vs negative prompt) | reliability (split-half cosine) | steering result |
|---|---|---|---|
| R_id | world-class vs skilled | -0.55 | a weak E (6 / 19, 7 / 29, 11 / 6). Minus E, the layer-10 removal effect is gone (11 / 15, p = 0.002 vs E) |
| R_act | "pretend and act as" vs direct cue | -0.47 | random level everywhere |
| R_sharp | R_id pairs with the largest judge-scored craft gap | weak filter (judge scores 73 vs 72) | E again at removal (2 / 29, 1 / 30). Minus E a weak loss (7 / 18, 6 / 20) |
| R_wide | 20 world-class vs 20 novice paraphrases | 0.70 to 0.87 | removal 0 / 56, 2 / 55, also minus E (0 / 57, 0 / 54). Addition 12 / 5, minus E 6 / 9 |
| R_content | world-class essayist vs world-class other profession | 0.34 to 0.65 | random level everywhere |

- R_act and R_content do nothing. R_sharp is E again. R_id is a weak E.
- R_wide is the first reliable role vector. Its non-effort part steers, but only when removed.

## 4b. R_wide minus E is a competence direction with a downward lever only

![Win rate of each role vector (filled dot) and of the same vector with its E component projected out (hollow dot) at the three cells. Blue line is the effort vector at that cell, orange line a random direction, dotted line 0.50. Only R_wide at removal (layers 10 and 16) sits below both lines with and without its E part. Removing R_wide-minus-E pushes the essay toward "novice": the essays stay intact (coherence 80, no truncation) and read as plain student prose, and the panel never picks them. At layer 6 addition R_wide beats random only with its E part in (filled 0.71, hollow 0.40), so adding the non-effort part does nothing. This is a competence or register direction, not the "world-class essayist identity". Not yet tested: adding it at layers 10 to 16, or smaller doses.](results/2026-11-06_w8/role_recipes_winrate.png)

## Open questions and cost

- Add R_wide-minus-E at layers 10 to 16, or at smaller doses, to check whether the competence direction has an upward lever at all.
- Is the role effect worth chasing further in this model? The paper reports 0.57 n.s. for Qwen3.5-9B essays, our replication 0.55 and 8 / 6. The prompt itself does little here.
- The effort story is now: real at equal coherence, moves the content markers the exhortation moves, and is what the role prompt mostly acts through. What should the next test of it be (27B, other tasks, metacognition)?
- Cost this week: about $10.33 on OpenRouter ($1.08 rubric coder, $0.44 craft judge, $6.88 judging of 1,980 pairs, $1.93 coherence) and about $2.65 on vast. Full report: `week8_results.md`, one-pager: `week8_onepager.md`.

## Backup: coherence gap bins, all groups

Resolved pairs with both essays scored. Gap is coherence of side a minus side b. Each cell is the win rate of side a in that bin, with the number of pairs in brackets. Last column: share of unequal-coherence pairs where the panel chose the more coherent essay.

| side a | pairs | gap < -10 | -10 to -3 | -3 to +3 | +3 to +10 | > +10 | more coherent essay wins |
|---|---|---|---|---|---|---|---|
| unsteered (null cells) | 121 | 0.06 (33) | 0.00 (7) | 0.50 (46) | 0.93 (14) | 1.00 (21) | 0.96 |
| random, r -0.1 or -0.05 | 182 | 0.04 (53) | 0.31 (13) | 0.41 (83) | 0.90 (10) | 0.87 (23) | 0.89 |
| random, r +0.025 to +0.1 | 311 | 0.02 (87) | 0.00 (25) | 0.47 (150) | 0.85 (20) | 0.90 (29) | 0.95 |
| effort removed, r -0.1 or -0.05 | 671 | 0.02 (133) | 0.07 (43) | 0.10 (346) | 0.86 (63) | 0.81 (86) | 0.91 |
| effort added, r +0.025 to +0.1 | 1071 | 0.10 (373) | 0.33 (60) | 0.71 (302) | 0.97 (160) | 0.99 (176) | 0.92 |
| effort, abs(r) = 0.2 | 567 | 0.00 (161) | 0.00 (86) | 0.01 (234) | 0.10 (52) | 0.35 (34) | 0.79 |
| effort ablated 8-16 or all layers | 233 | 0.01 (204) | 0.00 (5) | 0.50 (16) | 1.00 (2) | 1.00 (6) | 0.99 |

- Random directions lose through small coherence losses: the random essay is the less coherent one (gap below -3) in 36% of random-addition pairs against 16% the other way, and those pairs go 0.02.

## Backup: role-vector steering, every cell (1 of 2)

Essay task, neutral prompt, side a steered, side b unsteered, 60 pairs per cell. "E cell (p)" and "random cell (p)" give the effort and the pooled random result at the same layer and dose, with Fisher p against this row. "equal coh." is the win rate among pairs within 3 coherence points, with the number of pairs. R_id cells are in section 4.3 of the report.

| steered with | layer | r | W / L | win rate | ties | coh a / b | E cell (p) | random cell (p) | equal coh. |
|---|---|---|---|---|---|---|---|---|---|
| R_act | 6 | +0.1 | 10 / 7 | 0.59 | 43 | 89.2 / 88.5 | 22 / 3 (0.06) | 16 / 25 (0.25) | 0.71 (7) |
| R_act minus E | 6 | +0.1 | 7 / 11 | 0.39 | 42 | 88.0 / 88.5 | 22 / 3 (0.001) | 16 / 25 (1.0) | 0.33 (3) |
| R_act | 10 | -0.1 | 7 / 13 | 0.35 | 40 | 88.6 / 88.5 | 2 / 29 (0.02) | 13 / 27 (1.0) | 0.22 (9) |
| R_act minus E | 10 | -0.1 | 8 / 13 | 0.38 | 39 | 86.9 / 88.5 | 2 / 29 (0.009) | 13 / 27 (0.78) | 0.40 (5) |
| R_act | 16 | -0.1 | 8 / 15 | 0.35 | 37 | 89.7 / 88.5 | 5 / 37 (0.05) | 20 / 21 (0.31) | 0.18 (11) |
| R_act minus E | 16 | -0.1 | 2 / 12 | 0.14 | 46 | 86.8 / 88.5 | 5 / 37 (1.0) | 20 / 21 (0.03) | 0.00 (3) |
| R_sharp | 6 | +0.1 | 6 / 12 | 0.33 | 42 | 85.6 / 88.5 | 22 / 3 (<0.001) | 16 / 25 (0.78) | 0.50 (6) |
| R_sharp minus E | 6 | +0.1 | 7 / 12 | 0.37 | 41 | 86.0 / 88.5 | 22 / 3 (0.001) | 16 / 25 (1.0) | 0.75 (4) |
| R_sharp | 10 | -0.1 | 2 / 29 | 0.06 | 29 | 87.8 / 88.5 | 2 / 29 (1.0) | 13 / 27 (0.009) | 0.00 (16) |
| R_sharp minus E | 10 | -0.1 | 7 / 18 | 0.28 | 35 | 89.5 / 88.5 | 2 / 29 (0.06) | 13 / 27 (0.79) | 0.14 (14) |
| R_sharp | 16 | -0.1 | 1 / 30 | 0.03 | 29 | 90.0 / 88.5 | 5 / 37 (0.23) | 20 / 21 (<0.001) | 0.00 (21) |
| R_sharp minus E | 16 | -0.1 | 6 / 20 | 0.23 | 34 | 89.3 / 88.5 | 5 / 37 (0.31) | 20 / 21 (0.04) | 0.08 (12) |

## Backup: role-vector steering, every cell (2 of 2)

Same design and columns as the previous slide.

| steered with | layer | r | W / L | win rate | ties | coh a / b | E cell (p) | random cell (p) | equal coh. |
|---|---|---|---|---|---|---|---|---|---|
| R_wide | 6 | +0.1 | 12 / 5 | 0.71 | 43 | 86.8 / 87.2 | 22 / 3 (0.24) | 16 / 25 (0.04) | 0.86 (7) |
| R_wide minus E | 6 | +0.1 | 6 / 9 | 0.40 | 45 | 87.0 / 87.2 | 22 / 3 (0.003) | 16 / 25 (1.0) | 0.80 (5) |
| R_wide | 10 | -0.1 | 0 / 56 | 0.00 | 4 | 80.2 / 87.2 | 2 / 29 (0.12) | 13 / 27 (<0.001) | 0.00 (12) |
| R_wide minus E | 10 | -0.1 | 0 / 57 | 0.00 | 3 | 78.1 / 87.2 | 2 / 29 (0.12) | 13 / 27 (<0.001) | 0.00 (11) |
| R_wide | 16 | -0.1 | 2 / 55 | 0.04 | 3 | 81.7 / 87.2 | 5 / 37 (0.13) | 20 / 21 (<0.001) | 0.00 (12) |
| R_wide minus E | 16 | -0.1 | 0 / 54 | 0.00 | 6 | 81.0 / 87.2 | 5 / 37 (0.01) | 20 / 21 (<0.001) | 0.00 (8) |
| R_content | 6 | +0.1 | 7 / 15 | 0.32 | 38 | 89.3 / 87.2 | 22 / 3 (<0.001) | 16 / 25 (0.78) | 0.00 (9) |
| R_content minus E | 6 | +0.1 | 8 / 14 | 0.36 | 38 | 88.4 / 87.2 | 22 / 3 (<0.001) | 16 / 25 (1.0) | 0.50 (8) |
| R_content | 10 | -0.1 | 6 / 16 | 0.27 | 38 | 85.1 / 87.2 | 2 / 29 (0.05) | 13 / 27 (0.78) | 0.43 (7) |
| R_content minus E | 10 | -0.1 | 9 / 10 | 0.47 | 41 | 87.2 / 87.2 | 2 / 29 (0.001) | 13 / 27 (0.39) | 0.33 (6) |
| R_content | 16 | -0.1 | 8 / 13 | 0.38 | 39 | 85.9 / 87.2 | 5 / 37 (0.02) | 20 / 21 (0.59) | 0.71 (7) |
| R_content minus E | 16 | -0.1 | 4 / 15 | 0.21 | 41 | 85.8 / 87.2 | 5 / 37 (0.44) | 20 / 21 (0.05) | 0.17 (6) |
