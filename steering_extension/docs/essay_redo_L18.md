# Essay dose curve redo with the selected vector (E_astart, layer 18)

Date: 2026-10-17. Design identical to the pilot's full essay curve (`mini_pilot_report.md`, "Full pilot"):
30 essay items x 2 repeats = 60 pairs per cell, steered side vs a shared unsteered baseline sample, paper's
canonical framed-neutral prompt, paper judge panel, both orders, flips -> tie, panel ties excluded, exact CIs.
Only the vector differs: E_astart (assistant-start-token readout, v3 extraction, grant + postmortem) at layer 18,
chosen in `layer_selection.md`. Robustness arms at layers 16 and 22; the pilot's response-mean E (v3, layer 16)
as comparison; two random matched-norm directions at layer 18. Table: `results/2026-10-17_essay_redo_L18/dose_summary.csv`.
Cost: 20 GPU-minutes (about $0.15) and about $12 of judging + coherence.

| cell | resolved | W / L | win rate | 95% CI | p | all-vote rate | words a / b | coherence a (pass >= 80) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E_astart L18 r = -0.20 | 20 | 7 / 13 | 0.35 | [0.15, 0.59] | 0.26 | 0.49 | 411 / 390 | 88 (0.88) |
| E_astart L18 r = -0.10 | 18 | 10 / 8 | 0.56 | [0.31, 0.79] | 0.82 | 0.56 | 402 / 390 | 89 (0.87) |
| E_astart L18 r = -0.05 | 18 | 12 / 6 | 0.67 | [0.41, 0.87] | 0.24 | 0.59 | 395 / 390 | 90 (0.93) |
| E_astart L18 r = +0.05 | 20 | 11 / 9 | 0.55 | [0.32, 0.77] | 0.82 | 0.53 | 392 / 390 | 88 (0.78) |
| E_astart L18 r = +0.10 | 12 | 9 / 3 | 0.75 | [0.43, 0.95] | 0.15 | 0.52 | 390 / 390 | 87 (0.78) |
| E_astart L18 r = +0.15 | 21 | 11 / 10 | 0.52 | [0.30, 0.74] | 1.00 | 0.51 | 386 / 390 | 87 (0.82) |
| E_astart L18 r = +0.20 | 22 | 10 / 12 | 0.45 | [0.24, 0.68] | 0.83 | 0.49 | 382 / 390 | 85 (0.72) |
| E_astart L16 r = -0.10 / +0.10 | 15 / 21 | 10 / 5, 9 / 12 | 0.67 / 0.43 | | 0.30 / 0.66 | 0.53 / 0.47 | 414, 378 / 390 | 90, 86 |
| E_astart L22 r = -0.10 / +0.10 | 20 / 21 | 14 / 6, 13 / 8 | 0.70 / 0.62 | | 0.12 / 0.38 | 0.58 / 0.52 | 398, 391 / 390 | 89, 86 |
| **rmean E L16 r = -0.10** (pilot vector, v3) | 32 | 6 / 26 | **0.19** | [0.07, 0.36] | **0.001** | 0.34 | 397 / 390 | 89 (0.88) |
| **rmean E L16 r = +0.05** | 21 | 16 / 5 | **0.76** | [0.53, 0.92] | **0.027** | 0.57 | 392 / 390 | 87 (0.82) |
| random L18 r = -0.20 (two directions) | 20 / 27 | 13 / 7, 13 / 14 | 0.65 / 0.48 | | | 0.55 / 0.49 | 400, 390 / 390 | 89, 88 |
| random L18 r = +0.10 (two directions) | 20 / 17 | 9 / 11, 10 / 7 | 0.45 / 0.59 | | | 0.47 / 0.52 | 392, 400 / 390 | 86, 88 |
| baseline vs baseline | 13 | 8 / 5 | 0.62 | [0.32, 0.86] | 0.58 | 0.54 | 396 / 390 | 89 (0.87) |

Logistic slope on signed dose for E_astart L18 (resolved pairs, item-clustered SE): all doses 0.76 (p = 0.36);
negative side 8.7 (p = 0.015); positive side -3.7 (p = 0.39). Fisher E vs pooled random at +0.1: 9/3 vs 19/18, p = 0.19.

## Reading

1. **The selected vector does little on essays.** E_astart at layer 18 produces no significant cell at any
   dose; the tie rate is 63-80 percent (the judges see near-identical essays), length and coherence barely move.
   The layer-18 pick came from a single judged grant cell (8/1 of 30), and it does not carry to the essay task.
   The same holds at layers 16 and 22. Random directions are null too, so this is not a perturbation story:
   the direction is simply weak at the response positions.
2. **The pilot's response-mean E replicates with the new, "unreliable" v3 extraction.** +0.05 wins 16/5
   (0.76, p = 0.027), -0.1 loses 6/26 (0.19, p = 0.001), with coherence intact and length unchanged. This is the
   pilot's signed curve again (pilot: +0.05 0.65 n.s., -0.1 0.21). Two independent extractions (pilot v2 with
   translation, 180 per arm; v3 without translation, 120 per arm) give the same behavioural effect, so the
   response-mean direction has a reproducible causal component even though its split-half cosine is negative:
   split-half measures the whole 4096-d vector, most of which is noise, while steering responds to the part that
   is shared. The reliability screen in L1 was the wrong filter for causal relevance.
3. **Readout matters more than layer.** The prompt-side direction (what the model represents after reading an
   exhortation) is reliable but behaviourally weak at response positions; the response-side direction (how
   exhorted responses differ) is noisy but behaviourally potent. For the mediator question this is informative:
   the exhortation's effect on output is carried by a response-state direction, not by a copy of the
   instruction representation. Steering the instruction representation into the response stream does not
   reproduce the instruction's effect.
4. **Positive side now significant for rmean E.** The pilot's +0.05 cell was 11/6 (0.65, n.s.); here 16/5
   (0.76, p = 0.027). Pooled across the two independent runs: 27/11 (0.71, exact p = 0.014). Sufficiency has
   weak but real support at r = 0.05 for the response-mean direction at layer 16, about 3-4x the natural shift.

## Consequences for the plan

- Drop E_astart as a steering vector; keep it as a monitoring probe (it is excellent at detecting whether an
  exhortation was present, AUC 1.0, which is what Phase 3 projection monitoring needs).
- The steering direction is the response-mean E. Its layer question is still open: the pilot's L12/L16/L20
  check showed the negative side at all three; the positive side has only been seen at L16. A layer sweep for
  rmean E should use the judge directly on essay at r = +0.05 (the only dose that works), 60 pairs per layer,
  5 layers: about $10 of judging. The feature-signature proxy is retired (it failed on postmortem and
  disagreed with judges on grant).
- Extraction for rmean E should scale n (the pilot's 180 and v3's 120 both work; 300+ per arm, grant +
  postmortem + essay-held-out items from the paper's other prompts, would raise the reliable fraction) and
  can use PC-denoising against the neutral arm.
- Role vectors: R_id/R_act are reliable only in the prompt-side readout, which this run shows to be weak for
  steering. A response-mean role vector needs the larger extraction before any dose cells.
