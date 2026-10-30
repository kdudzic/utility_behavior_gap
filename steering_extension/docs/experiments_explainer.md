# Every steering experiment so far, in order

Last updated 2026-10-30 (week 7, before the week-7 GPU batch). One entry per experiment: what was done, with
what values, on what, and what came out. Detailed tables live in the per-week documents linked in each entry.
Numbers are win rates of the steered (or ablated) side with wins / losses in brackets, panel ties excluded.

## 0. Fixed setup shared by everything

| element | value |
| --- | --- |
| model | Qwen3.5-9B (bf16, local HuggingFace weights; 32 decoder layers, hidden size 4096) |
| prompts | the paper's own prompt text, byte for byte: framed-neutral competition prompt; max-effort exhortation appended to it; role-cue prompts ("world-class" / "skilled") |
| tasks | essay is the evaluation task (30 items); grant and postmortem (30 items each) feed vector extraction; translation excluded since 2026-10-17 |
| sampling | temperature 1.0, thinking off, blank system prompt, max_tokens essay 900 / grant 1400 / postmortem 3000 |
| judging | the paper's three judges (claude-haiku-4.5, gemini-3.1-flash-lite-preview, gpt-5-mini), both presentation orders, a judge whose two orders disagree counts as a tie, panel majority, panel ties excluded, exact-binomial 95% CI |
| coherence | one judge (claude-haiku-4.5), 0 to 100, readable and on-topic text, independent of quality |
| vector | difference of mean hidden states, max-effort minus neutral prompt, at each layer's output (same recipe for the role vectors) |
| readout | where in the sequence the hidden state is taken: "response mean" = average over the model's own answer tokens (the "old" vector); "assistant-start" = the last prompt token; "prompt mean" = average over the prompt tokens; week 6 added single template tokens and the first generated token |
| steering | add coef x vector to one layer's output during generation; dose r = size of the added vector as a fraction of that layer's RMS hidden-state size; r > 0 adds, r < 0 removes; mode `response` (generated tokens only, default), `prompt` (prompt tokens only), `all` (both) |
| ablation | project the direction out of the layer output at every token (prompt and response), at the listed layers |
| cell | one (vector, layer, dose, mode) setting; essay cells are 30 items x 2 repeats = 60 pairs unless stated; steered essay vs an unsteered essay from the same prompt and repeat |
| controls | norm-matched random directions (rand0, rand1, ...); baseline vs baseline (two unsteered samples) |

## 1. Week 4 (2026-10-10): pilot, `mini_pilot_report.md`

| # | experiment | values | result |
| --- | --- | --- | --- |
| 1.1 | Phase 0: does our local pipeline reproduce the paper's effort effect? | max-effort vs neutral, essay, 150 pairs; role cue world-class vs skilled, 150 pairs | effort 0.70 (31/13, p = 0.01), +20 words; role 0.55 (31/25, n.s.). Paper: 0.67 and 0.57. Pipeline valid. |
| 1.2 | Phase 1: first vectors (v1) | response mean, 14 items x 3 tasks incl. translation, 42 responses per arm; E, R_id, R_act | E norm 1 to 3% of residual; the three directions near-orthogonal |
| 1.3 | Phase 2a: layer x dose sweep, 10 items | E at layers 8, 12, 16, 20, 24 x r +0.05, +0.1, +0.2 | 2 to 5 resolved pairs per cell, no signal; coherence drops only at r >= 0.1 for layers 12 and 24. Layer 16 chosen as a mid-depth prior. |
| 1.4 | Phase 2b: signed doses at layer 16, 30 items x 1 | E at r -0.2, -0.1, +0.1, +0.2 (response), +0.2 (all); rand0 at +/-0.2 | remove loses: -0.1 0.10 (1/9), -0.2 0.00 (0/27), coherence intact; add +0.1 0.73 (8/3, n.s.); +0.2 loses with coherence loss; random null |
| 1.5 | v2 vectors and reliability | 30 items x 3 tasks x 2 repeats, 180 per arm | E split-half cosine 0.65; R_act 0.22; R_id -0.05 (role vectors unreliable in this readout) |
| 1.6 | Phase 2 full: essay dose curve at layer 16, 60 pairs | E v2 at r -0.2 to +0.2 | same shape as 1.4; the "remove hurts, add helps weakly" pattern |

## 2. Week 5 (2026-10-17): new readouts and layer choice, `layer_selection.md`, `essay_redo_L18.md`, `essay_rmean_layers.md`

| # | experiment | values | result |
| --- | --- | --- | --- |
| 2.1 | v3 vectors, three readouts | grant + postmortem only, 30 items x 2 repeats, 120 per arm; readouts response mean, assistant-start, prompt mean | assistant-start and prompt-mean vectors build the same way every time (split-half 0.97 to 1.0) and separate exhortation from no-exhortation perfectly (AUC 1.0); response-mean E split-half -0.17 |
| 2.2 | prompt-mean vector on grant, judge-free | 11 layers x 2 doses, 30 items; text features | moves features opposite to the real exhortation at every layer; dropped |
| 2.3 | layer selection for the assistant-start vector | reliability profile, judge-free grant sweep (coherence, KL < 0.1, re-projection, feature match), then judges at 3 layers | features picked layer 24, judges picked layer 18 (8/1 on grant); layer 18 chosen; late layers change surface statistics, not what judges value |
| 2.4 | essay dose curve, assistant-start vector, layer 18 | r -0.2, -0.1, -0.05, +0.05, +0.1, +0.15, +0.2; also layers 16, 22; random at 18 | nothing significant at any dose (0.35 to 0.75, 63 to 80% ties); length and coherence unchanged |
| 2.5 | essay, response-mean vector rebuilt (v3), layer 16 | r -0.1, +0.05 | -0.1: 0.19 (6/26, p = 0.001); +0.05: 0.76 (16/5, p = 0.027). Pooled +0.05 over weeks 4 and 5: 27/11 |
| 2.6 | essay layer profile, response-mean vector | layers 8, 12, 16, 20, 24 x r -0.1, +0.05; rand0 at 16 | remove hurts at 8 to 16 (0.12, 0.09, 0.06), fades at 20 to 24; add n.s. everywhere; random null |

Lesson of week 5: a vector that builds reliably (assistant-start) does not steer; the noisy response-mean vector
does. The response-mean E is the working vector from here on.

## 3. Week 6 (2026-10-27): full sweep of the working vector, `week6_results.md`

v4 vectors: same recipe as v3 with 30 items x 2 tasks x 5 repeats = 300 responses per arm. v3 and v4 behave the same
(bridge run: -0.1 0.10 vs 0.12; +0.05 0.62 vs 0.60).

| # | experiment | values | result |
| --- | --- | --- | --- |
| 3.1 | full dose-response sweep | layers 6, 8, ..., 28 x r -0.2, -0.1, -0.05, +0.025, +0.05, +0.075, +0.1; rand0, rand1 at layer 16 at -0.1 and +0.05; 5,340 pairs | remove at -0.1 loses at every layer 6 to 20 (0.06 to 0.22, p < 0.003); -0.2 near 0/60 at 6 to 20; add helps early: layer 6 monotonic to 0.88 (22/3) at +0.1, layer 10 0.82 (18/4), layer 14 0.81 (17/4) at +0.05; from layer 16 on add is flat or turns down (layer 16 +0.1: 0.23); random at 16 null |
| 3.2 | multi-layer injection | dose split evenly over layers 12+16+20, 14+16+18, 8 to 24; r -0.1, +0.05 | same as single layer 16 (0.14 / 0.19 remove; 0.50 to 0.65 add) |
| 3.3 | injection position, layer 16 | prompt tokens only; prompt + generated; r -0.1, +0.05 | prompt-only remove 0.29 (8/20, p = 0.04); both 0.02 (1/47); add 0.54 to 0.57 |
| 3.4 | other pre-response readouts, layer 16 | assistant-start, `</think>`, newline after it, `<think>`, newline before it, `assistant`, first generated token; r +/-0.1 | all at 0.26 to 0.65, none significant |
| 3.5 | ablation under the max-effort prompt | E at all 32 layers; rand0 at all 32; E at layers 8 to 16; vs untouched max-effort and vs neutral | all-layer E ablation breaks the model (0/60, coherence 2); random ablation harmless (0.57); layers 8 to 16: 0.15 (3/17, p = 0.003), coherence 82 vs 88; untouched max-effort vs neutral 0.67 (14/7) |

## 4. Week 7 offline (2026-10-30): reading the texts, `week7_offline.md`

| # | analysis | result |
| --- | --- | --- |
| 4.1 | qualitative reading of ablation (layers 8 to 16) and striking steering cells | ablation under exhortation: overwrought metaphors, invented statistics, 13% essays with a broken token; removal under neutral prompt: bland textbook essays with intact fluency; early-layer addition: more specifics, longer, shorter sentences |
| 4.2 | coherence across all forms | holds for removal at -0.05/-0.1 (89, slightly above baseline), addition at <= +0.05, random, multi-layer, positions, readouts; drops for addition at >= +0.075 from layer 16 on (81 to 84), removal at -0.2 (83 to 86), local ablation (82), all-layer ablation (2) |
| 4.3 | paper text features | our exhortation prompt reproduces the paper's feature signature (r = 0.96); early-layer addition reproduces most of it (r = 0.4 to 0.5: longer, more sentences, more rare words and semicolons, fewer positive words) but with shorter, simpler sentences; removal flattens vocabulary rather than mirroring the exhortation (r about 0); local ablation keeps the "more" and breaks the sentences |

## 5. Week 7 GPU batch (planned, `week7_plan.txt`)

| # | experiment | values | question |
| --- | --- | --- | --- |
| 5.1 | random controls on the sweep grid | rand0, rand1 at layers 6, 10, 14, 20 x r -0.1, +0.05, +0.1; 1,440 pairs | are the early-layer results direction-specific? |
| 5.2 | cross-validation | vector built from 300 essay responses per arm, tested on grant at layers 6, 10, 16 x r -0.1, +0.05, +0.1, rand0 at 10; 720 pairs | does the direction transfer across tasks? |
| 5.3 | role cues | world-class and skilled prompts; E ablated at layers 8 to 16, E added at layer 6 +0.1, each vs the untouched role essay; world-class vs skilled bridge; 300 pairs | does the direction act under a role cue instead of the exhortation? |
| 5.4 | clean necessity test | max-effort prompt, E or rand0 ablated at layers 8 to 16, vs the neutral-prompt essay; 120 pairs | once the direction is gone, does the exhortation still help? |

## 6. Standing answers to the hypotheses

- H2, removing the direction cancels the effect: supported at 10 of 12 layers with a full dose curve; under the
  exhortation prompt the local ablation loses 3/17 but with a coherence cost, and the clean version (vs neutral)
  is item 5.4.
- H1, adding the direction reproduces the effect: supported at layers 6 to 14 (best 22/3 at layer 6, +0.1), with
  most of the exhortation's text signature; fails from layer 16 on; random controls at those layers are item 5.1.
- H3, random directions do nothing: supported at layer 16 (6 cells); other layers are item 5.1.
- Not yet shown: transfer to another task (5.2), effect under a role cue (5.3), a length control, anything on
  the 27B model.
