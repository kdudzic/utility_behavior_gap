# Week 10 results (2026-11-20/21): the rubric coder on essay and grant, the broken tokens, and sampling with the tail cut

Plan: `steering_extension/1811_todo.txt` and `1811_meeting_notes.txt` (meeting of 2026-11-18). Kimi K2.5 is left
for later (PI decision 2026-11-20). Model: Qwen3.5-9B throughout, unless DeepSeek V3.2 is named.

Main results:

- The rubric coder's marker profiles depend on the coder. On grant the paper's coder (gemini) gives one abstract
  the win on all seven markers in 51% of pairs; a second coder does so in 20% and a blind reader in none of 20.
  With a second coder, week 8's "E improves essay content but not framing" does not hold. What both coders agree
  on: E improves grant abstracts on the shared markers (sections 1, 1.1).
- The "broken tokens" are mostly Chinese words in English sentences, in about one Qwen text in ten, steered or not.
  They are rare draws from the tail of the distribution, and the paper's OpenRouter setup produces them too
  (section 2).
- Cutting the tail (top-p 0.95) removes about two thirds of the coherence damage in every group, and E then
  damages no more essays than a random direction or a second unsteered essay (10% against 8% and 12%). The effort
  effect remains (E wins 0.85, random 0.46). So the coherence cost of E found in weeks 6 to 9 is mostly tail draws
  (section 3).

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

### 1.1 Check of the coder: a second coder and a blind reading (2026-11-21)

Two checks of whether these profiles come from the texts or from the coder:

- **Second coder.** The same paper prompt and code with claude-haiku-4.5 instead of gemini-2.5-flash (temperature
  0), on the same 540 pairs: the four essay cells of the table and the five grant cells
  (`rubric_judge.py --cells w10x --coder anthropic/claude-haiku-4.5`, $2.88).
- **Blind reading.** 20 grant pairs (12 that gemini rated the same on all seven markers, 8 mixed) read by a
  separate Claude agent that did not see the coder's verdicts, with the same seven marker definitions
  (`outputs/steering/w10_handcheck/`). It is a second model reader, not a human check.

| | gemini (paper's coder) | haiku | blind reader |
|---|---|---|---|
| essay pairs with the same winner on all markers | 4% | 2% | |
| grant pairs with the same winner on all markers | 51% | 20% | 0 of 20 |
| marker verdicts that are ties, grant | 6% | 8% | 45% (20 pairs) |
| agreement with gemini where both decide, per marker | | essay 67%, grant 73% | 58% (20 pairs) |

The four shared markers by haiku (same pairs as the table above):

| task | side a vs side b | framing | concreteness | objections / risks | no overclaiming |
|---|---|---|---|---|---|
| essay | max-effort prompt vs neutral prompt | +0.42 | 0.00 | -0.08 | -0.33 |
| essay | add E, layer 6, +0.1 | +0.37 | +0.27 | +0.05 | -0.53 |
| essay | add E, layer 14, +0.05 | +0.35 | +0.08 | +0.13 | -0.43 |
| essay | add random direction, layer 6, +0.1 | -0.15 | -0.10 | +0.05 | -0.13 |
| grant | max-effort prompt vs neutral prompt | +0.27 | +0.15 | +0.38 | +0.42 |
| grant | add E, layer 6, +0.05 | +0.30 | +0.13 | +0.30 | +0.17 |
| grant | add E, layer 10, +0.05 | +0.35 | +0.27 | +0.35 | +0.10 |
| grant | add E, layer 16, +0.05 | +0.53 | +0.45 | +0.60 | +0.35 |
| grant | add random direction, layer 10, +0.05 | 0.00 | +0.23 | +0.30 | +0.07 |

- What holds with both coders: E improves grant abstracts on all four shared markers, most at layer 16, and the
  prompt raises framing on essays.
- What does not hold: week 8's "on essays E improves content but not framing" (section 7.3 of the explainer).
  Haiku sees E raise essay framing about as much as the prompt does (+0.35 to +0.37 against +0.42). Which markers
  E moves depends on the coder.
- New with haiku: E essays overclaim more (-0.43 to -0.53, random direction -0.13). This fits the overblown style
  the coherence judge named in week 9.
- gemini's grant codes are mostly an overall verdict copied to every marker. The blind reader saw mixed or small
  differences in the same pairs (no pair with one winner on all seven markers, 45% ties) and agreed with gemini on
  58% of the markers both decided, little above chance.
- Haiku is noisy too: it gives the random direction on grant +0.23 and +0.30 on two markers although the panel
  splits that cell 8 / 8.
- So marker-level profiles from a single LLM coder should not carry conclusions. The panel's overall verdict and
  effects that both coders agree on are what remains.

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
  Section 3 measures this directly.
- E raises the rate only a little (to 15% at +0.1), but section 3 shows that the tail explains most of E's extra
  coherence damage.
- The paper's texts most likely carry the same defect.

## 3. Sampling with the tail cut (2026-11-21)

Does cutting the tail change the coherence results of weeks 6 to 9? Run `w10_tail95` repeats seven week-6/7 essay
cells with the same prompts, vectors, items and repeats, generated with a nucleus cut of top-p 0.95 instead of the
full distribution (`steer/generate.py --top-p`, chain `vast/w10t_chain.sh`, one A100). Both sides of every pair are
cut. The comparison is the same cells sampled from the full distribution (`w6_sweep` for E, `w7_random` for the
random direction, both runs' unsteered pairs). The tail-cut decision (top-p 0.95, these cells) was mine, after the PI
asked to run the check; it is a robustness check next to the paper's protocol, not a replacement. Script
`local/week10_tail.py`, tables in `outputs/steering/w10_analysis/tail_tables.txt`. Manifest: `make_steering_jobs --vectors
outputs/steering/vectors/qwen3.5-9b_v4/vectors.safetensors --run-name w10_tail95 --task essay --items 30 --repeats 2`
with `--cell E:6:0.05 --cell E:6:0.1 --cell E:14:0.05 --cell E:14:0.1 --cell rand0:6:0.1 --cell rand0:14:0.1`.

The cut works: re-read through Qwen, 0.7% of the new tokens lie outside the 0.95 nucleus (2.5% before; not zero
because of numerical differences between batched generation and re-reading), and 8 of 480 texts have a foreign
word (1.7%, against about 9%).

Side a against the unsteered essay of its own run, neutral prompt, essay task. "Damaged": side a more than 3
coherence points below its partner. "Equal coherence": within 3 points.

| side a | sampler | pairs | W / L | win rate | coh a / b | damaged | win rate at equal coherence |
|---|---|---|---|---|---|---|---|
| E added (layers 6 and 14, +0.05 and +0.1) | full | 240 | 67 / 28 | 0.71 | 87.4 / 88.7 | 30% | 0.81 (29 / 7) |
| E added | top-p 0.95 | 240 | 50 / 9 | 0.85 | 91.0 / 91.5 | 10% | 0.90 (43 / 5) |
| random direction added (layers 6 and 14, +0.1) | full | 120 | 17 / 24 | 0.41 | 88.6 / 89.0 | 20% | 0.50 (12 / 12) |
| random direction added | top-p 0.95 | 120 | 13 / 15 | 0.46 | 91.0 / 91.5 | 8% | 0.48 (11 / 12) |
| unsteered (second essay) | full | 120 | 16 / 25 | 0.39 | 87.1 / 88.8 | 28% | 0.40 (6 / 9) |
| unsteered | top-p 0.95 | 60 | 9 / 7 | 0.56 | 90.4 / 91.5 | 12% | 0.78 (7 / 2) |

| test (Fisher) | p |
|---|---|
| damaged, E: top-p 0.95 against full | < 0.001 |
| damaged, random: top-p 0.95 against full | 0.015 |
| damaged, unsteered: top-p 0.95 against full | 0.022 |
| damaged, full: E against random | 0.044 |
| damaged, top-p 0.95: E against random / against unsteered | 0.70 / 0.64 |
| win rate, E: top-p 0.95 against full | 0.053 |
| win rate, top-p 0.95: E against random | < 0.001 |
| panel ties, E: 181 of 240 (top-p 0.95) against 145 of 240 (full) | < 0.001 |

Per cell (W / L, damaged share): E layer 6 +0.05 8 / 1 and 7% (full 15 / 9, 30%); E layer 6 +0.1 17 / 2, 10%
(22 / 3, 17%); E layer 14 +0.05 14 / 2, 8% (17 / 4, 25%); E layer 14 +0.1 11 / 4, 15% (13 / 12, 48%); random layer
6 5 / 7, 5% (7 / 15, 23%); random layer 14 8 / 8, 12% (10 / 9, 17%).

- Cutting the tail removes about two thirds of the coherence damage in every group: E from 30% to 10%, random from
  20% to 8%, unsteered from 28% to 12%. Coherence rises on both sides (about 87 to 89 becomes about 91).
- With the cut, E no longer damages more essays than a random direction or a second unsteered essay (10% against 8%
  and 12%). With the full tail it did (30% against 20%, p = 0.044). So the extra coherence loss under E reported in
  weeks 6 to 9 is mostly tail draws: E makes rare tokens somewhat more likely, and some of them break the text.
- The effort effect survives and looks cleaner. E wins 0.85 against 0.71 with the full tail (p = 0.053) and beats
  the random direction clearly (0.85 against 0.46). The layer-14 +0.1 cell, the most damaged with the full tail
  (48%), goes from 0.52 to 0.73.
- The panel calls more ties with the cut (75% of E pairs against 60%), so fewer pairs are resolved.
- The unsteered null moves from 0.39 (16 / 25) to 0.56 (9 / 7); both are within chance of 0.50 and the new cell
  has only 16 resolved pairs.
- Each sampler has its own texts (new samples), so part of each difference is sampling noise; the pooled
  differences in damage are large enough not to depend on that.

## 4. Not tested

- The rubric comparison at matched doses and layers between tasks, and a human check of the grant codes (the
  blind reading in 1.1 is by a model).
- The tail cut on grant, under the harmful prompt (sandbagging), or on the effort-removal cells; other cuts (top-k
  20, top-p 0.9).
- Whether the paper's own effort results change with a cut (its texts were sampled from the full distribution).
- Garbled English as a category (only foreign scripts are counted).
- Why DeepSeek has almost none: its tail was not measured.

## 5. Cost

OpenRouter, from the usage recorded with every call: rubric coder $0.67 (300 grant pairs), second coder $2.88 (540
pairs), OpenRouter generation $0.10 (600 texts), panel judging of the tail-cut run $1.47 (420 pairs), coherence
$0.44 (480 texts); $5.56 in all. vast: two A100 sessions of about an hour each at $0.72 and $0.57 per hour, about
$1.50 (estimate, not read from the bill).
