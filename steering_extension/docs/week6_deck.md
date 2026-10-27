---
title: "SPAR Week 6 Progress Report"
subtitle: "Effort direction in Qwen3.5-9B: full dose-response sweep, multi-layer, positions, readouts, ablation"
author: "Kacper"
date: "2026-10-27"
---

## Goals for this week (from the week-6 plan)

1. Full dose-response sweep of the "old" vector on the 9B model: the whole signed dose grid, not just -0.1 and +0.05, at every second layer.
2. Generate more extraction data and use it.
3. Test injection at several layers at once.
4. Remove the exhortation vector completely while using the exhortation prompt.
5. Try other tokens near the start of the answer as the readout for the pre-response vector (newline, end of assistant tag).
6. Check where we inject: generated tokens only (current), prompt tokens only, and both.

All six were run this week.

## Setup: how to read every number in this deck

- The vector is the "old" effort direction: mean hidden state over the model's own answer tokens, max-effort prompt minus neutral prompt, built from 300 grant and postmortem responses per side (was 120 last week).
- Steering adds the vector to one layer's output while the model writes an essay. Qwen3.5-9B has 32 layers. The sweep uses every second layer from 6 to 28.
- Dose r is the size of the added vector as a fraction of the hidden state's typical size at that layer. Positive r adds the direction, negative r removes it. Last week used only -0.1 and +0.05; this week 7 doses from -0.2 to +0.1.
- Win rate: share of pairs in which the paper's three judges prefer the steered essay over an unsteered essay on the same topic. 60 pairs per cell (30 essay prompts x 2). Ties are dropped, so "22 / 3" means 22 wins, 3 losses, 35 ties.
- Coherence: a separate judge scores each essay 0 to 100 for readable, on-topic text.

## This week's takeaways

**Removing the direction hurts essays at almost every layer. Adding it helps only in the early layers.**

- Removal at r = -0.1 makes essays lose at every layer from 6 to 20 (win rates 0.06 to 0.22, p < 0.003 each). At -0.2 nearly every resolved pair is lost.
- Adding helps at layers 6 to 14. Layer 6 at +0.1 wins 22 / 3, layer 10 at +0.1 wins 18 / 4, layer 14 at +0.05 wins 17 / 4. From layer 16 on, larger doses make essays worse.
- Adding the vector only while the model reads the prompt, never while it writes, already hurts essays (0.29). Reading and writing together gives the strongest removal yet (1 / 47).
- Six other ways to read the vector out of the prompt were tried. None steers.
- Removing the direction at all 32 layers under the real exhortation prompt breaks the model into gibberish. Removing it at layers 8 to 16 only keeps the text readable and the essay loses 3 / 17.
- 7,380 pairs, 44,280 judge votes, about $65 of judging and $1 of GPU.

## Sweep: win rate by layer and dose

Each cell: 60 steered essays against 60 unsteered essays, same prompts. Blue means the judges preferred the steered essay, red the unsteered one. Numbers are win rate and wins / losses.

![](results/2026-10-27_w6_sweep/dose_heatmap.png)

## Sweep: numbers and the "broken text" check

Win rate of the steered essay, wins / losses in brackets. Bold marks p < 0.01. Last week's cells were -0.1 and +0.05 at layers 8 to 24.

| layer (of 32) | r = -0.2 | r = -0.1 | r = +0.05 | r = +0.1 |
|---|---|---|---|---|
| 6 | 0.00 (0/54) | 0.19 (7/30) | 0.62 (15/9) | **0.88 (22/3)** |
| 10 | 0.00 (0/56) | **0.06 (2/29)** | 0.67 (12/6) | **0.82 (18/4)** |
| 14 | 0.00 (0/57) | **0.08 (3/37)** | **0.81 (17/4)** | 0.52 (13/12) |
| 16 | 0.00 (0/56) | **0.12 (5/37)** | 0.60 (15/10) | 0.23 (7/23) |
| 20 | 0.02 (1/46) | **0.22 (7/25)** | 0.65 (13/7) | 0.33 (10/20) |
| 24 | 0.09 (3/32) | 0.28 (7/18) | 0.60 (9/6) | 0.43 (10/13) |
| random direction, layer 16 | | 0.55, 0.42 | 0.35, 0.50 | |

- Removal at -0.1 is not broken text. Keeping only pairs where both essays score at least 80 on coherence, the steered essay still wins 0 to 13% at layers 8 to 18.
- Removal at -0.2 is partly broken text. Those essays are shorter (352 to 380 words against 393) and less coherent (mean 83 to 86 against 88).
- Adding at layer 6 (+0.1) keeps 16 / 1 among coherent pairs, but those essays are 20 words longer. Judges may reward length. Not separated yet.

## Where to inject, and several layers at once

All at layer 16, the layer used in weeks 4 and 5. Win rate of the steered essay.

| change from the old way | r = -0.1 (remove) | r = +0.05 (add) |
|---|---|---|
| old way: vector added only while the model writes | 0.12 (5/37) | 0.60 (15/10) |
| added only while the model reads the prompt | 0.29 (8/20), p = 0.04 | 0.57 (13/10) |
| added while reading and while writing | **0.02 (1/47)** | 0.54 (14/12) |
| same total dose split over layers 12, 16, 20 | 0.14 (5/30) | 0.50 (10/10) |
| same total dose split over 9 layers, 8 to 24 | 0.19 (6/26) | 0.65 (13/7) |

- The direction already acts while the model reads the prompt, with nothing added during writing.
- Spreading the dose over several layers changes nothing compared with layer 16 alone.
- Coherence stays at 85 to 89 in all of these cells.

## Vector variants: more data, other readouts

More data: the vector rebuilt from 300 responses per side instead of 120 gives the same essay results at layer 16 (remove 0.12 against 0.10, add 0.60 against 0.62). The two builds have cosine 0.71 to 0.84 across layers. The noise is in the judging, not in the vector.

Other readouts: the same contrast read at one token of the prompt template instead of averaged over the answer. Layer 16, r = -0.1 and +0.1.

| readout position | remove | add |
|---|---|---|
| last prompt token (last week's "new" vector) | 0.44 | 0.35 |
| `</think>` token | 0.57 | 0.43 |
| newline after `</think>` | 0.26 (p = 0.06) | 0.54 |
| `assistant` token | 0.47 | 0.57 |
| first token the model writes | 0.33 | 0.65 (p = 0.21) |
| answer average, for comparison | **0.12** | 0.23 |

- None of the single-token readouts steers at this layer, although these are the readouts that build the same way every time (split-half 0.9 to 1.0). Not yet tried at layers 6 to 14, where adding worked best.

## Ablation under the real exhortation prompt

The model gets the max-effort prompt. The effort direction is projected out of the hidden state at the listed layers, at every token. Each ablated essay is judged against a fresh essay from the same prompt.

| direction removed at | judged against | wins / losses | win rate | coherence |
|---|---|---|---|---|
| all 32 layers | untouched max-effort essay | 0 / 60 | 0.00 | 2 (gibberish) |
| all 32 layers, random direction | untouched max-effort essay | 13 / 10 | 0.57 | 88 |
| layers 8 to 16 | untouched max-effort essay | 3 / 17 | **0.15**, p = 0.003 | 82 (untouched: 88) |
| nothing | neutral-prompt essay | 14 / 7 | 0.67, p = 0.19 | 86 |

- Removing the direction at every layer destroys the output (a few dozen tokens of newlines). A random direction does no harm, so the damage is specific to this direction, but that cell says nothing about effort.
- Removing it at layers 8 to 16 keeps the text readable, and the essay loses. Coherence dips from 88 to 82, so part of the loss may be damage.
- The clean test, ablated max-effort essay against a neutral-prompt essay, still needs a run with the local ablation.

## What it means, and what to doubt

- H2, removing the direction cancels the effect: supported at 10 of 12 layers with a full dose curve, and now also under the real exhortation prompt.
- H1, adding the direction reproduces the effect: supported at layers 6 to 14, with a monotonic curve at layer 6. Fails from layer 16 on.
- H3, a random direction does nothing: supported, but random controls exist only at layer 16. The strong early-layer cells need their own.
- The direction matters while the model reads the prompt, not only while it writes.
- Only the answer-average readout steers. A readout that builds reliably is not the same as one that steers.
- Each cell has 60 pairs and 30 to 45 ties, so single cells have wide intervals. The shape across neighbouring cells is reliable, a single cell is not.
- Essay task and the 9B model only.

## Next

- Random controls at layers 6, 10 and 14.
- An ablation that does not break the model, judged against the neutral prompt.
- A length control for the early-layer effect.
- Readout vectors at layers 8 to 10.
- Decide whether the 9B result is worth repeating at 27B.
