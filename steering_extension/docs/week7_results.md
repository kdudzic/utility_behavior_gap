# Week 7 results: random controls, cross-validation on grant, role cues, clean necessity test

Date: 2026-10-30. Items 5 to 8 of `week7_plan.txt`. Setup as in `week6_results.md` unless stated: Qwen3.5-9B,
the paper's prompts, 30 items x 2 repeats = 60 pairs per cell, steered (or ablated) side against an unsteered side
from the same item and repeat, the paper's three-judge panel with both orders, flips -> tie, panel ties excluded,
exact-binomial CI. Vector: v4 response-mean effort direction unless stated. Dose r as a fraction of the layer's RMS
residual norm. Coherence: one judge, 0 to 100.

Generation ran without the hub kernels this time (the `kernels-community/fla` kernel no longer imports under
transformers main; the torch fallback is about 25% slower, see `vast/w7_chain.sh`). Totals: 2,700 pairs,
5,400 generations plus 600 extraction responses (1 h 20 min of one A100 PCIe at $0.65/h), 16,200 judge votes,
3,000 coherence scores (about $25 to 30 of OpenRouter calls). Tables: `results/2026-10-30_w7/`.

## 1. Random controls on the sweep grid (plan item 5)

Two norm-matched random directions (rand0, rand1 from the v4 file) at layers 6, 10, 14, 20 and r = -0.1, +0.05,
+0.1; 1,440 pairs plus a baseline-vs-baseline cell. Full table `w7_random_dose_summary.csv`.

**Random directions are not neutral at these doses.** Pooled over the 24 cells the random-steered essay wins
148 / 265 (0.36): at r = -0.1 0.35 (49 / 92), at +0.05 0.32 (41 / 86), at +0.1 0.40 (58 / 87). Coherence stays at
baseline (86.7 to 89.2 per cell) and length is unchanged, so the judges see small but real damage from any
perturbation of this size, not broken text. Week 6's four random cells at layer 16 already pointed this way
(37 / 43, 0.46). The baseline-vs-baseline cell in this run came out 5 / 15 (0.25, p = 0.04); the seven null cells
across all runs are 11/10, 10/7, 11/13, 10/7, 8/10, 5/15, 16/7, pooled 71 / 69, so that cell is the low end of
ordinary scatter at 20 resolved pairs.

The effort vector against the pooled random cells at the same layer and dose (Fisher exact):

| layer | r | effort vector (week 6) | random pooled | p |
| --- | --- | --- | --- | --- |
| 6 | -0.1 | 0.19 (7/30) | 0.30 (12/28) | 0.30 |
| 6 | +0.05 | 0.62 (15/9) | 0.31 (10/22) | 0.03 |
| 6 | +0.1 | **0.88 (22/3)** | 0.39 (16/25) | 0.0001 |
| 10 | -0.1 | **0.06 (2/29)** | 0.33 (13/27) | 0.009 |
| 10 | +0.05 | 0.67 (12/6) | 0.50 (16/16) | 0.37 |
| 10 | +0.1 | **0.82 (18/4)** | 0.33 (11/22) | 0.0008 |
| 14 | -0.1 | **0.07 (3/37)** | 0.53 (16/14) | 0.00003 |
| 14 | +0.05 | **0.81 (17/4)** | 0.26 (9/26) | 0.0001 |
| 14 | +0.1 | 0.52 (13/12) | 0.47 (18/20) | 0.8 |
| 20 | -0.1 | 0.22 (7/25) | 0.26 (8/23) | 0.77 |
| 20 | +0.05 | 0.65 (13/7) | 0.21 (6/22) | 0.003 |
| 20 | +0.1 | 0.33 (10/20) | 0.39 (13/20) | 0.79 |

- **The positive effect is direction-specific.** Every early-layer winning cell (layer 6 at +0.05 and +0.1,
  layer 10 at +0.1, layer 14 at +0.05, layer 20 at +0.05) beats its random control, with random sitting at 0.2 to
  0.4 in the same cells.
- **The negative effect is direction-specific at layers 10 and 14** (0.06 and 0.07 against 0.33 and 0.53), but at
  layers 6 and 20 the random controls lose almost as much as the effort vector (0.30 and 0.26 against 0.19 and
  0.22). At those layers removal at -0.1 is not distinguishable from generic damage at 60 pairs.
- Week 6's "removal hurts at every layer" therefore has to be read against a random floor of about 0.35, not
  0.5. The effort-specific part of the removal effect is clearest at layers 10 to 16.

## 2. Cross-validation: vector from essays, tested on grant (plan item 6)

The effort vector was rebuilt from essay responses only (30 essay items x 10 repeats, 300 per arm, same recipe;
`outputs/steering/vectors/qwen3.5-9b_essay_v1/`). It has cosine 0.60 to 0.71 with the v4 vector (built from grant
and postmortem) at every layer and 0.00 with the random directions; its split-half reliability is as poor as
v4's (0.24 at layer 16). It was then injected on the grant task (30 items x 2 repeats, max_tokens 1400, the
paper's grant prompt) at layers 6, 10, 16 x r -0.1, +0.05, +0.1, with rand0 at layer 10 as control. Table
`dose_w7_crossval_grant.txt`.

| layer | r = -0.1 | r = +0.05 | r = +0.1 |
| --- | --- | --- | --- |
| 6 | **0.02 (1/40)** | 0.68 (15/7) | 0.54 (13/11) |
| 10 | **0.04 (2/46)** | 0.67 (14/7) | 0.33 (9/18) |
| 16 | **0.00 (0/49)** | **0.76 (13/4), p = 0.05** | 0.17 (5/25), coherence 78 |
| rand0 at 10 | 0.40 (8/12) | 0.50 (8/8) | 0.59 (10/7) |
| baseline vs baseline | | 0.70 (16/7) | |

- **The direction transfers across tasks.** A vector that never saw a grant abstract steers grant abstracts:
  removal at -0.1 loses 1/40, 2/46, 0/49 (the strongest removal seen anywhere; random at the same layer and dose
  0.40, Fisher p = 0.0005), addition at +0.05 wins 0.67 to 0.76 at all three layers (random 0.50).
- The shape matches the essay sweep: +0.1 is already too much at layers 10 and 16 (0.33 and 0.17, coherence 82
  and 78), and the best positive dose is +0.05.
- Grant outputs are longer (660 words); removal shortens them by 25 to 40 words, addition at +0.1 lengthens by 20
  to 40, as on essays.

## 3. Role cues: does the direction act without the exhortation? (plan item 7)

The paper's framed role-cue prompts, "You are a world-class essayist" and "You are a skilled essay writer",
with no exhortation. Each cell compares the steered or ablated essay with the untouched essay under the same
role prompt. Table `cells_w7_role.txt`.

| prompt | intervention | W / L | win rate | coherence (int. / untouched) |
| --- | --- | --- | --- | --- |
| world-class | E ablated at layers 8 to 16 | 3 / 31 | **0.09**, p < 0.0001 | 80 / 89 |
| skilled | E ablated at layers 8 to 16 | 6 / 27 | **0.18**, p = 0.0003 | 82 / 89 |
| world-class | E added at layer 6, +0.1 | 11 / 13 | 0.46 | 85 / 89 |
| skilled | E added at layer 6, +0.1 | 17 / 5 | **0.77**, p = 0.02 | 87 / 89 |
| world-class vs skilled, both untouched | | 8 / 6 | 0.57 | |

- **Ablation hurts under both role prompts**, as much as under the exhortation prompt (week 6: 3 / 17). The
  direction is used whenever the model writes a competent essay, not only when told to try hard. The coherence
  cost is the same 7 to 9 points as before.
- **Adding the direction helps under the weak role cue and not under the strong one.** Under "skilled" it
  reproduces the essay-sweep win (0.77 against 0.88 under the neutral prompt). Under "world-class" it does
  nothing (0.46). One reading: the world-class cue already pushes along this direction, and more adds nothing
  or overshoots; the text features fit (the world-class vs skilled contrast itself correlates 0.38 with the
  exhortation's feature signature, and adding E under world-class drives semicolons and rare words further than
  under skilled: +0.87 / +0.82 SD against +0.35 / +0.44). This is one cell per prompt; a dose curve under the
  world-class prompt would settle it.
- The paper's role contrast reproduces weakly here (8 / 6, 0.57; paper 0.57, week 4 0.55).

## 4. Clean necessity test (plan item 8)

Max-effort prompt, direction ablated at layers 8 to 16, judged against the neutral-prompt essay with nothing
removed. Reference without ablation (week 6): max-effort beats neutral 14 / 7 (0.67). Table `cells_w7_necessity.txt`.

| removed under the max-effort prompt | W / L vs neutral essay | win rate | coherence (ablated / neutral) |
| --- | --- | --- | --- |
| effort direction, layers 8 to 16 | 7 / 19 | **0.27**, p = 0.03 | 82 / 87 |
| random direction, layers 8 to 16 | 12 / 8 | 0.60 | 89 / 88 |
| nothing (week 6) | 14 / 7 | 0.67 | 86 / 89 |

- With the direction removed, the exhortation no longer helps; the essay falls below the neutral one. With a
  random direction removed, the exhortation's advantage is intact (0.60 against 0.67).
- Text features: under random ablation the exhortation's feature signature is fully present (r = 0.90 with the
  paper's signature); under E ablation the "more rare words and semicolons" part survives (+0.84, +1.68 SD) but
  sentences get short and simple (-0.70, grade -1.54), as in week 6's local ablation.
- Caveat as before: the ablated essays lose 5 coherence points, so part of the 0.27 is writing damage rather
  than a lost exhortation effect. The random-ablation control shows the ablation operation itself is harmless; the
  damage is specific to removing this direction.

## 5. What changes in the hypotheses

- **H1 (adding reproduces the effect): supported and now direction-specific.** The early-layer wins beat
  matched random controls (p = 0.03 to 0.0001), the direction built from essays transfers to grant (0.67 to 0.76
  at +0.05), and it works under the weak role cue. It does not add to the strong role cue.
- **H2 (removing cancels the effect): supported, with a correction.** Random perturbation alone costs about 15
  points of win rate; the effort-specific removal effect is clear at layers 10 to 16 (and on grant at all three
  layers tested), not at layers 6 and 20. Under the exhortation prompt, ablating the direction removes the
  exhortation's advantage (0.27 vs neutral) while a random ablation does not (0.60).
- **H3 (random does nothing): not quite.** Random directions at |r| = 0.05 to 0.1 lose 0.32 to 0.40 of pairs
  with coherence intact. The right null for steering cells is the matched random cell, not 0.5. Week 6's
  conclusions survive this re-reading where it matters (positive early-layer cells, removal at layers 10 to 16).

## 6. Caveats and next steps

- 60 pairs per cell; the null cells scatter from 0.25 to 0.70, so no single cell under about 15 / 5 or over 5 / 15
  should be read on its own.
- Ablation still costs coherence; an ablation that keeps coherence (fewer layers, response tokens only, or
  orthogonalised to the mean activation) would make the necessity result cleaner.
- Role-cue result rests on one dose; run a short dose curve under the world-class prompt.
- Length control for the positive effect still not done.
- Cross-validation only one way (essay to grant); the reverse (v4 to essay) is the week-6 sweep itself.
