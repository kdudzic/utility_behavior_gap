---
title: "SPAR Week 10 Progress Report"
subtitle: "The rubric coder on essay and grant, the broken tokens, and sampling with the tail cut"
author: "Kacper"
date: "2026-11-21"
---

## This week's goals

Goals from the 18.11 meeting:

1. Compare the rubric coder on essay and grant, on the markers the two tasks share.
2. Find out what the broken tokens in unsteered texts are and why they appear.

Follow-ups run on 21.11: a second rubric coder and a blind reading of grant pairs; essays generated with the tail of the distribution cut. Kimi K2.5: left for later.

Every panel number is a pairwise comparison: W / L is pairs won / lost by side a, 0.50 means no effect. E is the effort vector built on essays, so grant is held out for it. Model: Qwen3.5-9B.

## Takeaways

- **The rubric coder's marker profiles depend on the coder.** On grant the paper's coder gives one abstract the win on all seven markers in 51% of pairs, a second coder in 20%, a blind reader in 0 of 20. With a second coder, week 8's "E improves essay content but not framing" does not hold.
- **What both coders agree on: E improves grant abstracts on the shared markers**, most at layer 16.
- **The broken tokens are rare draws from the tail of Qwen's distribution.** Mostly Chinese words, in about one text in ten, steered or not. The paper's OpenRouter setup produces them too.
- **Cutting the tail removes most of E's coherence cost.** With top-p 0.95, E damages 10% of essays, like a random direction (8%) or a second unsteered essay (12%). The effort effect stays: E wins 0.85, random 0.46.

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

## 1b. Check of the coder: second coder and blind reading

Same 540 pairs coded again by claude-haiku-4.5 with the paper's prompt. 20 grant pairs read blind by a separate Claude agent (a model, not a human).

| | paper's coder (gemini) | haiku | blind reader |
|---|---|---|---|
| grant: same winner on all seven markers | 51% | 20% | 0 of 20 |
| essay: same winner on all six markers | 4% | 2% | |
| agreement with gemini per marker | | 67% essay, 73% grant | 58% (chance 50%) |
| essay, E layer 6 +0.1: framing / concreteness | +0.10 / +0.42 | +0.37 / +0.27 | |
| essay, E: no overclaiming | -0.10 | -0.43 to -0.53 | |
| grant, E layer 16: framing / concreteness | +0.38 / +0.63 | +0.53 / +0.45 | |

- Holds with both coders: E improves grant abstracts; the prompt raises essay framing.
- Does not hold: "E improves essay content but not framing". Haiku also finds E essays overclaim more, which fits week 9's overblown style.
- Marker profiles from one LLM coder should not carry conclusions.

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

## 4. Sampling with the tail cut

Week-6/7 essay cells generated again with the same prompts and vectors, top-p 0.95 instead of the full distribution, both sides cut. Side b: the unsteered essay of the same run. "Damaged": side a more than 3 coherence points below side b.

| side a | sampler | W / L | win rate | damaged | coherence a / b |
|---|---|---|---|---|---|
| E added (4 cells, 240 pairs) | full | 67 / 28 | 0.71 | 30% | 87.4 / 88.7 |
| E added | top-p 0.95 | 50 / 9 | 0.85 | 10% | 91.0 / 91.5 |
| random direction (2 cells, 120 pairs) | full | 17 / 24 | 0.41 | 20% | 88.6 / 89.0 |
| random direction | top-p 0.95 | 13 / 15 | 0.46 | 8% | 91.0 / 91.5 |
| unsteered (120 / 60 pairs) | full | 16 / 25 | 0.39 | 28% | 87.1 / 88.8 |
| unsteered | top-p 0.95 | 9 / 7 | 0.56 | 12% | 90.4 / 91.5 |

- The cut removes about two thirds of the damage in every group (p < 0.001 for E).
- With the cut, E damages no more essays than random or unsteered (p = 0.70, 0.64). With the full tail it did (p = 0.044).
- The effort effect stays and is cleaner: E against random 0.85 against 0.46 (p < 0.001). More ties with the cut (75% against 60%).

## Open questions and cost

- Human check of the grant rubric codes, or drop marker-level claims and keep the panel's overall verdict.
- The tail cut on grant, on sandbagging, and on removal cells. Should the extension switch to a cut sampler for coherence work, or keep the paper's protocol and report the cut as a check?
- Why does DeepSeek have almost no foreign words? Its tail was not measured.
- Cost: $5.56 on OpenRouter (second coder $2.88, rubric coder $0.67, judging $1.47, coherence $0.44, generation $0.10) and about $1.50 on vast (two A100 sessions, estimate). Full report: `week10_results.md`.
