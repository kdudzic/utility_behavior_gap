---
title: "SPAR Week 5 Progress Report"
subtitle: "Effort direction in Qwen3.5-9B: new readouts, layer choice, essay rerun"
author: "Kacper"
date: "2026-10-17"
---

## Personal updates

-

## This week in one line

**New vector is weak everywhere. Old vector is strong somewhere.**

- Old vector (response-token average), layer 16, essays: remove it, essays lose **2 / 32**; add a little, essays win **28 / 14** pooled (p = 0.04)
- New vector (assistant-start token), best layer 18, essays: **nothing significant at any of 7 doses**; 63-80% ties
- Random directions: nothing, everywhere
- Layer 16 was a guess last week. Now tested: it sits inside a plateau (layers 8-16 all work for removal). Not special, not wrong

## What changed since last week

- Translation dropped from everything (vectors now from grant + postmortem only, essays held out for testing)
- Two new ways to read out the vector tried, as suggested: assistant-start token, average over user-prompt tokens
- Layer chosen by a written procedure instead of a prior
- Infrastructure moved to vast.ai (Athena login closed). One command rents, runs, pulls, destroys

## Three readouts, one contrast

Same prompts (max-effort vs neutral), same model, same 120 responses per side. Only *where* we read the hidden state differs.

| readout | taken from | built twice, same direction? (split-half cos, L16) |
|---|---|---|
| response average (old) | mean over the model's own answer tokens | **-0.17** (noise dominates) |
| assistant-start token (new) | last prompt token, right before the model starts writing | **0.97** |
| user-prompt average (new) | mean over the user's prompt tokens | **0.99** |

- The two new readouts look perfect on paper. Partly by construction: the two prompts differ in text, so "was there an exhortation" is easy to read off the prompt
- Cosine between old and assistant-start direction: 0.15-0.29. They are different directions

## User-prompt average: dropped early

- Steered grant abstracts at 11 layers, 2 doses, 30 items each
- Moved the text the **wrong way** at every layer: fewer rare words, more positive words, the opposite of what the real exhortation does (feature-signature correlation -0.1 to -0.6)
- Reason: this direction is mostly the words of the exhortation sentence itself, not a state of the model
- Not carried to the essay test

## Assistant-start token vector: where it comes from

- Chat template ends with `<|im_start|>assistant` and a newline. The vector is read at that last token
- It is the model's state after reading the whole prompt and just before writing word one
- Deterministic given the prompt: no sampling noise, hence the 0.97 reliability
- Natural size of the exhortation shift at layer 16: **0.12** of the residual norm (old readout: 0.014). Nine times larger, so doses went up to 0.2

## Layer procedure (pre-registered, written before running)

1. **Reliability profile** per layer, free from extraction data: which layers have a stable direction
2. **Judge-free sweep** on grant (not essays, to keep essays clean): 11 layers x 6 doses x 30 items. Hurdles: fluency intact, KL to the unsteered model < 0.1, steered text re-read still points along the direction. Rank passing layers by how well the feature changes match the paper's exhortation effect
3. **Judge check**: top 3 layers + layer 16, paper's 3-judge panel, 30 grant pairs each
4. **Essay dose curve** at the winner, same design as last week

## Layer procedure: what happened

- Step 1: layers 14-24 pass for the new vector; 8-12 fail the "text still points along the direction" hurdle
- Step 2: feature match picked **layer 24** (0.86), layer 22 close (0.88), layer 18 third (0.79)
- Step 3: judges disagreed. **Layer 18** won 8 / 1 on grant; layers 22 and 24 were null or lost. Rule said: judges override. Layer 18 chosen
- Replication of step 2 on postmortems: no signal at all. Feature-matching shortcut retired
- Lesson: late layers change surface statistics without changing what judges value

## Essay rerun: new vector at layer 18

Same design as last week: 30 items x 2 repeats, steered vs unsteered, paper judges.

| dose | W / L | win rate | ties |
|---|---|---|---|
| -0.20 | 7 / 13 | 0.35 (n.s.) | 40 |
| -0.10 | 10 / 8 | 0.56 | 42 |
| -0.05 | 12 / 6 | 0.67 | 42 |
| +0.05 | 11 / 9 | 0.55 | 40 |
| +0.10 | 9 / 3 | 0.75 (n.s.) | 48 |
| +0.15 | 11 / 10 | 0.52 | 39 |
| +0.20 | 10 / 12 | 0.45 | 38 |

- Nothing significant. Judges saw near-identical essays. Same at layers 16 and 22
- Length unchanged, fluency unchanged

## Essay rerun: old vector, rebuilt from scratch

Old recipe, but new data (no translation, 120 responses per side instead of 180). Layer 16.

| dose | W / L | win rate | p |
|---|---|---|---|
| -0.10 | 6 / 26 | 0.19 | 0.001 |
| +0.05 | 16 / 5 | 0.76 | 0.027 |

- Last week's curve again, from an independent build
- Pooled over the two runs, +0.05 is 27 / 11 (p = 0.014): first real sign that adding the direction helps

## Old vector: layer profile (the question from last week)

Old vector, essays, 60 pairs per cell, 5 layers.

| layer | remove (-0.10) | add (+0.05) |
|---|---|---|
| 8 | **0.12** (3 / 22) | 0.77 (10 / 3, n.s.) |
| 12 | **0.09** (3 / 32) | 0.33 (n.s.) |
| 16 | **0.06** (2 / 32) | 0.57 (n.s.) |
| 20 | 0.32 (n.s.) | 0.42 (n.s.) |
| 24 | 0.28 (n.s.) | 0.45 (n.s.) |
| random @16 | 0.48 | 0.35 |

- Removal hurts across layers 8-16, fades after 20. Layer 16 is inside the plateau
- Adding helps only weakly; layer 16 +0.05 pooled over all three runs (last week + two today): 39 / 20 (0.66). Real, not stable run to run
- Fluency 85-90 in every cell, length within 17 words

## Old vs new vector, side by side

| | old: response average | new: assistant-start |
|---|---|---|
| builds the same twice? | no (split-half -0.17) | yes (0.97) |
| detects "exhortation was present"? | poorly (AUC 0.5-0.65) | perfectly (AUC 1.0) |
| removing it hurts essays? | **yes, strongly** (0.06-0.12) | no |
| adding it helps essays? | weakly (0.67-0.76 at +0.05) | no |
| random direction does the same? | no | no |

- Reliability of the whole vector was the wrong filter. The old vector is mostly noise, but its shared part drives behaviour
- The state after *reading* the instruction is not the state that *does* the work. The effect lives in the response

## What it means

- **H2 (removal cancels the effect): supported again**, now at three layers and from two independent builds
- **H1 (adding reproduces the effect): weak.** One dose, one layer, significant only when pooled
- **H3 (random does nothing): supported**
- The exhortation's influence is carried by a response-state direction, not by a copy of the instruction
- Length: steering never reproduces the +17-word effect of the real prompt, at any layer or readout

## Next

- Rebuild the old vector with more data (300+ per side) and noise cleaning; the response readout is the right one, it just needs n
- Role vectors: only reliable in the prompt readout, which we now know is weak for steering. Need the response readout at larger n before any test
- Ablation arm (project the direction out under the real max-effort prompt): still not run, still cheap
- Spend this week: about $3 GPU, about $25 judging. Vast credit low; GLM-5.1 on hold pending Chris
