---
title: "SPAR Week 7 Progress Report"
subtitle: "Effort vector: what the texts look like, random controls, transfer to grant, role cues, necessity"
author: "Kacper"
date: "2026-10-31"
---

## This week's goals (from the meeting notes)

1. Qualitative study: what changes in the text when the effort direction is removed at layers 8 to 16, and why coherence stays high while the score drops.
2. Coherence under every form of steering tried so far.
3. The paper's other metrics (its text features) applied to our steered and ablated outputs.
4. Random-direction controls across the sweep grid, not only at layer 16.
5. Cross-validation: build the vector from essays, test it on another task (grant).
6. Ablate and add the vector under the paper's role-cue prompts ("world-class", "skilled").
7. The clean necessity test: ablated exhortation essay against a neutral essay.
8. One explainer document listing every experiment so far (`docs/experiments_explainer.md`).

## How to read every number

- Every number is a pairwise comparison. For each topic the model writes one essay with the intervention and one without, from the same prompt. The paper's three judges pick the better one. Win rate = share of resolved pairs the intervened essay won. 0.50 means no effect. There is no absolute score.
- 60 pairs per cell. "Unsteered vs unsteered" rows pair two unsteered essays from the same prompt and should sit near 0.50.
- "Random direction" rows apply the same dose with a random vector of the same size. They show how much comes from perturbing the model at all.
- Coherence is a separate judge's 0 to 100 score for readable, on-topic text, given for both essays. Unsteered essays score 87 to 89.
- The vector is the effort direction: average hidden state while answering the max-effort prompt minus the neutral prompt. Dose r is the vector's size as a fraction of the hidden state's size at that layer; r < 0 removes the direction. Ablation projects the direction out at the listed layers. Qwen3.5-9B, 32 layers.

## Takeaways

- Removing the direction makes essays bland, not broken. Ablating it under the exhortation makes them overwrought, with invented statistics and 13% broken tokens, at coherence 82.
- Random directions are not harmless. They lose 0.36 of pairs with coherence intact. The null for a steering cell is about 0.35, not 0.50.
- Against that null, adding the direction at layers 6 to 14 is still a clear win (22 / 3 against 16 / 25 for random at layer 6). Removal is direction-specific at layers 10 to 16, not at 6 and 20.
- A vector built from essays steers grant abstracts: removal 0 / 49 at layer 16, addition at +0.05 wins 0.76.
- Under the paper's role prompts, ablation hurts as much as under the exhortation. Adding helps under "skilled" (17 / 5) but not under "world-class" (11 / 13).
- With the direction ablated, the exhortation no longer beats the neutral prompt (7 / 19). With a random direction ablated, it still does (12 / 8).

## What the texts look like

Max-effort prompt, direction ablated at layers 8 to 16, against the untouched max-effort essay (3 / 17). Four changes:

- Purple register: "these funds are the CD4 count of our democracy" (coherence 72), "a world burning with data" (62).
- Invented specifics: "a turnout of ninety-eight percent", "12 million voices in Canberra".
- Broken tokens in fluent text: "theregarul routine", "the沉默 is the exception". 13% of ablated essays, 5% of untouched.
- More, shorter sentences at the same length.

Coherence stays at 82 because the text is readable and on topic. The quality judges see overwrought style and fake detail next to a sober twin. Of 60 ablated essays, two read as damaged (45, 62); the rest read as a worse writer.

Removing the direction by steering (neutral prompt, layer 16, r = -0.1; 5 / 37) looks different: textbook essays, "First, Secondly, Thirdly", no title, fewer cases and numbers. Both essays in a typical pair score 92 on coherence; the judges take the twin 3 to 0.

## Coherence by dose and layer

Mean coherence of steered essays in the week-6 sweep (share at or above 80 in brackets). Unsteered: 87.5 and 88.7 (0.85).

| dose r | layers 6 to 14 | layers 16 to 28 |
|---|---|---|
| -0.2 | 84.8 (0.77) | 88.4 (0.85) |
| -0.1 | 89.0 (0.89) | 89.6 (0.89) |
| -0.05 | 89.1 (0.86) | 88.7 (0.85) |
| +0.025 | 87.4 (0.82) | 87.4 (0.80) |
| +0.05 | 87.5 (0.81) | 86.5 (0.75) |
| +0.075 | 86.3 (0.77) | 85.2 (0.73) |
| +0.1 | 86.0 (0.74) | 84.2 (0.69) |

- Random directions: 88.0 to 88.6 at every dose. Direction ablated at layers 8 to 16, any prompt: 80 to 82. Ablated at all 32 layers: 2.4.
- Coherence falls with positive dose, more in the late layers. Removal at -0.05 and -0.1 sits 1 to 2 points above unsteered: plainer text.

## The paper's text features on our outputs

The paper measures 14 text features of every output (length, sentences, rare words, semicolons, sentiment words, readability, and so on). Same code here. Values: paired difference (intervened minus unsteered) in standard deviations.

| feature | paper's exhortation | our exhortation prompt | add layer 6, +0.1 | remove layer 16, -0.1 | ablate 8 to 16 under exhortation |
|---|---|---|---|---|---|
| words | +0.46 | +0.54 | +0.66 | +0.12 | -0.10 |
| sentences | +0.20 | +0.26 | +1.20 | +0.20 | +0.81 |
| words per sentence | +0.16 | +0.11 | -0.61 | -0.16 | -0.99 |
| rare-word rate | +0.20 | +0.30 | +0.52 | -1.18 | +0.61 |
| semicolons and colons | +0.23 | +0.42 | +0.63 | -0.70 | +1.20 |
| positive-sentiment words | -0.14 | -0.21 | -0.30 | +0.49 | -0.63 |
| Flesch-Kincaid grade | +0.04 | 0.00 | -0.80 | -0.28 | -1.55 |
| correlation with paper's column | 1 | +0.96 | +0.51 | -0.03 | +0.47 |

- Our pipeline reproduces the paper's signature. Adding the vector early moves the same features the same way, plus shorter and simpler sentences.
- Removing is not the mirror image: length unchanged, vocabulary flattened. Ablation keeps the "more" and breaks the sentences.

## Random controls across the grid

Neutral prompt. Random directions at layers 6, 10, 14, 20 and r = -0.1, +0.05, +0.1, each against the unsteered essay from the same topic.

| steered with | W / L | win rate | coherence steered / unsteered |
|---|---|---|---|
| nothing (unsteered vs unsteered) | 5 / 15 | 0.25 | 86.7 / 89.0 |
| random, r = -0.1, 8 cells pooled | 49 / 92 | 0.35 | 88.6 / 89.0 |
| random, r = +0.05, 8 cells pooled | 41 / 86 | 0.32 | 88.0 / 89.0 |
| random, r = +0.1, 8 cells pooled | 58 / 87 | 0.40 | 88.2 / 89.0 |

Effort vector (week 6) against random at the same layer and dose:

| layer | r | effort | random | p |
|---|---|---|---|---|
| 6 | +0.1 | 0.88 (22/3) | 0.39 (16/25) | 0.0001 |
| 10 | +0.1 | 0.82 (18/4) | 0.33 (11/22) | 0.0008 |
| 14 | +0.05 | 0.81 (17/4) | 0.26 (9/26) | 0.0001 |
| 10 | -0.1 | 0.06 (2/29) | 0.33 (13/27) | 0.009 |
| 14 | -0.1 | 0.07 (3/37) | 0.53 (16/14) | 0.00003 |
| 6 | -0.1 | 0.19 (7/30) | 0.30 (12/28) | 0.30 |
| 20 | -0.1 | 0.22 (7/25) | 0.26 (8/23) | 0.77 |

## Cross-validation: essay-built vector on grant

Vector rebuilt from essay responses only (cosine 0.6 to 0.7 with the grant-and-postmortem vector), injected while the model writes grant abstracts, against the unsteered abstract from the same item.

| steered with | layer | r = -0.1 | r = +0.05 | r = +0.1 |
|---|---|---|---|---|
| nothing (unsteered vs unsteered) | | | 0.70 (16/7) | |
| essay-built vector | 6 | 0.02 (1/40) | 0.68 (15/7) | 0.54 (13/11) |
| essay-built vector | 10 | 0.04 (2/46) | 0.67 (14/7) | 0.33 (9/18) |
| essay-built vector | 16 | 0.00 (0/49) | 0.76 (13/4) | 0.17 (5/25) |
| random direction | 10 | 0.40 (8/12) | 0.50 (8/8) | 0.59 (10/7) |

- Coherence stays at 87 to 89 for removal; drops to 78 to 84 at +0.1.
- Against the week-6 vector on essays at the same cells: removal is stronger on grant (0.19 / 0.06 / 0.12 on essays), +0.05 the same (0.62 / 0.67 / 0.60), +0.1 weaker (0.88 / 0.82 / 0.23). Vector and task differ at once, so this does not say which one moves the peak.

## Role cues: the direction without the exhortation

The paper's role prompts, "You are a world-class essayist" and "You are a skilled essay writer", no exhortation. Each row against the untouched essay from the same prompt, except the reference row.

| prompt | intervention | opponent | W / L | win rate | coherence int. / opp. |
|---|---|---|---|---|---|
| world-class | ablated at layers 8 to 16 | untouched world-class | 3 / 31 | 0.09 | 80 / 89 |
| skilled | ablated at layers 8 to 16 | untouched skilled | 6 / 27 | 0.18 | 82 / 89 |
| world-class | added at layer 6, +0.1 | untouched world-class | 11 / 13 | 0.46 | 85 / 89 |
| skilled | added at layer 6, +0.1 | untouched skilled | 17 / 5 | 0.77 | 87 / 89 |
| world-class | none (paper's role contrast) | untouched skilled | 8 / 6 | 0.57 | 89 / 89 |
| neutral (week 6) | added at layer 6, +0.1 | untouched neutral | 22 / 3 | 0.88 | 89 / 89 |

- Ablation hurts under both role prompts as much as under the exhortation. The model uses this direction whenever it writes a competent essay.
- Adding helps under the weak cue and not under the strong one. One reading: "world-class" already pushes along this direction. One dose per prompt only.

## Clean necessity test

Max-effort prompt with the direction ablated at layers 8 to 16, against the neutral-prompt essay with nothing removed. Does the exhortation still help once the direction is gone?

| removed while writing | W / L vs neutral essay | win rate | coherence ablated / neutral |
|---|---|---|---|
| effort direction | 7 / 19 | 0.27 | 82 / 87 |
| random direction | 12 / 8 | 0.60 | 89 / 88 |
| nothing (week 6) | 14 / 7 | 0.67 | 86 / 89 |

- With the direction removed, the exhortation no longer helps. With a random direction removed, it keeps its advantage. The ablated essays lose 5 coherence points, so part of the drop is writing damage.
- Where the hypotheses stand: adding reproduces the effect and beats matched random controls, transfers to grant, works under the weak role cue (H1). Removing cancels it, specific to the direction at layers 10 to 16 and under the exhortation prompt (H2). Random directions are not neutral, so the matched random cell is the null (H3 revised).
