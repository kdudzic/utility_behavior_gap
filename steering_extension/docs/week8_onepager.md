---
title: "Week 8 in one page: is the effort vector's effect a coherence effect, and is there a role direction?"
author: "Steering extension of the utility-behavior gap paper, Qwen3.5-9B"
date: "2026-11-07"
titlepage: false
fontsize: 9pt
geometry: "a4paper, margin=1.5cm"
colorlinks: true
header-includes:
  - \usepackage{setspace}
  - \setstretch{1.03}
  - \setlength{\parskip}{4pt}
  - \usepackage{float}
  - \setkeys{Gin}{keepaspectratio}
  - \floatplacement{figure}{H}
  - \setlength{\textfloatsep}{6pt}
  - \setlength{\intextsep}{4pt}
...

**Design.** Every number is a pairwise comparison on the essay task. For each topic and repeat the model writes one essay with the intervention (side a) and one without (side b) from the same neutral prompt. The paper's three judges pick the better essay in both orders, flipped judges count as ties, and pairs the panel ties are dropped. W / L is the number of pairs side a won and lost. 0.50 means no effect, the pooled null cells give 71 / 69. Coherence is a separate 0 to 100 score from claude-haiku-4.5 at temperature 0, told to ignore quality. Unsteered essays score 87 to 89. The effort vector E is the week-6 difference of means (max-effort minus neutral). The dose r is a fraction of the layer's residual RMS, and r < 0 removes the direction. Full report: `week8_results.md`.

**1. The effort vector's win-rate effects are not coherence effects.** Across the week-7 grid (layers 6 to 20, r from -0.1 to +0.1) random directions keep coherence at 87.6 to 89.2 in every cell. The effort vector keeps it at removal and at +0.05 up to layer 14 and loses 2 to 5 points only at +0.1 from layer 10 on. Ablation is the one intervention with a clear cost (-5.4 at layers 8 to 16). The win rates differ where coherence does not. At layers 6 to 14 removal wins 0.06 to 0.19 against random's 0.26 to 0.53, and addition wins 0.62 to 0.88 against 0.26 to 0.50 (figure 1).

**2. The panel follows coherence, but the effort effect survives at equal coherence.** Over 9,120 judged pairs, whenever the two essays differ in coherence by more than 3 points the panel picks the more coherent one 85 to 100% of the time, in null cells too. Among pairs within 3 points of each other, effort removal wins 0.10 (346 pairs), effort addition 0.71 (302 pairs), random 0.41 to 0.47, null 0.50. Restricted to layers 6 to 14, removal at -0.1 wins 0.00 of 99 equal-coherence pairs and addition at +0.1 wins 0.90 of 40 (figure 2). Random directions lose through small coherence losses the panel punishes.

**3. The paper's rubric coder sees the vector doing part of what the prompt does.** The paper's blind coder (gemini-2.5-flash, temperature 0, six essay markers, 660 calls) was run on our judged pairs. Our exhortation matches the paper's profile (thesis, depth, example and closure up 0.3 to 0.4). Adding E raises argument depth (+0.40 to +0.45) and concrete example (+0.42) but not thesis framing or closure (+0.03 to +0.10). Removing E lowers every content marker by 0.5 to 0.8 with plausibility flat. Ablation under the exhortation is the only cell marked less plausible (-0.28). The vector improves reasoning and examples, the prompt also improves framing and flow.

**4. The role cue is mostly the effort direction, and five role-vector recipes give no role direction separate from effort.** Untouched "world-class essayist" essays sit along E at half to two thirds of the exhortation's shift (ratio 0.51 to 0.65, AUC 0.60 to 0.74). Along the part of the role vector that is not E, nothing separates (AUC 0.50 to 0.57). We then steered with five role vectors at the three clearest effort cells, each also with its E component projected out (figure 3, table).

| vector | contrast | reliability (split-half) | steering result |
|---|---|---|---|
| R_id | world-class vs skilled (v4) | -0.55 | weak E; minus E, the layer-10 removal effect is gone (11 / 15, p = 0.002 vs E) |
| R_act | "pretend and act as" vs direct cue | -0.47 | random level everywhere |
| R_sharp | R_id pairs with the largest judge-scored craft gap | weak filter | E again at removal (2 / 29, 1 / 30); minus E a weak loss (7 / 18, 6 / 20) |
| R_wide | 20 world-class vs 20 novice paraphrases | 0.70 to 0.87 | removal 0 / 56, 2 / 55, also minus E (0 / 57, 0 / 54); addition 12 / 5, minus E 6 / 9 |
| R_content | world-class essayist vs world-class other profession | 0.34 to 0.65 | random level everywhere |

R_wide is the first reliable role vector. Its removal pushes the essay toward "novice" and loses nearly every pair, with the essays intact (coherence 80, plain student prose) and the effect intact after projecting E out. Its addition helps only through its E component. So R_wide-minus-E is a competence direction that only works when removed, not the "world-class essayist" identity.

**Takeaways.** The effort direction's effect is real at equal coherence, moves the content markers the exhortation moves, and is what the role prompt mostly acts through. No recipe tried gives a role direction that improves essays independently of E. Open: adding R_wide-minus-E at layers 10 to 16 or at smaller doses. Cost this week about $10.33 OpenRouter and $2.65 GPU rental.

\newpage

![Coherence of the steered essay for the effort direction and a random direction, by layer and dose. Random directions never change coherence. The effort vector costs coherence only at +0.1 from layer 10 on.](results/2026-11-06_w8/coherence_grid.png){width=100%}

![Panel decision against the within-pair coherence gap. Wherever the gap exceeds 3 points every group follows coherence. In the equal-coherence bin (-3 to 3) effort removal still loses (0.10) and effort addition still wins (0.71) while random and null sit at 0.41 to 0.50.](results/2026-11-06_w8/pairs_winrate_by_coherence_gap.png){width=60%}

![Win rate of each role vector (filled) and of the same vector with its E component projected out (hollow) at the three cells, against the effort vector (blue line) and a random direction (orange line). Only R_wide at removal beats E, and it does so by making the prose simpler.](results/2026-11-06_w8/role_recipes_winrate.png){width=100%}
