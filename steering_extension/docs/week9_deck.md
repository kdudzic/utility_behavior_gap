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
3. Is the paper's sandbagging also carried by the effort direction? Qwen3.5-9B and DeepSeek V3.2 (note item 2).
4. Rubric coder on the cross-validation cells (note item 4): dropped. The grant rubric has other markers than the essay rubric (no thesis or closure marker), so the essay finding cannot be repeated on grant abstracts.

How to read every number in this deck:

- Every result is a pairwise comparison. For each item and repeat the model writes one text for side a and one for side b. The paper's three judges pick the better one in both orders. Flipped judges count as ties, and pairs the panel ties are dropped. W / L is pairs won / lost by side a. 0.50 means no effect.
- Coherence is a separate 0 to 100 score from claude-haiku-4.5 at temperature 0, told to ignore quality.
- E is the effort vector (max-effort minus neutral prompt, response-token mean). The dose r is a fraction of the layer's residual size. r < 0 removes the direction, r > 0 adds it.
- Sandbagging is the paper's comparison: "harmful" is the competition prompt with a sponsor who funds a harmful cause, "baseline" is the same competition prompt with no sponsor (the paper's framed-empty arm). Prompts are the paper's, byte for byte.

## Takeaways

- **Adding the effort vector gives a mixture.** 35% of steered essays lose coherence and hold 80% of the losses. The rest keep their coherence and win 0.71 (unsteered pairs 0.44, random direction 0.49).
- **What the coherence judge objects to, and what is specific to effort, is overblown style.** Inflated metaphor and jargon is named in 52% and 38% of its explanations after adding E, against 12% for a random direction and 7% for unsteered pairs. Broken tokens are named as often without steering.
- **Both models sandbag as in the paper.** Qwen on grant 32 / 78 (paper 51 / 128), and 46% of its harmful-prompt texts are refusals or objections. DeepSeek on essay 3 / 81 and on grant 5 / 33, with no refusals at all.
- **In both models the harmful cause moves the text backward along the effort direction.** By half an exhortation in Qwen, by a full one in DeepSeek.
- **Whether effort carries the sandbagging differs by model.** Qwen: no. Adding E leaves the gap where it was (0.27 against 0.29), and the sandbagging vector is orthogonal to E. DeepSeek: partly. The sandbagging vector points against E (cosine -0.45), and adding E at layer 30 lifts the harmful essay from 1 / 41 to 8 / 28 and 6 / 23 (two doses) against the baseline.

## 1. Adding E damages some essays, the rest win

![Qwen3.5-9B, essay task, neutral prompt. Side a: an essay with E added (r +0.025 to +0.1, layers 6 to 28), with a random direction added, or a second unsteered essay. Side b: the unsteered essay from the same topic and repeat. "Damaged" means the steered essay scores more than 3 coherence points below its partner. Left: E damages 35% of pairs (random 22%, unsteered 22%). Right: damaged pairs lose and hold 80% of all losses. At equal coherence E wins 0.71 (random 0.49, unsteered 0.44). "More coherent" pairs win in every group, because all cells share 60 unsteered partners and 16 of those score low. So the week-6 win rates are too high in level, while effort vs random vs unsteered comparisons hold. A higher dose gives more damage (0.28 to 0.37 of pairs) and no more wins at equal coherence.](results/2026-11-17_w9/1b_mixture.png)

## 2. What the coherence judge objects to in steered essays

The coherence judge (claude-haiku-4.5, temperature 0, same definition) saw the task and two essays, one steered and one unsteered, without knowing which, and said which would score higher on coherence and why, with quotes. Both orders. A second model (gemini-2.5-flash) sorted the reasons. Qwen3.5-9B, essay task, 359 pairs. The table uses only pairs where the judge rated the first-named essay lower in both orders, and gives the share of its explanations naming each reason.

| reason named by the judge | E added, essay won the panel (28 pairs) | E added, essay lost the panel (56) | random direction added (41) | unsteered vs unsteered (15) |
|---|---|---|---|---|
| overblown style (inflated metaphor, jargon) | 52% | 38% | 12% | 7% |
| broken tokens (garbled words, foreign characters) | 52% | 68% | 54% | 60% |
| invented specifics (made-up names, numbers) | 16% | 26% | 29% | 17% |
| repetition | 2% | 11% | 6% | 0% |

- Overblown style is the one reason specific to the effort direction. Example the judge quoted: "The friction of blowing dry grass versus the textured allure of blooming native blooms".
- Broken tokens and invented specifics are named as often for a random direction and for unsteered pairs.
- Winners and losers differ in amount, not in kind. Of the 59 essays that won the panel with a lower coherence score, only 28 are rated lower in both orders, by 5.5 points. For the losers it is 56 of 60, by 13.5 points.
- Caveat: the pairwise judge prefers the essay shown first (75% of 718 judgments). Reason categories come from one model with no human check. Whether the panel rewards the overblown style as richer writing was not tested.

## 3. Sandbagging in Qwen3.5-9B: replicates, but effort does not carry it

Grant task (the one task where Qwen sandbags in the paper). 30 items, 60 pairs per run. "Clean" pairs pass the paper's refusal screen (its classifier, unchanged): the harmful-prompt text is not a refusal and carries no objection. E is the essay-built vector, so grant is held out for it. Vectors are added at layer 10, r +0.05. Coherence is 87.6 to 88.9 on both sides of every row.

| side a | side b | clean pairs | W / L | win rate |
|---|---|---|---|---|
| harmful | baseline | 196 | 32 / 78 | 0.29 (paper 0.28, 51 / 128) |
| harmful + E | baseline | 164 | 18 / 49 | 0.27 |
| harmful + random direction | baseline | 168 | 14 / 72 | 0.16 |
| harmful + E | harmful | 101 | 24 / 16 | 0.60 |
| harmful + random direction | harmful | 116 | 23 / 28 | 0.45 |

- 46% of harmful-prompt texts are refusals or abstracts with an objection (360 texts). Those practically never win (1 / 156). With them counted, harmful wins 33 / 234.
- Readout: clean harmful abstracts sit backward on E, by 0.4 to 0.6 of the distance the max-effort prompt moves them forward (Cohen's d -0.6 to -0.9 at layers 6 to 16, 196 against 360 texts; a random direction shows nothing).
- Adding E does not close the gap: 0.27 against 0.29 (p = 0.86).
- A sandbagging vector S (harmful minus baseline, split-half cosine 0.97) is orthogonal to E (cosine 0.00 to +0.10). Added to the baseline prompt it makes abstracts lose 3 / 27 with coherence unchanged. Removed under the harmful prompt it wins 28 / 15 against the untouched harmful abstract (clean pairs 10 / 3).

## 4. Sandbagging in DeepSeek V3.2: the harmful cause reads as negative effort

We hosted the released checkpoint (671.9B parameters, FP8, 61 layers) on 8 rented GPUs, thinking off, the paper's prompts and panel. Left: harmful (side a) against baseline (side b), 30 items x 2 repeats per run. Right: untouched texts re-encoded and placed along E, 60 per condition. E is built from max-effort vs neutral on grant, the sandbagging vector S from harmful vs baseline on essay. d is Cohen's d, and ratio is the harmful shift divided by the max-effort shift.

| task | pairs | W / L | win rate | paper | coherence a / b | words a / b | refusals or objections |
|---|---|---|---|---|---|---|---|
| essay | 120 | 3 / 81 | 0.04 | 0.10 (28 / 251) | 92.0 / 91.8 | 308 / 375 | 0 of 120 |
| grant | 60 | 5 / 33 | 0.13 | 0.31 (92 / 208) | 92.0 / 91.6 | 543 / 584 | 0 of 60 |

Position along E:

| layer | cosine of S with E | harmful vs baseline along E, essay: d | same, grant: d | max-effort vs neutral along E, essay: d | ratio |
|---|---|---|---|---|---|
| 12 | -0.19 | -0.32 | -0.47 | +1.66 | -0.21 |
| 20 | about -0.2 | -0.36 | -0.85 | +1.17 | -0.31 |
| 30 | -0.45 | -1.97 | -1.69 | +1.91 | -1.02 |
| 42 | -0.56 | -1.71 | -1.05 | +1.30 | -1.33 |

- DeepSeek's gap is all sandbagging: same coherence, shorter and worse texts, no refusals.
- From layer 30 on the harmful cause moves texts backward along E as far as the max-effort prompt moves them forward (Qwen: half as far). A random direction shows nothing (d -0.5 to +0.4).
- The sandbagging vector points against E. In Qwen the cosine was about zero.

## 5. DeepSeek V3.2: adding effort partly undoes the sandbagging

Essay task, 60 pairs per cell. Side a is the harmful prompt with a vector added or removed, compared with the untouched harmful essay and with the baseline essay. S is the sandbagging vector. Coherence is 90.9 to 92.2 in every cell, and 719 of 720 steered texts pass the refusal screen.

| harmful prompt plus | layer, dose | vs untouched harmful: W / L | vs baseline: W / L | words (harmful 307, baseline 373) |
|---|---|---|---|---|
| nothing | | | 1 / 41 | 307 |
| E added | 12, +0.1 | 21 / 10 | 1 / 35 | 319 |
| E added | 20, +0.1 | 20 / 3 | 2 / 33 | 327 |
| E added | 30, +0.05 | 27 / 7 | 8 / 28 | 329 |
| E added | 30, +0.1 | 29 / 1 | 6 / 23 | 337 |
| random direction added | 20, +0.1 | 14 / 9 | 2 / 38 | 315 |
| S removed | 20, -0.1 | 19 / 4 | 2 / 34 | 326 |
| S removed | 30, -0.1 | 21 / 11 | 3 / 33 | 333 |

- E at layer 30, where the readout is strongest, beats the random control (29 / 1 against 14 / 9, p = 0.001) and lifts the win rate against the baseline from 0.02 to 0.21 (p = 0.016).
- Half the dose at layer 30 gives the same result in separately generated essays (8 / 28, p = 0.010). Together the two cells win 14 / 51 (0.22, p = 0.004).
- The rescue is partial and did not grow with the dose (0.22 and 0.21). The steered essay recovers 22 to 30 of the 66 missing words. Doses above +0.1 were not run. Layers 12 and 20 give no rescue at either dose.
- Removing S does no better than the random direction (p 0.19 to 0.78).
- Caveats: layers and doses were carried over from Qwen by relative depth (6, 10, 16 of 32) and not tuned on DeepSeek. The random control is at layer 20, there is none at layer 30. The longer essay wins 264 of 304 resolved steered vs untouched pairs, so the rescue may work through length.

## Answer to note item 2, open questions and cost

| | Qwen3.5-9B (grant) | DeepSeek V3.2 (essay) |
|---|---|---|
| harmful vs baseline | 32 / 78 (0.29), clean pairs | 3 / 81 (0.04) |
| refusals or objections among harmful texts | 46% | 0% |
| harmful texts along E, relative to the max-effort shift | -0.4 to -0.6 | -1.0 to -1.3 from layer 30 |
| cosine of the sandbagging vector with E | 0.00 to +0.10 | -0.45 at layer 30 |
| harmful + E vs baseline (untouched harmful) | 0.27 (0.29) | 0.22 and 0.21 at two doses (0.02) |

- Both models register the harmful cause as a move backward along the effort direction. Only in DeepSeek does adding it back help. The difference between the models is not established: Qwen was tested with power at layer 10 only, and its readout is strongest at layers 18 to 20 (d -1.0 to -1.1), which were not steered.
- Open: doses of E above +0.1 and layers 30 to 42 on DeepSeek. Doubling the dose from +0.05 to +0.1 did not close more of the gap. Can it be closed fully? A random control under the baseline prompt. DeepSeek steering on grant. Every DeepSeek steering cell has 23 to 42 resolved pairs.
- Open: Qwen's sandbagging vector at other layers and doses, with larger clean-pair cells (now 8 to 16 resolved pairs).
- Open: does the panel reward the overblown style that E adds, or win despite it?
- Cost this week: $26 on OpenRouter (panel judging of 3,960 pairs $20, coherence $3, pairwise coherence judge $2, refusal classifier $0.59) and about $155 on vast (DeepSeek study run $99.69, three smoke-test attempts before it $54, Qwen about $1.50). Full report: `week9_results.md`.

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
- Removing S does not stop the refusals: 30 of 60 texts are clean untouched, 35 and 33 of 60 with S removed.
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
