# Week 10 results (2026-11-20): the rubric coder on essay and grant, and the broken tokens in unsteered texts

Plan: `steering_extension/1811_todo.txt` and `1811_meeting_notes.txt` (meeting of 2026-11-18). Kimi K2.5 is left
for later (PI decision 2026-11-20). Model: Qwen3.5-9B throughout, unless DeepSeek V3.2 is named.

## 0. How to read the tables

Every panel number is a pairwise comparison, as in the paper. For each item and repeat the model writes one text
for side a and one for side b. The paper's three judges pick the better one in both orders; flips count as ties
and panel ties are dropped. W / L is the number of pairs side a won and lost, and 0.50 means no effect.

The rubric coder is the paper's blind task-rubric coder with its code unchanged (google/gemini-2.5-flash,
temperature 0, the two texts shown as A and B in random order). For each marker it says which text is better, or
neither. delta = share of pairs where side a is better minus share where side b is better, from -1 to +1. 60 pairs
per cell.

Prompt, all cells: the paper's competition wrapper with no effort or role cue ("neutral"), except the max-effort
rows. "Unsteered" is the same prompt, generated without a vector. E is the effort vector built on essays (week 7),
so it is held out for grant. r is the dose as a fraction of the layer's residual size.

## 1. The rubric coder on essay and grant (todo item 1)

The essay rubric has six markers and the grant rubric seven, with no names in common. Four pairs mean the same
thing (PI decision 2026-11-20, from the paper's own definitions of each marker):

| essay marker | grant marker | shared idea |
|---|---|---|
| thesis_stakes_framing | problem_significance | why it matters |
| concrete_example_quality | intervention_specificity | concreteness |
| counterargument_qualification | risk_mitigation | anticipates objections or risks |
| plausibility_overreach | measurable_impact | credible claims, no overclaiming |

Not compared: essay argument_depth and rhetorical_coherence_closure; grant evaluation_rigor,
feasibility_implementation_readiness and stakeholder_context_fit.

New this week: the coder on five grant cells (300 pairs, `local/rubric_judge.py --cells w10`). The essay rows are
week 8's. Side b is the unsteered text, except in the prompt rows, where it is the neutral-prompt text.

| task | side a vs side b (panel W / L) | framing | concreteness | objections / risks | no overclaiming |
|---|---|---|---|---|---|
| essay | max-effort prompt vs neutral prompt (14 / 7) | +0.38 | +0.27 | +0.12 | 0.00 |
| essay | add E, layer 6, +0.1 (22 / 3) | +0.10 | +0.42 | -0.02 | -0.10 |
| essay | add E, layer 14, +0.05 (17 / 4) | +0.08 | +0.10 | +0.17 | -0.10 |
| essay | add random direction, layer 6, +0.1 (7 / 15) | -0.20 | -0.27 | +0.02 | -0.05 |
| grant | max-effort prompt vs neutral prompt (24 / 5) | +0.55 | +0.60 | +0.60 | +0.52 |
| grant | add E, layer 6, +0.05 (15 / 7) | +0.22 | +0.30 | +0.30 | +0.07 |
| grant | add E, layer 10, +0.05 (14 / 7) | +0.28 | +0.23 | +0.37 | +0.28 |
| grant | add E, layer 16, +0.05 (13 / 4) | +0.38 | +0.63 | +0.67 | +0.43 |
| grant | add random direction, layer 10, +0.05 (8 / 8) | +0.08 | +0.03 | +0.15 | +0.07 |

95% intervals are about ±0.2 (bootstrap over pairs; full tables in `outputs/steering/w10_rubric/rubric_summary.md`).

- On essays, E raises concreteness (+0.42 at layer 6) but not framing (+0.08 to +0.10), while the prompt raises
  both. On grant, E raises all four, framing included (+0.22 to +0.38), as the prompt does. The essay pattern
  ("the vector improves content, not framing") does not carry over to grant.
- On grant the coder hardly tells its markers apart. It names the same winner on all seven markers in 51% of
  pairs, against 6% on essays (week-8 cells). So on grant the markers mostly measure overall quality, and the
  difference in profile between the tasks may come from the coder rather than from the vector.
- E helps on grant at every layer tested, the random direction does not (+0.03 to +0.15).
- The cells are not matched between tasks: on essays E is at +0.1 (layer 6) and +0.05 (layer 14), on grant all
  three layers are at +0.05; the random control is at layer 6 on essays and at layer 10 on grant.

## 2. The broken tokens in unsteered texts (todo item 2)

In week 9 the coherence judge named "broken tokens" in 60% of its explanations for pairs of two unsteered essays.
Script `local/week10_tokens.py` scans every text of every run for words in another script inside the English text
(CJK, kana, Hangul, Cyrillic, Arabic, Hebrew, Indic scripts, Thai, Greek, Vietnamese letters, the replacement
character). Tables in `outputs/steering/w10_analysis/tokens_tables.txt`.

### 2.1 What they are

Mostly single Chinese words in the middle of an English sentence, often with the right meaning in the wrong
language:

- "...and免费的 access reinforces the idea..." (free)
- "...quantitative analysis of decision准确度 rates..." (accuracy)
- "...wearable GPS trackers and家长的 direct feedback logs..." (parents')
- "...preventing вспышки (outbreaks) that could..." (Russian, followed by its own translation)

Among the Qwen texts that have them, the scripts are CJK (2,068 texts), Cyrillic (158), the replacement character
(63), Arabic (45) and a few others.

### 2.2 How often, and steering has little to do with it

| texts (distinct) | with a foreign word |
|---|---|
| Qwen, unsteered, essay | 168 of 2,224 (7.6%) |
| Qwen, unsteered, grant | 189 of 1,860 (10.2%) |
| Qwen, E added, by dose (+0.025, +0.05, +0.075, +0.1) | 11.0%, 11.5%, 12.8%, 14.8% |
| Qwen, random direction added | 8% to 9% |
| DeepSeek V3.2, unsteered (essay and grant) | 0 of 480 |
| DeepSeek V3.2, steered | 1 of 840 |

About one Qwen text in ten has one, with or without steering. Adding E raises the rate a little at higher doses.

### 2.3 Is it our setup? The paper's settings through OpenRouter

Our local generation samples from the full distribution at temperature 1.0 (`top_p 1.0`, `top_k 0`). The paper
generated through OpenRouter at temperature 1.0 with the provider's defaults. We generated 300 essays and 300 grant
abstracts with the paper's own script, prompts and settings (runs `w10_or_essay` and `w10_or_grant`, neutral
prompt, 30 items x 5 repeats x 2 sides):

| unsteered Qwen texts | local | OpenRouter, paper settings | Fisher p |
|---|---|---|---|
| essay | 152 of 1,924 (7.9%) | 16 of 300 (5.3%) | 0.13 |
| grant | 167 of 1,560 (10.7%) | 22 of 300 (7.3%) | 0.09 |

The paper's texts very likely had them too, perhaps somewhat less often. It is a property of Qwen, not of our setup.

### 2.4 Where they come from: the tail of the distribution

`steer/token_probs.py` re-reads 1,320 unsteered texts through Qwen (one A100, chain `vast/w10_chain.sh`) and records
for every token its probability and rank at temperature 1.0. Qwen's own generation config sets no top-k or top-p.

| | local, essay | local, grant | OpenRouter, essay | OpenRouter, grant |
|---|---|---|---|---|
| texts | 120 | 600 | 300 | 300 |
| tokens outside the 20 most likely | 1.3% | 0.9% | 1.0% | 0.7% |
| tokens outside the 0.95 nucleus | 2.7% | 2.5% | 2.2% | 2.0% |
| texts with at least one token outside the top 20 | 100% | 93% | 74% | 74% |

| foreign-script tokens | local | OpenRouter |
|---|---|---|
| tokens | 82 | 39 |
| median probability | 0.00008 | 0.00002 |
| median rank | 55 | 283 |
| outside the 20 most likely | 63% | 85% |
| probability below 0.01 | 82% | 95% |

- The foreign words are tail draws. Their median probability is about 1 in 12,000 and most lie outside the 20 most
  likely tokens. With top-k 20 or top-p 0.95 most of them would not be sampled.
- About 1% of all tokens in a text are such tail draws. Most are harmless English alternatives. Qwen's vocabulary
  has many Chinese tokens, so some draws land there.
- OpenRouter's texts also contain tokens far outside the top 20, so its provider did not cut the distribution
  either. They have somewhat fewer tail tokens (0.7% to 1.0% against 0.9% to 1.3%). Why (different precision on
  the provider's side, or a mild cut) is not known.

### 2.5 Does this explain the coherence judge's "broken tokens"?

About half. Of the 254 explanations coded "broken tokens", 129 are about an essay that contains a foreign word. In
the other 125 the judge quotes garbled English, such as "Theshield", "Furthermore,gregated" or "New York chap",
which are likely tail draws too but are not detected by script. For the pairs of two unsteered essays the share
with a foreign word is 29%.

### 2.6 What it means for our results

- Both sides of every pair come from the same sampler, so the pairwise comparisons stay fair. But about one text in
  ten carries a visible defect unrelated to the intervention. That adds noise to the panel and to the coherence
  scores, and it is part of why pairs of two unsteered essays get "damaged" coherence by chance (22%, week 9).
- It does not explain the effort results: E raises the rate only a little (to 15% at +0.1).
- The paper's texts most likely carry the same defect.

## 3. Not tested

- The rubric comparison at matched doses and layers between tasks, and a second coder or a hand check of the grant
  codes (the coder's lack of separation on grant is the main limit).
- Whether texts sampled with top-k or top-p win or lose against full-distribution texts (no generation with a cut
  was run).
- Garbled English as a category (only foreign scripts are counted).
- Why DeepSeek has almost none: its tail was not measured.

## 4. Cost

OpenRouter, from the usage recorded with every call: rubric coder $0.67 (300 pairs), generation $0.10 (600 texts),
$0.77 in all. vast: one A100 for about an hour at $0.72 per hour, about $1 (estimate, not read from the bill).
