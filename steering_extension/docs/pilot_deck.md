---
title: "SPAR Week 4(?) Progress Report"
subtitle: "Steering the effort direction in Qwen3.5-9B: pilot"
author: "Kacper"
date: "2026-10-10"
---

## Research Question & Hypotheses

- **RQ:** are the effort and expert roleplay effects carried by a single direction in the residual stream, and does their size correspond to a dose?
- **Hypotheses:**
  - H1: Adding the direction to a neutral prompt wins like the effort prompt does
  - H2: Removing the direction cancels the effect
  - H3: Random directions of equal size do nothing, fluency stays intact

## Design

- **Model.** Qwen3.5-9B (only OW actor in the paper); thinking off, temperature 1.0, prompts from the paper
- **Vectors.** E (effort), R_id (world-class vs skilled), R_act (act-as persona). Extracted from the paper's grant, postmortem, and translation tasks, with the essay test held out (prompts per direction per vector: 90 x 2 x 3). Readout from response token means
- **Dose unit.** Fraction *r* of the layer's residual norm; natural prompt shift at layer 16 is r = 0.014. **Proposed by Claude**
- **Cells.** Main curve at layer 16, r in {-0.2, -0.1, -0.05, +0.05, +0.1, +0.15}; layer check at layers 12 and 20 at +/-0.1; two random same-norm directions; baseline vs baseline null check

## Analysis pipeline

- Judging reuses the paper's unchanged script and panel: claude-haiku-4.5, gemini-3.1-flash-lite, gpt-5-mini
- Per cell: win rate, exact-binomial 95% CI, two-sided binomial p. Trend: logistic regression of win on signed dose with item-clustered SEs. Specificity: Fisher test of E vs pooled random directions at the same norm. **Proposed by Claude**
- Some side checks: one judge coherence, word counts, truncation.
- Vector quality: split-half cosine between vectors from two independent halves of the data. **Proposed by Claude.** This disqualified the role vectors (pure noise)

## Results (for now, Claude analysis)

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

- Dose trend: steep and monotone from -0.2 to +0.05 (p = 5e-12), then reverses. Same at layers 12 and 20
- E vs random at -0.2: Fisher p = 7e-6. Split-half reliability: E 0.65, R_act 0.22, R_id -0.05

## What it means and what is next

- **H1 not shown.** No positive dose beats baseline; above r = 0.05 prose becomes very... flowery(?) and fluency drops. The unsteered model already sits near the judges' optimum
- **H2 supported.** Removing the direction destroys judged quality while prose stays fluent and the same length. Essays turn plain and formulaic.
- **H3 mostly supported.** Random directions cost a little at the largest dose, E costs 20x more at half the norm.
- **My observation.** E behaves like a rhetorical-elaboration dial the judges reward in moderation; the prompt's +20-word length effect is not reproduced by steering
- **Role.** No reproducible role direction with this recipe. This does match the paper's weak role effects, but role steering needs a new extraction method
