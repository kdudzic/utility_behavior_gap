# Does an effort-exhortation prompt act through a steerable direction? A mechanistic follow-up to the utility-behavior gap

### Kacper Dudzic

k.e.dudzic@gmail.com

## Abstract

Zhou and Ackerman showed that a "give your best effort" exhortation raises the judged quality of LLM writing while the model's own stated utilities do not. We ask whether that prompt effect is carried by one direction in Qwen3.5-9B's residual stream. We extract the direction as the mean activation difference between exhorted and neutral responses, then add it, remove it, or ablate it while the model writes, and judge the output with the paper's blind three-judge panel. Adding the direction at early layers reproduces the exhortation's effect (up to 22 wins to 3 losses against unsteered essays), removing it cancels the effect, both beat matched random directions, and the direction transfers from essays to grant abstracts. The exhortation effect is mediated by a single steerable direction.

## Introduction

- The parent paper finds a utility-behavior gap: prompts that cue effort move output quality, elicited utilities do not. It is purely behavioral; nothing is known about what the exhortation changes inside the model.
- If the effect runs through one direction in activation space, effort becomes measurable and controllable without prompt text, which matters for monitoring whether a model is trying and for understanding why stated preferences fail to become incentives.
- Hypotheses, treating the direction as a candidate mediator: H1 sufficiency (adding it reproduces the effect, growing with dose), H2 necessity (removing it cancels the effect), H3 specificity (random directions of the same size do not).
- Contributions so far: a full layer-by-dose map of the direction's effect on essays; its text signature compared with the real prompt's; random-direction controls at every layer that matters; transfer to a second task; a necessity test under the real exhortation; and the finding that random perturbations are not neutral, which changes the null for all such tests.

## Methods

- Model: Qwen3.5-9B (32 layers), run locally; the paper's prompts byte for byte; temperature 1.0, thinking off.
- Direction: mean hidden state over the model's own answer tokens under the max-effort prompt minus under the neutral prompt, per layer, from 300 responses per side on grant and postmortem prompts (essays held out for evaluation). A second direction built from essay responses only is used for the transfer test.
- Interventions: add or subtract the direction at one layer's output while the model writes, dose given as a fraction of that layer's residual norm (r from -0.2 to +0.1); directional ablation (project the direction out at every token) at layers 8 to 16.
- Evaluation: the paper's design, unchanged. Each intervened essay is judged against an unsteered essay from the same prompt by claude-haiku-4.5, gemini-3.1-flash-lite-preview and gpt-5-mini in both orders; a judge whose orders disagree counts as a tie, panel ties are dropped, exact-binomial CIs. 60 pairs per cell. A separate judge scores coherence 0 to 100. The paper's 14 text features are computed with its own code.
- Controls: two norm-matched random directions at the same layers and doses; unsteered-vs-unsteered null cells; random-direction ablation.
- Scale to date: about 12,500 judged pairs, 75,000 judge votes, on rented A100 time.

## Results

- Sufficiency. Adding the direction at layers 6 to 14 wins against unsteered essays: layer 6 at r = +0.1, 22 / 3 (0.88); layer 10, 18 / 4; layer 14 at +0.05, 17 / 4. From layer 16 on, adding at high dose loses and costs coherence. Matched random directions at the winning cells sit at 0.26 to 0.39 (Fisher p from 0.03 to 0.0001).
- Necessity. Removing the direction at r = -0.1 loses at every layer from 6 to 20 (win rates 0.06 to 0.22) with coherence intact. Against random controls the loss is direction-specific at layers 10 to 16, not at 6 and 20. Under the real exhortation prompt, ablating the direction at layers 8 to 16 drops the essay below the neutral-prompt essay (7 / 19); ablating a random direction leaves the exhortation's advantage (12 / 8; untouched 14 / 7).
- Specificity, revised. Random directions are not neutral: pooled over 24 cells they lose 148 / 265 (0.36) with unchanged coherence and length. The null for a steering cell is about 0.35, not 0.5; all claims above hold against that null.
- Transfer. The direction built from essays steers grant abstracts: removal 1 / 40, 2 / 46, 0 / 49 at layers 6, 10, 16; addition at +0.05, 0.67 to 0.76.
- What the texts look like. Removal by steering yields bland, textbook essays with fluency intact (rare-word rate -1.2 SD, positive-sentiment words +0.5). Addition at early layers moves the paper's text features the way the real exhortation does (correlation 0.5 with the paper's feature deltas; our own prompt replication reaches 0.96), with shorter, denser sentences the prompt does not produce. Ablation under the exhortation gives overblown text with invented statistics and 13% broken tokens.
- Negative results. Directions read at single prompt tokens (assistant-start, template tokens, first generated token) build reliably (split-half 0.9 to 1.0) but do not steer. Spreading the dose over several layers adds nothing. Adding the direction under the paper's "world-class" role prompt does nothing (11 / 13), while under the "skilled" prompt it wins 17 / 5. Ablation costs 5 to 9 coherence points, so part of the necessity result can be writing damage.
