---
title: "SPAR Week 6 Progress Report"
subtitle: "Effort direction in Qwen3.5-9B: full dose-response sweep, multi-layer, positions, readouts, ablation"
author: "Kacper"
date: "2026-10-27"
---

## Personal updates

- (fill in)

## This week's takeaways

**Removing the old vector hurts at almost every layer. Adding it helps only in the early layers.**

- Full dose curve at 12 layers. Removal at r = -0.1 loses at layers 6 to 20, with win rates of 0.06 to 0.22 and p < 0.003 everywhere.
- Adding helps early. Layer 6 reaches 22 / 3 at +0.1, layer 10 reaches 18 / 4, layer 14 reaches 17 / 4 at +0.05. From layer 16 on, a larger dose makes the essay worse.
- Steering only the prompt tokens already works for removal (0.29). Prompt and response together is the strongest removal yet (1 / 47).
- Six other pre-response readouts were tried. None of them steers.
- Removing the direction at every layer breaks the model. Removing it at layers 8 to 16 only, under the real exhortation prompt, the essay loses 3 / 17.

## What was run

Everything on Qwen3.5-9B, essay task, the paper's prompts and judges, 60 pairs per cell (30 items x 2 repeats).

| plan item | run | pairs |
|---|---|---|
| 1. full dose-response sweep | 12 layers x 7 doses, plus random controls | 5,340 |
| 2. more data | vector rebuilt from 300 responses per side (was 120) | - |
| 3. several layers at once | 3 layer sets x 2 doses | 360 |
| 4. ablation under the exhortation prompt | all layers; layers 8 to 16 | 300 |
| 5. other pre-response readouts | 7 readouts x 2 doses | 900 |
| 6. where to inject | prompt only; prompt and response | 300 |

In total 7,380 pairs, 44,280 judge votes and 7,980 coherence scores. About $65 of judging and $1 of GPU time.

## Sweep: win rate by layer and dose

![](results/2026-10-27_w6_sweep/dose_heatmap.png)

## Sweep: dose curves per layer

![](results/2026-10-27_w6_sweep/dose_curves_by_layer.png)

## Sweep: numbers

Win rate of the steered essay, with W / L of resolved pairs. Bold marks p < 0.01.

| layer | -0.2 | -0.1 | -0.05 | +0.05 | +0.1 |
|---|---|---|---|---|---|
| 6 | 0.00 (0/54) | 0.19 (7/30) | 0.41 | 0.62 (15/9) | **0.88 (22/3)** |
| 10 | 0.00 (0/56) | **0.06 (2/29)** | 0.38 | 0.67 (12/6) | **0.82 (18/4)** |
| 14 | 0.00 (0/57) | **0.08 (3/37)** | 0.32 | **0.81 (17/4)** | 0.52 |
| 16 | 0.00 (0/56) | **0.12 (5/37)** | 0.26 | 0.60 (15/10) | 0.23 (7/23) |
| 20 | 0.02 (1/46) | **0.22 (7/25)** | 0.38 | 0.65 (13/7) | 0.33 |
| 24 | 0.09 (3/32) | 0.28 (7/18) | 0.36 | 0.60 | 0.43 |
| 28 | 0.29 (7/17) | 0.29 | 0.38 | 0.42 | 0.59 |
| random @16 | | 0.55, 0.42 | | 0.35, 0.50 | |

Baseline against baseline gives 0.52 (11 / 10).

## Sweep: is it just broken text?

- At -0.1 it is not. Keeping only pairs where both essays score at least 80 on coherence, the steered side still wins 0 to 13% at layers 8 to 18 (layer 12 is 0 / 24, layer 16 is 1 / 30).
- At -0.2 it partly is. The essays get shorter (352 to 380 words against 393) and less coherent (mean 83 to 86).
- Adding at layer 6 with +0.1 keeps 16 / 1 among coherent pairs. These essays are also longer (415 words against 393). Judges may like length. This is not separated yet.
- From layer 14 on, length stays within 10 words of the baseline.

## More data: did it change the vector?

Same cells as last week, same day, layer 16.

| vector | remove (-0.1) | add (+0.05) |
|---|---|---|
| 120 responses per side (last week's build) | 0.10 (3 / 28) | 0.62 (16 / 10) |
| 300 responses per side (new build) | 0.12 (5 / 37) | 0.60 (15 / 10) |
| last week's run, for reference | 0.06 (2 / 32) | 0.57 (12 / 9) |

- The result is the same. The cosine between the two builds is 0.71 to 0.84 across layers.
- The noise is in the judging, not in the vector.

## Several layers at once

The same total dose, split evenly across the layers.

| layers | remove (-0.1) | add (+0.05) |
|---|---|---|
| 12 + 16 + 20 | 0.14 (5 / 30) | 0.50 (10 / 10) |
| 14 + 16 + 18 | - | 0.62 (13 / 8) |
| 8, 10, ..., 24 (9 layers) | 0.19 (6 / 26) | 0.65 (13 / 7) |
| layer 16 alone | 0.12 (5 / 37) | 0.60 (15 / 10) |

- No gain over one layer, and no loss either.

## Where to inject

Layer 16. Until now the vector was added only while the model writes.

| added to | remove (-0.1) | add (+0.05) |
|---|---|---|
| response tokens only (the old way) | 0.12 (5 / 37) | 0.60 |
| prompt tokens only | 0.29 (8 / 20), p = 0.04 | 0.57 |
| prompt and response | **0.02 (1 / 47)** | 0.54 |

- Adding the vector while the model reads the prompt, and never while it writes, already hurts the essay.
- Both together is the strongest removal seen so far. Coherence is unchanged (88 to 89).
- For adding, the three modes give the same result at this sample size.

## Other pre-response readouts

Vectors read at single tokens near the end of the prompt, and at the first written token. Layer 16, r = -0.1 and +0.1.

| readout | remove | add |
|---|---|---|
| assistant-start token (last week's new vector) | 0.44 | 0.35 |
| `</think>` | 0.57 | 0.43 |
| newline after `</think>` | 0.26 (p = 0.06) | 0.54 |
| `<think>` | 0.43 | 0.45 |
| `assistant` | 0.47 | 0.57 |
| first written token | 0.33 | 0.65 (p = 0.21) |
| response average, for comparison | **0.12** | 0.23 |

- None of them steers. These are the readouts that build the same way every time (split-half 0.9 to 1.0).
- Tested at one layer only. Adding worked best at layers 6 to 14, not at 16.

## Ablation under the real exhortation prompt

The model gets the max-effort prompt and the direction is projected out of every block output.

| removed at | compared with | W / L | win rate | coherence |
|---|---|---|---|---|
| all 32 layers | untouched max-effort | 0 / 60 | 0.00 | **2** (gibberish) |
| all 32 layers, random direction | untouched max-effort | 13 / 10 | 0.57 | 88 |
| layers 8 to 16 | untouched max-effort | 3 / 17 | **0.15**, p = 0.003 | 82 (baseline 88) |
| nothing (max-effort against neutral) | neutral prompt | 14 / 7 | 0.67, p = 0.19 | 86 |

- Removing the direction at every layer breaks the model. The output is a few dozen tokens of newlines. A random direction does no harm, so the breakage is specific to this direction, but the cell tells us nothing about effort.
- Removing at layers 8 to 16 keeps the text readable and the essay loses. Coherence dips a little, so some of the loss can be damage.
- The clean test, ablated max-effort against the neutral prompt, still needs a run with the local ablation.

## What it means

- H2, removal cancels the effect, is supported at 10 of 12 layers with a full dose curve, and now also under the real exhortation prompt.
- H1, adding reproduces the effect, is supported at layers 6 to 14, with a monotonic curve at layer 6. It fails from layer 16 on.
- H3, a random direction does nothing, is supported, but random controls exist only at layer 16.
- The direction matters while the model reads the prompt, not only while it writes.
- Only the response-average readout steers. A readout that builds reliably is not the same as a readout that steers.

## Caveats

- Random controls exist at one layer only. The strong early-layer cells need their own.
- Each cell has 60 pairs and 30 to 45 ties, so single cells have wide intervals. The shape across neighbouring cells is reliable, a single cell is not.
- Adding at early layers makes essays about 20 words longer. Judges may reward length.
- Readouts were tried at one layer and one dose. Positions were tried at one layer.
- Essay task and the 9B model only.

## Next

- Random controls at layers 6, 10 and 14.
- An ablation that does not break the model, compared against the neutral prompt.
- A length control for the early-layer effect.
- Readout vectors at layers 8 to 10.
- Decide whether the 9B result is worth repeating at 27B.
