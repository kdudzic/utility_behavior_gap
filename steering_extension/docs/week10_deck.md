---
title: "SPAR Week 10 Progress Report"
subtitle: "The rubric coder on essay and grant, and the broken tokens in unsteered texts"
author: "Kacper"
date: "2026-11-20"
---

## This week's goals

Goals from the 18.11 meeting:

1. Compare the rubric coder on essay and grant, on the markers the two tasks share.
2. Find out what the broken tokens in unsteered texts are and why they appear.

Kimi K2.5: left for later.

Every panel number is a pairwise comparison: W / L is pairs won / lost by side a, 0.50 means no effect. E is the effort vector built on essays, so grant is held out for it. Model: Qwen3.5-9B.

## Takeaways

- **On grant, adding E improves every shared marker, framing included.** On essays it improved concreteness but not framing. The essay pattern does not carry over.
- **But on grant the coder hardly separates its markers.** It names the same winner on all seven markers in 51% of pairs (essays: 6%), so the grant profile mostly measures overall quality.
- **The broken tokens are mostly Chinese words inside English sentences.** About one Qwen text in ten has one, steered or not. DeepSeek has almost none.
- **They are rare draws from the tail of Qwen's distribution, and the paper's setup produces them too.** Their median probability is about 1 in 12,000. Texts made with the paper's settings through OpenRouter have them at a similar rate.

## 1. The rubric coder on essay and grant

The paper's blind coder (gemini-2.5-flash, code unchanged), 60 pairs per row. delta = share where side a is better minus share where side b is better. Side b: the unsteered text, or the neutral-prompt text in the prompt rows. Four marker pairs mean the same thing.

| task | side a (panel W / L) | framing | concreteness | objections / risks | no overclaiming |
|---|---|---|---|---|---|
| essay | max-effort prompt (14 / 7) | +0.38 | +0.27 | +0.12 | 0.00 |
| essay | E, layer 6, +0.1 (22 / 3) | +0.10 | +0.42 | -0.02 | -0.10 |
| essay | random, layer 6, +0.1 (7 / 15) | -0.20 | -0.27 | +0.02 | -0.05 |
| grant | max-effort prompt (24 / 5) | +0.55 | +0.60 | +0.60 | +0.52 |
| grant | E, layer 16, +0.05 (13 / 4) | +0.38 | +0.63 | +0.67 | +0.43 |
| grant | E, layer 10, +0.05 (14 / 7) | +0.28 | +0.23 | +0.37 | +0.28 |
| grant | random, layer 10, +0.05 (8 / 8) | +0.08 | +0.03 | +0.15 | +0.07 |

- Framing = thesis framing (essay) / problem significance (grant). Concreteness = concrete example / intervention specificity. Objections = counterargument / risk mitigation. No overclaiming = plausibility / measurable impact.
- Intervals are about ±0.2. Doses and layers differ between the tasks.

## 2. The broken tokens: what they are and how often

Scan of every generated text for words in another script inside English text.

| texts | with a foreign word |
|---|---|
| Qwen, unsteered, essay | 7.6% (168 of 2,224) |
| Qwen, unsteered, grant | 10.2% (189 of 1,860) |
| Qwen, E added, +0.025 to +0.1 | 11% to 15% |
| Qwen, random direction added | 8% to 9% |
| DeepSeek V3.2, all texts | 1 of 1,320 |

- Examples: "and免费的 access" (free), "decision准确度 rates" (accuracy), "preventing вспышки (outbreaks)".
- They explain about half of the coherence judge's "broken tokens". The other half is garbled English ("Theshield", "Furthermore,gregated").

## 3. The broken tokens: where they come from

We sample at temperature 1.0 from the full distribution. We generated 600 texts with the paper's settings through OpenRouter and re-read texts through Qwen to get each token's probability.

| | ours | paper's settings (OpenRouter) |
|---|---|---|
| essays with a foreign word | 7.9% | 5.3% (p = 0.13) |
| grant abstracts with a foreign word | 10.7% | 7.3% (p = 0.09) |
| tokens outside the 20 most likely | 0.9% to 1.3% | 0.7% to 1.0% |
| foreign tokens: median probability | 0.00008 | 0.00002 |
| foreign tokens outside the 20 most likely | 63% | 85% |

- The foreign words are rare tail draws. Sampling with top-k 20 or top-p 0.95 would remove most of them.
- The paper's provider does not cut the tail either, so the paper's texts most likely have them too.
- Both sides of every pair come from the same sampler, so comparisons stay fair, but about one text in ten carries a defect unrelated to the intervention.

## Open questions and cost

- Grant rubric: a second coder or a hand check, since the coder barely separates markers on grant.
- Rubric at matched doses and layers on both tasks.
- Do texts sampled with top-k or top-p win against full-distribution texts? Not run.
- Why does DeepSeek have almost none? Its tail was not measured.
- Cost: $0.77 on OpenRouter (rubric coder $0.67, generation $0.10) and about $1 on vast (one A100 for an hour). Full report: `week10_results.md`.
