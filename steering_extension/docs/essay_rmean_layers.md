# Essay layer sweep for the response-mean effort vector (layers 8-24, doses +0.05 / -0.1)

Date: 2026-10-17. Layer profile of the response-mean effort vector (key `E` from
`outputs/steering/vectors/qwen3.5-9b_v3/vectors.safetensors`; the v3 extraction uses grant + postmortem only
and excludes translation) on the essay task, judged directly by the paper's three-judge panel. Design as in
`essay_redo_L18.md`: 30 essay items x 2 repeats = 60 pairs per cell, steered side vs a shared unsteered baseline
sample, paper's canonical framed-neutral essay prompt, temperature 1.0, max_tokens 900, blank system prompt,
response-position steering, Qwen3.5-9B bf16. Cells: layers 8, 12, 16, 20, 24 at r = +0.05 and r = -0.1 (dose as a
fraction of the layer's RMS residual norm); random matched-norm control `rand0` at layer 16 at the same two doses;
a baseline-vs-baseline cell. Judging: both presentation orders, flips -> tie, panel ties excluded, exact-binomial
CIs and two-sided exact-binomial p against 0.5; "all-vote rate" is the share of every judge x order vote that
favoured the steered side (no tie rule). Coherence from the one-judge coherence scorer (mean of the steered side,
fraction >= 80). 780 pairs, 1560 generations, 4680 judge votes, 840 coherence scores. Table:
`results/2026-10-17_essay_rmean_layers/dose_summary.csv`. Cost: about 35 minutes of an A100 PCIe (about $0.40)
plus about $8 of judging + coherence.

| cell | resolved | W / L | win rate | 95% CI | p | all-vote rate | words a / b | coherence a (pass >= 80) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E L8 r = -0.10 | 25 | 3 / 22 | 0.12 | [0.03, 0.31] | 0.00016 | 0.35 | 388 / 395 | 89.4 (0.92) |
| E L8 r = +0.05 | 13 | 10 / 3 | 0.77 | [0.46, 0.95] | 0.092 | 0.52 | 405 / 395 | 88.3 (0.85) |
| E L12 r = -0.10 | 35 | 3 / 32 | 0.09 | [0.02, 0.23] | 4.2e-07 | 0.27 | 386 / 395 | 88.4 (0.85) |
| E L12 r = +0.05 | 24 | 8 / 16 | 0.33 | [0.16, 0.55] | 0.15 | 0.43 | 400 / 395 | 84.8 (0.67) |
| E L16 r = -0.10 | 34 | 2 / 32 | 0.06 | [0.01, 0.20] | 6.9e-08 | 0.26 | 390 / 395 | 86.5 (0.83) |
| E L16 r = +0.05 | 21 | 12 / 9 | 0.57 | [0.34, 0.78] | 0.66 | 0.51 | 394 / 395 | 86.4 (0.78) |
| E L20 r = -0.10 | 25 | 8 / 17 | 0.32 | [0.15, 0.54] | 0.11 | 0.42 | 412 / 395 | 89.3 (0.88) |
| E L20 r = +0.05 | 19 | 8 / 11 | 0.42 | [0.20, 0.67] | 0.65 | 0.50 | 392 / 395 | 85.8 (0.75) |
| E L24 r = -0.10 | 18 | 5 / 13 | 0.28 | [0.10, 0.53] | 0.096 | 0.42 | 399 / 395 | 89.8 (0.93) |
| E L24 r = +0.05 | 22 | 10 / 12 | 0.45 | [0.24, 0.68] | 0.83 | 0.48 | 393 / 395 | 87.5 (0.83) |
| rand0 L16 r = -0.10 | 23 | 11 / 12 | 0.48 | [0.27, 0.69] | 1.00 | 0.47 | 400 / 395 | 87.0 (0.82) |
| rand0 L16 r = +0.05 | 20 | 7 / 13 | 0.35 | [0.15, 0.59] | 0.26 | 0.46 | 395 / 395 | 87.6 (0.85) |
| baseline vs baseline | 16 | 6 / 10 | 0.38 | [0.15, 0.65] | 0.45 | 0.46 | 389 / 395 | 87.6 (0.82) |

Logistic regression on signed dose: not fitted (analyze_dose requires >= 3 doses per (key, layer); this design has
two per layer). Fisher exact, E vs pooled random at the same signed dose and layer (only layer 16 has a random
arm): r = +0.05, E 12/9 vs random 7/13, p = 0.215; r = -0.10, E 2/32 vs random 11/12, p = 0.00033.

## Reading

1. The negative dose (r = -0.1) loses at layers 8, 12 and 16 (win rates 0.12, 0.09, 0.06; all p < 0.001, with the
   resolved share rising from 25/60 at L8 to 34-35/60 at L12-L16). At layers 20 and 24 the same dose is below 0.5
   (0.32, 0.28) but not significant (p = 0.11, 0.096), with fewer resolved pairs (25, 18).
2. The positive dose (r = +0.05) is above 0.5 only at layers 8 (10/3, 0.77, p = 0.092) and 16 (12/9, 0.57,
   p = 0.66); neither reaches significance. Layers 12, 20 and 24 are at or below 0.5 (0.33, 0.42, 0.45). The
   previous run's L16 +0.05 cell (16/5, 0.76, p = 0.027, `essay_redo_L18.md`) is not reproduced here; pooled
   across the two runs the L16 +0.05 cell is 28/14 (0.67, exact p = 0.044).
3. The random direction at layer 16 is null at both doses (0.48 and 0.35), and the baseline-vs-baseline cell is
   6/10 (0.38, p = 0.45). The Fisher test separates E from random at -0.1 (p = 0.00033) but not at +0.05 (p = 0.22).
4. Length barely moves: steered-side means are 386-412 words against 395 for the baseline; the largest shift is
   +17 words at L20 r = -0.1. No truncation in any cell.
5. Coherence stays in the 85-90 range across all cells (baseline 87.6). The lowest value is L12 r = +0.05
   (84.8, pass rate 0.67); the negative-dose cells at L8, L20 and L24 score slightly above baseline. The L12-L16
   negative-dose losses occur at coherence 86.5-88.4, so they are not a degeneration artefact by this measure.
