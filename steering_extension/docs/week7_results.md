# Week 7 report

Date: 2026-10-30. All eight items of `week7_plan.txt`. Full per-cell tables in `results/2026-10-30_w7/`.

## 0. How to read the tables

Every number is a pairwise comparison. For each topic the model writes one essay with the intervention and one
without, from the same prompt. The paper's three judges pick the better one (both orders, disagreement = tie,
panel majority, panel ties dropped). Win rate = share of resolved pairs won by the intervened essay. 0.50 means
no effect. There is no absolute score. 60 pairs per cell. "Unsteered vs unsteered" rows pair two unsteered essays
from the same prompt and should sit near 0.50. "Random direction" rows use a random vector of the same size.
Coherence is a separate 0 to 100 judge score, given for both sides; unsteered essays score 87 to 89.

The vector is the effort direction (mean hidden state over the answer under the max-effort prompt minus under the
neutral prompt, 300 responses per side). Dose r is the added vector's size as a fraction of the hidden state's
size at that layer; r < 0 removes the direction. Ablation projects the direction out at the listed layers. Model
Qwen3.5-9B, 32 layers. Prompts are the paper's.

Batch cost: 2,700 pairs, 16,200 judge votes, about $30 of judging and $1 of GPU.

## 1. What the texts look like (item 1)

Max-effort prompt, direction ablated at layers 8 to 16, against the untouched max-effort essay (week 6: 3 / 17,
coherence 82 against 88). Four changes in the 17 losing pairs. The register goes purple ("these funds are the
CD4 count of our democracy", coherence 72; "a world burning with data", coherence 62). Specifics are invented
("a turnout of ninety-eight percent", "12 million voices in Canberra"). Broken tokens appear in fluent text
("theregarul routine", "the沉默 is the exception"): 13% of ablated essays, 5% of untouched. More, shorter
sentences at the same length. Coherence stays at 82 because the text is readable and on topic; the quality judges
see overwrought style and fake detail next to a sober twin. Of 60 ablated essays, only two (45, 62) read as
damaged; the rest read as a worse writer.

Neutral prompt, direction removed at layer 16, r = -0.1 (5 / 37, coherence 89 against 89, same length). The
steered essays are textbook essays: "First, Secondly, Thirdly", no title, fewer cases and numbers, stock phrases.
Both essays in a typical pair score 92 on coherence; the judges take the twin 3 to 0. Removal makes the essay
blander, not broken.

Neutral prompt, direction added at layer 6, r = +0.1 (22 / 3, coherence 89 against 89, 415 against 393 words).
More specifics per point ("no minimum wage guarantees, and no sick leave, all while bearing the crushing weight
of business expenses like insurance, taxes, and vehicle maintenance"), shorter sentences, more semicolons and
rare words. No coherence or glitch cost.

## 2. Coherence under every steering form (item 2)

Mean coherence of the steered essays in the week-6 sweep, by dose and layer band (share at or above 80 in
brackets). Unsteered essays in the same run: 87.5 and 88.7 (0.85). The layer split is at 16 because that is where
the sweep's positive effect turned down.

| dose r | layers 6 to 14 | layers 16 to 28 |
| --- | --- | --- |
| -0.2 | 84.8 (0.77) | 88.4 (0.85) |
| -0.1 | 89.0 (0.89) | 89.6 (0.89) |
| -0.05 | 89.1 (0.86) | 88.7 (0.85) |
| +0.025 | 87.4 (0.82) | 87.4 (0.80) |
| +0.05 | 87.5 (0.81) | 86.5 (0.75) |
| +0.075 | 86.3 (0.77) | 85.2 (0.73) |
| +0.1 | 86.0 (0.74) | 84.2 (0.69) |

Other forms: random directions 88.0 to 88.6 at every dose (0.84 to 0.86); multi-layer, position modes and other
readouts 86.8 to 87.8; direction ablated at layers 8 to 16 under any prompt 80 to 82 (0.52 to 0.63); ablated at
all 32 layers 2.4.

Coherence falls with positive dose, more so in the late layers, and at -0.2 in the early layers. It is at or
slightly above unsteered (by 1 to 2 points) for removal at -0.05 and -0.1, inside the spread between unsteered
cells; this is the plainer text of section 1. Ablation is the only form that costs more than 4 points.

## 3. The paper's text features on our outputs (item 3)

Besides the judge win rate, the paper measures text features of every output and reports how they shift under
each prompt contrast. The 14 features, computed here with the paper's own code: words; sentences; words per
sentence; MATTR (moving-average type-token ratio, lexical diversity); unique-word ratio; mean word length;
rare-word rate per 1,000 words (words below a wordfreq Zipf-frequency threshold); numeric specificity per 1,000
(numbers, percentages, currency); semicolons and colons per 1,000; dashes per 1,000; positive and negative
sentiment words per 1,000 (VADER lexicon); Flesch-Kincaid grade; paragraphs. The paper's other metric family,
the utility measures, needs new model calls and is not computed.

For each cell, the value is the paired difference (intervened minus unsteered essay, same topic) divided by the
standard deviation of that difference over the 60 pairs, so +1.0 means the intervention moved the feature up by
one standard deviation. The first column is the paper's own direct-exhortation deltas for Qwen3.5-9B essays.

| feature | paper exhortation | our max-effort vs neutral prompt | add layer 6, +0.1 | remove layer 16, -0.1 | ablate 8 to 16 under max-effort |
| --- | --- | --- | --- | --- | --- |
| words | +0.46 | +0.54 | +0.66 | +0.12 | -0.10 |
| sentences | +0.20 | +0.26 | +1.20 | +0.20 | +0.81 |
| words per sentence | +0.16 | +0.11 | -0.61 | -0.16 | -0.99 |
| rare-word rate | +0.20 | +0.30 | +0.52 | -1.18 | +0.61 |
| semicolons and colons | +0.23 | +0.42 | +0.63 | -0.70 | +1.20 |
| unique-word ratio | -0.19 | -0.30 | +0.22 | -1.06 | -0.09 |
| MATTR | -0.27 | -0.32 | -0.10 | -0.20 | -1.00 |
| positive-sentiment words | -0.14 | -0.21 | -0.30 | +0.49 | -0.63 |
| negative-sentiment words | -0.04 | +0.01 | +0.10 | -0.35 | +0.43 |
| Flesch-Kincaid grade | +0.04 | 0.00 | -0.80 | -0.28 | -1.55 |
| mean word length | -0.20 | -0.11 | -0.32 | -0.03 | -1.37 |
| numeric specificity | -0.01 | -0.05 | +0.10 | -0.18 | +0.27 |
| dashes | +0.12 | +0.12 | +0.21 | -0.38 | +0.20 |
| paragraphs | 0.00 | -0.08 | +0.17 | +0.13 | +0.26 |

Pearson correlation across the 14 features between a cell's column and the paper's exhortation column (all cells
in `feature_deltas_key_cells_w6.csv`):

| cell | correlation with the paper's exhortation column |
| --- | --- |
| our max-effort vs neutral prompt, no steering | +0.96 |
| add at layer 6 / 10 / 14 (+0.1, +0.1, +0.05) | +0.51 / +0.38 / +0.40 |
| add at layer 6, +0.1, under the skilled / world-class prompt | +0.59 / +0.49 |
| remove at layer 16 / 10, -0.1 | -0.03 / -0.43 |
| remove at layer 16, -0.1, prompt tokens only | -0.74 |
| max-effort prompt, direction ablated at 8 to 16 | +0.47 |
| max-effort prompt, random direction ablated | +0.60 to +0.90 |
| random direction at layer 16, -0.1 | -0.04 |

Our pipeline reproduces the paper's signature (longer, more sentences, more rare words and semicolons, fewer
positive-sentiment words). Adding the vector early moves the same features the same way, and also shortens and
simplifies sentences (grade -0.8), which the prompt does not. Removing the vector is not the mirror image: length
unchanged, rare words -1.2, semicolons -0.7, positive words +0.5. Ablation under the exhortation keeps the "more"
(rare words +0.6, semicolons +1.2) and breaks the sentences (words per sentence -1.0, grade -1.6).

## 4. Random controls (item 5)

Neutral prompt. Random directions rand0 and rand1 at layers 6, 10, 14, 20 and r = -0.1, +0.05, +0.1, each against
the unsteered essay from the same topic. Full 24-row table in `w7_random_dose_summary.csv`.

| steered with | W / L | win rate | coherence steered / unsteered |
| --- | --- | --- | --- |
| nothing (unsteered vs unsteered) | 5 / 15 | 0.25 | 86.7 / 89.0 |
| random, r = -0.1, pooled 8 cells | 49 / 92 | 0.35 | 88.6 / 89.0 |
| random, r = +0.05, pooled 8 cells | 41 / 86 | 0.32 | 88.0 / 89.0 |
| random, r = +0.1, pooled 8 cells | 58 / 87 | 0.40 | 88.2 / 89.0 |

Random directions are not neutral: they lose about 0.36 of pairs with coherence intact. The null for a steering
cell is therefore about 0.35, not 0.50. The null cell here (5 / 15) is the low end of the seven null cells across
all runs (11/10, 10/7, 11/13, 10/7, 8/10, 5/15, 16/7; pooled 71 / 69).

Effort vector (week 6) against the pooled random cells at the same layer and dose, Fisher exact:

| layer | r | effort | random | p |
| --- | --- | --- | --- | --- |
| 6 | -0.1 | 0.19 (7/30) | 0.30 (12/28) | 0.30 |
| 6 | +0.1 | 0.88 (22/3) | 0.39 (16/25) | 0.0001 |
| 10 | -0.1 | 0.06 (2/29) | 0.33 (13/27) | 0.009 |
| 10 | +0.1 | 0.82 (18/4) | 0.33 (11/22) | 0.0008 |
| 14 | -0.1 | 0.07 (3/37) | 0.53 (16/14) | 0.00003 |
| 14 | +0.05 | 0.81 (17/4) | 0.26 (9/26) | 0.0001 |
| 20 | -0.1 | 0.22 (7/25) | 0.26 (8/23) | 0.77 |
| 20 | +0.05 | 0.65 (13/7) | 0.21 (6/22) | 0.003 |

The positive effect beats its random control at every early-layer winning cell. The removal effect beats random
at layers 10 and 14, not at 6 and 20, where random loses almost as much.

## 5. Cross-validation: essay-built vector on grant (item 6)

Effort vector rebuilt from essay responses only (cosine 0.6 to 0.7 with the grant-and-postmortem vector), injected
while the model writes grant abstracts from the paper's grant prompt, against the unsteered abstract from the
same item.

| steered with | layer | r = -0.1 | r = +0.05 | r = +0.1 | coherence at -0.1 / +0.05 / +0.1 (unsteered 88) |
| --- | --- | --- | --- | --- | --- |
| nothing (unsteered vs unsteered) | | | 0.70 (16/7) | | 89 |
| essay-built vector | 6 | 0.02 (1/40) | 0.68 (15/7) | 0.54 (13/11) | 89 / 87 / 84 |
| essay-built vector | 10 | 0.04 (2/46) | 0.67 (14/7) | 0.33 (9/18) | 89 / 84 / 82 |
| essay-built vector | 16 | 0.00 (0/49) | 0.76 (13/4) | 0.17 (5/25) | 87 / 86 / 78 |
| random direction | 10 | 0.40 (8/12) | 0.50 (8/8) | 0.59 (10/7) | 89 / 88 / 87 |

The direction transfers: removal loses almost every pair with coherence intact, addition at +0.05 wins 0.67 to
0.76, +0.1 is already too much at layers 10 and 16.

Is it as strong as the original vector on essays? Side by side at the same layers and doses:

| layer | dose | week-6 vector on essays | essay-built vector on grant |
| --- | --- | --- | --- |
| 6 | -0.1 | 0.19 (7/30) | 0.02 (1/40) |
| 10 | -0.1 | 0.06 (2/29) | 0.04 (2/46) |
| 16 | -0.1 | 0.12 (5/37) | 0.00 (0/49) |
| 6 | +0.05 | 0.62 (15/9) | 0.68 (15/7) |
| 10 | +0.05 | 0.67 (12/6) | 0.67 (14/7) |
| 16 | +0.05 | 0.60 (15/10) | 0.76 (13/4) |
| 6 | +0.1 | 0.88 (22/3) | 0.54 (13/11) |
| 10 | +0.1 | 0.82 (18/4) | 0.33 (9/18) |
| 16 | +0.1 | 0.23 (7/23) | 0.17 (5/25) |

Removal is stronger on grant, addition at +0.05 is the same, addition at +0.1 is weaker: the positive peak sits
at a lower dose on grant. Two things differ at once here, the vector and the task, so this does not say which one
moves the peak. The clean comparison, the week-6 vector on grant, was not run.

## 6. Role cues (item 7)

The paper's role prompts ("You are a world-class essayist", "You are a skilled essay writer"), no exhortation.
Each row against the untouched essay written from the same prompt, except the reference row.

| prompt | intervention | opponent | W / L | win rate | coherence int. / opp. |
| --- | --- | --- | --- | --- | --- |
| world-class | ablated at layers 8 to 16 | untouched world-class | 3 / 31 | 0.09 | 80 / 89 |
| skilled | ablated at layers 8 to 16 | untouched skilled | 6 / 27 | 0.18 | 82 / 89 |
| world-class | added at layer 6, +0.1 | untouched world-class | 11 / 13 | 0.46 | 85 / 89 |
| skilled | added at layer 6, +0.1 | untouched skilled | 17 / 5 | 0.77 | 87 / 89 |
| world-class | none (the paper's role contrast) | untouched skilled | 8 / 6 | 0.57 | 89 / 89 |
| neutral (week 6) | added at layer 6, +0.1 | untouched neutral | 22 / 3 | 0.88 | 89 / 89 |

Ablation hurts under both role prompts as much as under the exhortation. Adding helps under the weak cue (0.77)
and not under the strong one (0.46); one reading is that "world-class" already pushes along this direction. One
dose per prompt only.

## 7. Clean necessity test (item 8)

Max-effort prompt with the direction ablated at layers 8 to 16, against the neutral-prompt essay with nothing
removed. Does the exhortation still help once the direction is gone?

| removed while writing | W / L vs neutral essay | win rate | coherence ablated / neutral |
| --- | --- | --- | --- |
| effort direction | 7 / 19 | 0.27 | 82 / 87 |
| random direction | 12 / 8 | 0.60 | 89 / 88 |
| nothing (week 6) | 14 / 7 | 0.67 | 86 / 89 |

With the direction removed the exhortation no longer helps; with a random direction removed it keeps its
advantage. Caveat: the ablated essays lose 5 coherence points, so part of the 0.27 is writing damage.

## 8. Hypotheses after week 7

H1 (adding reproduces the effect): supported and direction-specific. Early-layer wins beat matched random
controls, the direction transfers from essays to grant, and it works under the weak role cue. It moves the
exhortation's text features, plus shorter sentences.

H2 (removing cancels the effect): supported with a correction. Random perturbation alone costs about 15 points;
the effort-specific removal is clear at layers 10 to 16 and on grant, not at layers 6 and 20. Ablating the
direction under the exhortation removes its advantage (0.27 vs neutral); a random ablation does not (0.60).

H3 (random does nothing): not quite. Random directions lose 0.32 to 0.40 with coherence intact. The null for a
steering cell is the matched random cell.

## 9. Caveats and next steps

- 60 pairs per cell; null cells scatter from 0.25 to 0.70. Do not read single cells between 5/15 and 15/5.
- Ablation costs 5 to 9 coherence points. Next: an ablation that keeps coherence, then rerun the necessity cell.
- Role-cue result rests on one dose; run a short dose curve under the world-class prompt.
- Length control for the positive effect still not done (steering adds about 20 words, the exhortation 15).
- Essay and grant, 9B only.
