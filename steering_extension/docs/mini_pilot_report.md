# Mini-pilot report (Qwen3.5-9B, essay, effort vector E)

Date: 2026-10-10. Status: DRAFT, filled in as cells complete. Compute: Athena A100 40 GB nodes, 4 GPUs per step.
Judging: paper panel (claude-haiku-4.5, gemini-3.1-flash-lite-preview, gpt-5-mini), both orders, flips -> tie, panel ties excluded.
All prompts byte-identical to the paper's canonical prompt book (framed-neutral competition wrapper, children's hospital target).

## Phase 0 mini: local replication of the paper's essay effort cell

| cell | pairs | W | L | ties | win rate (ties excl.) | 95% CI | p (two-sided) | mean words strong / neutral |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| local HF Qwen3.5-9B, max-effort vs framed neutral | 60 | 11 | 8 | 41 | 0.579 | [0.33, 0.80] | 0.65 | 412 / 396 |
| paper (OpenRouter), same cell | 150 | 37 | 18 | 95 | 0.673 | FWER [0.48, 0.83] | 0.007 (one-sided) | +17.3 word diff |

Reading: point estimate inside the paper's CI; tie rate (68% vs 63%) and length shift (+16 vs +17 words) match.
Underpowered at 60 pairs by design; the full pilot runs 150 pairs each for effort and role.

## Phase 1 mini: vectors

Contrast prompts: 14 items x 3 non-essay tasks (grant, postmortem, translation), one sampled response per prompt, 300-token cap,
response-token-mean readout. 42 responses per arm per contrast. Held out from the essay evaluation items by construction.

- Relative norm |v| / RMS(residual): E 0.004 (layer 0) rising to 0.015 (layer 12), 0.019 (layer 16), 0.029 (layer 20), 0.03 (layer 24+).
- R_id and R_act about 0.6-0.7x the norm of E at every layer.
- Cosines (layers 12-24): E|R_id 0.08-0.15, E|R_act 0.09-0.14, R_act|R_id 0.02-0.12. The three directions are nearly orthogonal.
- Random matched-norm directions rand0..rand4 stored per layer.

## Phase 2a mini: layer x dose sweep (10 items, 1 repeat)

Cells: E at layers {8, 12, 16, 20, 24} x r {0.05, 0.1, 0.2} (fraction of layer RMS residual norm, response positions only),
plus rand0 at layer 16 r {0.1, 0.2}, plus a baseline-vs-baseline null cell. Steered side vs shared unsteered baseline sample.

| cell | resolved n | W | L | ties | win rate | mean words a / b | coherence a |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_rep | 3 | 2 | 1 | 7 | 0.67 | 404 / 399 | 88.6 |
| steer_E_L12_r+0.050_response | 5 | 4 | 1 | 5 | 0.80 | 391 / 399 | 87.2 |
| steer_E_L12_r+0.100_response | 3 | 2 | 1 | 7 | 0.67 | 380 / 399 | 82.6 |
| steer_E_L12_r+0.200_response | 2 | 0 | 2 | 8 | 0.00 | 406 / 399 | 80.4 |
| steer_E_L16_r+0.050_response | 4 | 4 | 0 | 6 | 1.00 | 384 / 399 | 89.6 |
| steer_E_L16_r+0.100_response | 3 | 2 | 1 | 7 | 0.67 | 377 / 399 | 87.2 |
| steer_E_L16_r+0.200_response | 3 | 2 | 1 | 7 | 0.67 | 362 / 399 | 82.8 |
| steer_E_L20_r+0.050_response | 3 | 0 | 3 | 7 | 0.00 | 388 / 399 | 85.3 |
| steer_E_L20_r+0.100_response | 2 | 1 | 1 | 8 | 0.50 | 404 / 399 | 80.6 |
| steer_E_L20_r+0.200_response | 4 | 1 | 3 | 6 | 0.25 | 379 / 399 | 81.6 |
| steer_E_L24_r+0.050_response | 4 | 4 | 0 | 6 | 1.00 | 412 / 399 | 90.6 |
| steer_E_L24_r+0.100_response | 4 | 2 | 2 | 6 | 0.50 | 403 / 399 | 76.5 |
| steer_E_L24_r+0.200_response | 2 | 1 | 1 | 8 | 0.50 | 385 / 399 | 83.2 |
| steer_E_L8_r+0.050_response | 0 | 0 | 0 | 10 | - | 403 / 399 | 85.0 |
| steer_E_L8_r+0.100_response | 3 | 3 | 0 | 7 | 1.00 | 385 / 399 | 86.6 |
| steer_E_L8_r+0.200_response | 2 | 2 | 0 | 8 | 1.00 | 405 / 399 | 87.9 |
| steer_rand0_L16_r+0.100_response | 4 | 4 | 0 | 6 | 1.00 | 392 / 399 | 89.2 |
| steer_rand0_L16_r+0.200_response | 4 | 3 | 1 | 6 | 0.75 | 389 / 399 | 91.0 |

Reading: with 10 items per cell and the paper's tie convention (60-100% panel ties here), resolved n is 2-5 per cell:
no layer or dose can be selected on efficacy from this sweep. Coherence (0-100, single judge; unsteered baseline scores 85-89)
stays within ~5 points of baseline up to r=0.2 at layers 8-16 and drops to 76-80 at r>=0.1 for layers 12/24. Length falls
with +E at layer 16 (362 vs 399 words at r=0.2) while the paper's exhortation lengthens essays (+17 words): the natural
exhortation effect and the steered one are not obviously the same thing. The random direction also "wins" 4/0 at r=0.1,
so single-digit resolved counts carry no signal. Choice for Phase 2b mini: layer 16 (mid-depth prior, coherent to r=0.2),
r_max = 0.2, signed doses.

## Phase 0 full: 150 effort pairs + 150 role pairs (local HF, same prompts as the paper)

| cell | resolved n | W | L | ties | win rate | 95% CI | p | words a / b | coherence a (pass>=80) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| framed_user_max_effort | 44 | 31 | 13 | 106 | 0.70 | [0.55, 0.83] | 0.010 | 412 / 392 | - |
| framed_user_prompt_role | 56 | 31 | 25 | 94 | 0.55 | [0.41, 0.69] | 0.504 | 400 / 395 | - |

Paper cells (OpenRouter, Qwen3.5-9B): effort 0.673 (37/18, 95 ties, 150 pairs); role 0.571 (56/42, 202 ties, 300 pairs).
Both local cells reproduce the paper's point estimates, tie rates, and the +17-word effort length shift (+20 here).
The local HF stack is a valid stand-in for the paper's OpenRouter actor.

## Phase 2b mini: signed dose cells, layer 16, 30 items, 1 repeat

| cell | resolved n | W | L | ties | win rate | 95% CI | p | words a / b | coherence a (pass>=80) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_rep | 11 | 6 | 5 | 19 | 0.55 | [0.23, 0.83] | 1.000 | 391 / 389 | 88 (0.83) |
| steer_E_L16_r+0.100_response | 11 | 8 | 3 | 19 | 0.73 | [0.39, 0.94] | 0.227 | 382 / 389 | 86 (0.70) |
| steer_E_L16_r+0.200_all | 21 | 1 | 20 | 9 | 0.05 | [0.00, 0.24] | 0.000 | 366 / 389 | 76 (0.37) |
| steer_E_L16_r+0.200_response | 15 | 4 | 11 | 15 | 0.27 | [0.08, 0.55] | 0.118 | 370 / 389 | 81 (0.53) |
| steer_E_L16_r-0.100_response | 10 | 1 | 9 | 20 | 0.10 | [0.00, 0.45] | 0.021 | 405 / 389 | 89 (0.87) |
| steer_E_L16_r-0.200_response | 27 | 0 | 27 | 3 | 0.00 | [0.00, 0.13] | 0.000 | 416 / 389 | 83 (0.70) |
| steer_rand0_L16_r+0.200_response | 4 | 3 | 1 | 26 | 0.75 | [0.19, 0.99] | 0.625 | 388 / 389 | 87 (0.83) |
| steer_rand0_L16_r-0.200_response | 6 | 2 | 4 | 24 | 0.33 | [0.04, 0.78] | 0.688 | 387 / 389 | 91 (0.93) |

Side `a` is steered (or the second baseline sample in `baseline_rep`); side `b` is the shared unsteered baseline sample.
`r` is the dose as a fraction of the layer-16 RMS residual norm (36.5); the natural exhortation shift at this layer is r = 0.019.

Reading:
- **Signed, direction-specific effect on the negative side.** Subtracting E (r = -0.1, -0.2) makes essays lose decisively
  (1/9 and 0/27 resolved; tie rate collapses from 63% to 10% at -0.2), with coherence intact (median 92, pass rate 0.70-0.87)
  and essays *longer* (405-416 vs 389 words). The norm-matched random direction at the same dose is a null (2/4, 3/1, 80-87% ties).
  This is the specificity pattern the proposal asked for: not a generic perturbation.
- **Positive side is weak and narrow.** +0.1 wins 8/3 (0.73, CI [0.39, 0.94], n.s. at 30 items) with coherence pass rate 0.70;
  +0.2 already loses (4/11) with coherence pass rate 0.53, and +0.2 at all positions is a clear degradation (1/20, median coherence 78).
  r_max for positive steering is therefore about 0.1 at layer 16, 5x the natural shift; the proposal's grid should run {-0.2, -0.1, -0.05, +0.05, +0.1, +0.15}.
- **What E looks like in text.** Reading samples: -0.2 essays are fluent but plain and formulaic; +0.1 essays add rhetorical intensity
  ("moral imperative", "smog chokes our skies"); +0.2 turns purple ("the theft of breath", "the physics of escape").
  E behaves like a rhetorical-elaboration axis that judges reward in moderation. Whether this matches the paper's Table 2 effort
  feature signature is the first analysis for the full pilot (repo feature pipeline on these texts).
- **Length.** The natural exhortation lengthens essays (+17-20 words); +E shortens them slightly (-7 to -19 words) and -E lengthens them.
  Steering does not reproduce the length channel of the prompt effect, so any steered win is not a length artefact.

## Vector reliability (v2: 30 items x 3 tasks x 2 repeats, 180 responses per arm)

| vector | relative norm L12 / L16 / L20 | cos(v1, v2) L16 | split-half cos L16 (90 vs 90 per arm) |
| --- | --- | --- | --- |
| E | 0.011 / 0.014 / 0.022 | 0.62 | 0.65 (Spearman-Brown reliability of the full vector ~0.79) |
| R_act | 0.007 / 0.009 / 0.013 | -0.04 | 0.22 |
| R_id | 0.005 / 0.006 / 0.009 | 0.09 | -0.05 |

Reading: with the response-token-mean diff-of-means recipe, **E is a real but noisy direction** (its sampling noise explains part of the
weak positive side), **R_act is barely above noise**, and **R_id has no reproducible direction at all** at 180 responses per arm:
the "world-class vs skilled" cue leaves no consistent trace in the mean response residual. This is itself consistent with the paper's
small, mostly non-significant role effects, but it means the proposal's R_id steering arm cannot proceed on this recipe.
Options for the Phase 3 review: (a) prompt-token readout (deterministic, no sampling noise, averaged over many prompts),
(b) many more responses (noise falls as 1/sqrt(n); ~0.95 reliability for E needs ~4x), (c) PC-denoising against a neutral corpus,
(d) a two-sided role contrast (world-class vs explicitly novice) as a stronger, differently-defined construct.
The dose cells above used v1 (42 per arm); the full pilot uses v2.

## Spend

OpenRouter usage today (all judging + coherence, from the key's usage counter): about $12 of the $40 authorization.

## Open issues

- GatedDeltaNet runs on reference torch kernels (causal_conv1d missing on the offline compute nodes); ~400-550 tok/s per GPU at batch 30-48. Hub-kernel path needs an explicit revision pin to work offline; deferred.
- GitHub push from Athena needs credentials (none configured); commits are local until then.
