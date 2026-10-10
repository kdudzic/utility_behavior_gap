---
title: "Steering the effort direction in Qwen3.5-9B"
subtitle: "Pilot extension of Zhou & Ackerman, *A Utility-Behavior Gap in LLMs*"
author: "K. Dudzic"
date: "2026-10-10"
---

## Question, assumptions, hypotheses

- **Parent paper.** Telling a model "use maximum effort" raises judged essay quality (~70% pairwise wins); telling it it is "world-class" barely does (~55%); its own stated preferences do nothing.
- **Question.** Is the effort effect carried by a single direction in the residual stream, and does its size follow a dose?
- **Assumptions.** The paper's cells reproduce on a local white-box copy of Qwen3.5-9B; a diff-of-means direction (effort prompt minus no-effort prompt) is a fair candidate mediator; the paper's blind 3-judge panel is the outcome.
- **Hypotheses.** H1 *sufficiency*: adding the direction to a neutral prompt wins like the prompt does. H2 *necessity*: removing it cancels the effect. H3 *specificity*: random directions of equal size do nothing, fluency stays intact.

## Design and decisions

- **Model.** Qwen3.5-9B, only open-weight actor in the paper's roster; thinking off, temperature 1.0, prompts byte-identical to the paper.
- **Vectors.** E (effort), R_id (world-class vs skilled), R_act (act-as persona). Extracted from the paper's *other three tasks* (grant, postmortem, translation) so the essay test items stay held out. Response-token-mean readout, 180 responses per arm.
- **Dose unit.** Fraction *r* of the layer's residual norm; natural prompt shift at layer 16 is r = 0.014.
- **Cells.** Layer 16, r in {-0.2, -0.1, -0.05, +0.05, +0.1, +0.15}; layers 12 and 20 at +/-0.1; two random same-norm directions; baseline vs baseline null. 60 pairs per cell, steered essay vs unsteered essay on the same topic.
- **Decided with PI.** Pilot before full grid; coherence floor 80/100; shared baseline across doses; stop before the full grid.

## Analysis pipeline

- SLURM jobs on Athena (A100 40 GB, 4-8 GPUs in parallel): hooked HF generation writes the paper's own `generations.jsonl` schema.
- Judging reuses the paper's unchanged script and panel: claude-haiku-4.5, gemini-3.1-flash-lite, gpt-5-mini; both presentation orders; order flips become ties; ties excluded; majority of three.
- Per cell: win rate, exact-binomial 95% CI, two-sided binomial p. Trend: logistic regression of win on signed dose with item-clustered SEs. Specificity: Fisher test of E vs pooled random directions at the same norm.
- Side checks: coherence 0-100 by one judge (baseline scores ~88), word counts, truncation.
- Vector quality: split-half cosine between vectors from two independent halves of the data.

## Results

| Replication (local vs paper) | pairs | win rate | paper |
|---|---|---|---|
| max-effort prompt vs neutral | 150 | 0.71 (p = 0.01) | 0.67 |
| world-class vs skilled role | 150 | 0.55 (n.s.) | 0.57 |

| E dose at layer 16 | W / L | win rate | coherence pass |
|---|---|---|---|
| -0.20 | 1 / 54 | 0.02 | 0.88 |
| -0.10 | 7 / 26 | 0.21 | 0.92 |
| +0.05 | 11 / 6 | 0.65 (n.s.) | 0.80 |
| +0.10 | 8 / 16 | 0.33 | 0.48 |
| +0.15 | 0 / 30 | 0.00 | 0.28 |
| random, -0.2 (pooled) | 16 / 30 | 0.35 | 0.75 |

- Dose trend: steep and monotone from -0.2 to +0.05 (p = 5e-12), then reverses. Same at layers 12 and 20.
- E vs random at -0.2: Fisher p = 7e-6. Split-half reliability: E 0.65, R_act 0.22, R_id -0.05.

## What it means and what is next

- **H2 necessity (by subtraction): supported.** Removing the direction destroys judged quality while prose stays fluent and the same length. Essays turn plain and formulaic.
- **H3 specificity: mostly supported.** Random directions cost a little at the largest dose, E costs 20x more at half the norm.
- **H1 sufficiency: not shown.** No positive dose beats baseline; above r = 0.05 prose turns purple and fluency drops. The unsteered model already sits near the judges' optimum on this axis.
- **Reading.** E behaves like a rhetorical-elaboration dial the judges reward in moderation; the prompt's +20-word length effect is *not* reproduced by steering.
- **Role.** No reproducible role direction with this recipe; matches the paper's weak role effects, but role steering needs a new extraction method.
- **Next.** Ablation arm (project the direction out under the effort prompt), prompt-token readout for cleaner vectors, feature-signature comparison with the paper's Table 2, then the full task grid and the 27B model. Cost so far: $16 judging, ~10 GPU-hours.
