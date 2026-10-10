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

## Phase 2b mini: signed dose cells (30 items)

(pending sweep choice of layer and r_max)

## Open issues

- GatedDeltaNet runs on reference torch kernels (causal_conv1d missing on the offline compute nodes); ~400-550 tok/s per GPU at batch 30-48. Hub-kernel path needs an explicit revision pin to work offline; deferred.
- GitHub push from Athena needs credentials (none configured); commits are local until then.
