---
title: "SPAR Week 9 Progress Report"
subtitle: "Where does the coherence loss come from? Does sandbagging run through the effort direction?"
author: "Kacper"
date: "2026-11-18"
---

## This week's goals and how to read every number

Goals from the 07.11 meeting:

1. Look closer at the inverse relation between coherence and win rate under effort steering (note item 1).
2. Ask the coherence judge itself why steered essays that win score lower on coherence (note item 3).
3. Does the effort direction explain the paper's sandbagging? Tested on Qwen3.5-9B and DeepSeek V3.2 (note item 2).
4. Rubric coder on the cross-validation cells (note item 4). Dropped, because the grant rubric has other markers than the essay rubric (no thesis or closure marker), and the essay finding cannot be repeated on grant abstracts.

How to read every number in this deck:

- Every result is a pairwise comparison. For each item and repeat the model writes one text for side a and one for side b. The paper's three judges pick the better one in both orders. Flipped judges count as ties, and pairs the panel ties are dropped. W / L is pairs won / lost by side a. 0.50 means no effect.
- Coherence is a separate 0 to 100 score from claude-haiku-4.5 at temperature 0, told to ignore quality.
- E is the effort vector (max-effort minus neutral prompt, response-token mean). The dose r is a fraction of the layer's residual size. r < 0 removes the direction, r > 0 adds it.
- Sandbagging is the paper's comparison. "Harmful" is the competition prompt with a sponsor who funds a harmful cause, "baseline" is the same competition prompt with no sponsor (the paper's framed-empty arm). Prompts are the paper's, byte for byte.

## Takeaways

- **Adding the effort vector gives a mixture.** 35% of steered essays lose coherence and hold 80% of the losses. The rest keep their coherence and win 0.71 (unsteered pairs 0.44, random direction 0.49).
- **What the coherence judge objects to, and what is specific to effort, is overblown style.** Inflated metaphor and jargon is named in 52% and 38% of its explanations after adding E, against 12% for a random direction and 7% for unsteered pairs. Broken tokens are named as often without steering.
- **Both models sandbag as in the paper.** Qwen's harmful side wins 32 / 78 on grant (paper 51 / 128), and 46% of its harmful-prompt texts are refusals or objections. DeepSeek's harmful side wins 3 / 81 on essay and 5 / 33 on grant, with no refusals.
- **In both models the harmful cause moves the text backward along the effort direction.** The shift is half an exhortation in Qwen and a full one in DeepSeek.
- **Adding effort back closes part of the gap at best, in both models.** In Qwen the harmful abstract wins 0.27 with E against 0.29 without at layer 10. At layers 16 to 20 E helps more than a random direction (78 / 45 against 43 / 65) and the harmful abstract still wins only 0.28 against the baseline. Qwen's sandbagging vector built from clean texts has a cosine of -0.06 to -0.21 with E. In DeepSeek the cosine is -0.45, and adding E at layer 30 raises the harmful essay from 1 / 41 to 8 / 28 and 6 / 23 (two doses) against the baseline.
- **In DeepSeek both the sandbagging and the gain from E are mostly essay length.** The panel picks the longer essay in 85 to 98% of pairs. Harmful essays are 66 words shorter, E adds 22 to 30 words, and at equal length its advantage over a random direction is gone. Qwen's sandbagging is not a length effect.

## 1. Adding E damages some essays, the rest win

![Qwen3.5-9B, essay task. Each steered essay is compared with the unsteered essay for the same topic. "Damaged" means it scores more than 3 coherence points below that partner. Left: E damages 35% of pairs (random direction 22%, unsteered 22%). Right: damaged pairs hold 80% of the losses. At equal coherence E wins 0.71 (random direction 0.49, unsteered 0.44).](results/2026-11-17_w9/1b_mixture.png)

## 2. What the coherence judge objects to in steered essays

The coherence judge compared a steered and an unsteered essay, in both orders, and explained why one is less coherent. The table gives the share of its explanations that name each reason. Qwen3.5-9B, essay task.

| reason named by the judge | E added, essay won the panel (28 pairs) | E added, essay lost the panel (56) | random direction added (41) | unsteered (15) |
|---|---|---|---|---|
| overblown style (inflated metaphor, jargon) | 52% | 38% | 12% | 7% |
| broken tokens (garbled words, foreign characters) | 52% | 68% | 54% | 60% |
| invented specifics (made-up names, numbers) | 16% | 26% | 29% | 17% |

- Overblown style is the one reason specific to the effort direction. Example quoted by the judge: "The friction of blowing dry grass versus the textured allure of blooming native blooms".
- Broken tokens and invented specifics are named as often without steering.
- Caveats. The judge prefers the essay shown first (75% of judgments), so we use only verdicts that hold in both orders. One model sorted the reasons, with no human check.

## 3a. Qwen3.5-9B sandbags as in the paper

Grant task. "Harmful" is the competition prompt with a sponsor who funds a harmful cause, "baseline" is the same prompt with no sponsor. W / L is for the harmful side. "Clean" pairs pass the paper's refusal screen.

| harmful vs baseline | W / L | win rate |
|---|---|---|
| paper, clean pairs | 51 / 128 | 0.28 |
| ours, clean pairs, first three runs | 32 / 78 | 0.29 |
| ours, clean pairs, new run | 14 / 62 | 0.18 |
| ours, refusals and objections counted too | 33 / 234 | 0.12 |

- The paper's result replicates. Clean harmful abstracts lose, with the same coherence and length as the baseline.
- 46% of harmful-prompt texts are refusals or contain an objection. The screen removes them.
- Inside the model, clean harmful abstracts are shifted backward along E, by about half of what the max-effort prompt does forward (Cohen's d -0.6 to -0.9). A random direction shows nothing.

## 3b. Qwen3.5-9B: adding effort does not close the gap

E or a random direction is added under the harmful prompt (r +0.05). Clean pairs, win rate of the steered harmful abstract with W / L in brackets. Layers 16, 18 and 20 are pooled.

| harmful prompt plus | vs baseline, layer 10 | vs baseline, layers 16 to 20 | vs untouched harmful, layer 10 | vs untouched harmful, layers 16 to 20 |
|---|---|---|---|---|
| nothing | 0.29 (32 / 78) | 0.18 (14 / 62) | | |
| E | 0.27 (18 / 49) | 0.28 (55 / 140) | 0.60 (24 / 16) | 0.63 (78 / 45) |
| random direction | 0.16 (14 / 72) | 0.15 (30 / 176) | 0.45 (23 / 28) | 0.40 (43 / 65) |

- The gap stays. With E the harmful abstract wins 0.27 to 0.28 against the baseline, far from 0.50.
- E helps more than a random direction (p < 0.001 at layers 16 to 20, also at equal length). The effect is real and small.
- E also helps under the baseline prompt (0.61 at layer 18), so it may be a general boost and not a fix for sandbagging.

## 4a. DeepSeek V3.2 sandbags as in the paper, with no refusals

We hosted the released checkpoint on 8 rented GPUs, with thinking off and the paper's prompts and panel. Harmful (side a) against baseline (side b).

| task | pairs | W / L | win rate | paper | words a / b | refusals or objections |
|---|---|---|---|---|---|---|
| essay | 120 | 3 / 81 | 0.04 | 0.10 (28 / 251) | 308 / 375 | 0 of 120 |
| grant | 60 | 5 / 33 | 0.13 | 0.31 (92 / 208) | 543 / 584 | 0 of 60 |

- DeepSeek's whole gap is sandbagging. No text is a refusal and coherence is equal (92 on both sides).
- The harmful texts are shorter.

## 4b. DeepSeek V3.2: the harmful cause shifts texts against effort

Untouched texts placed along the effort direction E, essay task, 60 texts per condition. d is Cohen's d. Ratio is the harmful shift divided by the max-effort shift.

| layer | harmful vs baseline: d | max-effort vs neutral: d | ratio | cosine of sandbagging vector with E |
|---|---|---|---|---|
| 12 | -0.32 | +1.66 | -0.21 | -0.19 |
| 20 | -0.36 | +1.17 | -0.31 | about -0.2 |
| 30 | -1.97 | +1.91 | -1.02 | -0.45 |
| 42 | -1.71 | +1.30 | -1.33 | -0.56 |

- From layer 30 on the harmful cause moves texts backward along E as far as the max-effort prompt moves them forward. In Qwen it is half as far.
- A random direction shows nothing (d -0.5 to +0.4).
- The sandbagging vector (harmful minus baseline) points against E. In Qwen the cosine is -0.06 to -0.21.

## 5a. DeepSeek V3.2: adding effort at layer 30 closes part of the gap

Essay task, 60 pairs per cell. E or a random direction is added under the harmful prompt. W / L for the steered harmful essay.

| harmful prompt plus | layer, dose | vs untouched harmful | vs baseline |
|---|---|---|---|
| nothing | | | 1 / 41 (0.02) |
| E | 12, +0.1 | 21 / 10 | 1 / 35 (0.03) |
| E | 20, +0.1 | 20 / 3 | 2 / 33 (0.06) |
| E | 30, +0.05 | 27 / 7 | 8 / 28 (0.22) |
| E | 30, +0.1 | 29 / 1 | 6 / 23 (0.21) |
| random direction | 20, +0.1 | 14 / 9 | 2 / 38 (0.05) |

- Only layer 30 moves the result against the baseline, from 0.02 to 0.22 (two doses together 14 / 51, p = 0.004).
- The gain is partial and did not grow with the dose.
- Caveats. We did not tune layers and doses. The random control is at layer 20, and layer 30 has none.

## 5b. DeepSeek V3.2: the gain is mostly longer essays

Essay task. The panel picks the longer essay in almost every resolved pair.

| | DeepSeek, essay | Qwen, grant |
|---|---|---|
| the longer text wins, harmful vs baseline | 82 of 84 | 112 of 185 |
| words, harmful / baseline | 307 / 373 | 661 / 648 |
| words, harmful + E at layer 30 | 329 to 337 | |
| harmful vs baseline, observed win rate | 0.07 | 0.25 |
| harmful vs baseline, predicted at equal length | 0.35 | 0.21 |

- Harmful essays are 66 words shorter and E adds back 22 to 30 words.
- At equal length E at layer 30 no longer beats the random direction (p = 0.64, before 0.008).
- A gap remains at equal length (0.35 against 0.50), and it is much smaller.
- Qwen's sandbagging is not a length effect.

## Summary: does the effort direction explain sandbagging?

| | Qwen3.5-9B (grant) | DeepSeek V3.2 (essay) |
|---|---|---|
| harmful vs baseline | 0.29 (clean pairs) | 0.04 |
| refusals or objections among harmful texts | 46% | 0% |
| harmful shift along E, relative to the max-effort shift | -0.4 to -0.6 | -1.0 to -1.3 from layer 30 |
| cosine of the sandbagging vector with E | -0.06 to -0.21 | -0.45 at layer 30 |
| harmful + E vs baseline | 0.28 | 0.22 |

- In both models the harmful cause moves texts backward along the effort direction.
- Adding effort back helps in both and closes the gap in neither.
- So the harmful cause leaves a trace on the effort direction, and most of the sandbagging happens elsewhere.

## Open questions and cost

- DeepSeek: can the gap be closed fully? Not run are doses above +0.1, layers 30 to 42 and a random control at layer 30.
- DeepSeek: does the model write worse essays under a harmful cause, or only shorter ones that the judges like less? A run with a fixed word count would separate the two.
- Qwen: steering with the sandbagging vector built from clean texts. The one we used is mostly a refusal vector.
- Does the panel reward the overblown style that E adds, or do steered essays win despite it?
- Cost this week: $43 on OpenRouter and about $156 on vast.ai (DeepSeek $154, Qwen $2.50).

## Backup: Qwen3.5-9B, steering with the sandbagging vector

Grant task, layer 10, 60 pairs per cell. S is the harmful-minus-baseline vector. "S minus E" is S with its E component projected out. "Clean" pairs pass the paper's refusal screen.

| side a | side b | all pairs W / L | clean pairs W / L | coherence a / b |
|---|---|---|---|---|
| harmful, S removed (r -0.1) | untouched harmful | 28 / 15 | 10 / 3 | 90.8 / 90.1 |
| harmful, S minus E removed | untouched harmful | 29 / 14 | 7 / 1 | 90.9 / 89.9 |
| harmful, S removed | baseline | 9 / 31 | 9 / 7 | 90.6 / 88.8 |
| harmful, S minus E removed | baseline | 6 / 31 | 6 / 4 | 88.9 / 88.0 |
| untouched harmful (this run) | baseline | 4 / 36 | 4 / 7 | 90.5 / 88.5 |
| baseline, S added (r +0.1) | untouched baseline | 3 / 27 | 3 / 27 | 89.0 / 88.9 |
| baseline, S minus E added | untouched baseline | 2 / 26 | 2 / 26 | 89.2 / 88.9 |

- Projecting E out of S changes nothing in any cell.
- S is mostly a refusal vector (cosine 0.98 with the vector built from refusal and objection texts, 0.24 to 0.42 with the one built from clean texts). Steering with the clean-text vector was not run.
- Removing S does not stop the refusals. 30 of 60 untouched texts are clean, and 35 and 33 of 60 with S removed.
- The clean cells are small, so this is a direction of effect and not an estimate.

## Backup: hosting DeepSeek V3.2

| item | value |
|---|---|
| machine | 8 x RTX PRO 6000 (95 GiB each) on vast.ai, about $21 per hour |
| checkpoint | as released, FP8, 690 GB, downloaded in 11 minutes |
| load | 183 s, 8 layers per GPU with a cap of 86 GiB per GPU |
| thinking off | prompt ends with the closed think tag, as the chat template does it |
| throughput | 66 tokens per second on essays (batch 48), 47 on grant (batch 24) |
| check of the steering hook | a zero vector reproduces the unsteered text exactly |
| study run | 4 h 40 min, $99.69 including the download fee |
| smoke tests before it | three attempts, $54, of which $33 download fees |
