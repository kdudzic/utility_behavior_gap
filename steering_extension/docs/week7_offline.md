# Week 7, offline part: what the steered and ablated essays look like, coherence, paper features

Date: 2026-10-30. Items 1 to 3 of `week7_plan.txt` (meeting note `steering_extension/2810_meeting_notes.md`).
Everything here is computed from the week-6 outputs (`week6_results.md`); no new generations or judge calls.
Vocabulary as in week 6: the vector is the response-mean effort direction (v4); dose r is a fraction of the
layer's RMS residual norm; "remove" is r < 0, "add" is r > 0; win rate is the share of resolved pairs the paper's
three-judge panel gave to the steered (or ablated) essay; coherence is the one-judge 0-100 score.

## 1. Qualitative study

### 1.1 Ablation at layers 8 to 16 under the max-effort prompt (3 / 17, coherence 82 against 88)

Read side by side with their untouched twins (same prompt, same repeat). What changes:

- **The register goes purple.** Ablated essays pile up metaphors and slogans: "the CD4 count of our democracy",
  "inviting wolves into a barn", "a world burning with data", "the human chorus until it drowns out the
  cacophony". Untouched twins argue in plainer, thesis-first prose.
- **Invented specifics.** Ablated essays reach for concrete-sounding numbers and anecdotes that do not exist
  ("a turnout of ninety-eight percent", "12 million voices in Canberra", "a 15% surge in local business
  sales"). Untouched twins stay general or hedge.
- **Token glitches.** Fused or foreign tokens appear in otherwise fluent text ("theregarul routine", "the沉默 is
  the exception", "withparallel it", "high-capublic"). 13% of ablated essays contain a non-Latin character or a
  fused 20+ letter word, against 5% of untouched max-effort essays (table in 1.3).
- **Form.** Ablated essays more often carry a bold title (0.73 against 0.42 per essay) and are cut into more,
  shorter sentences (21.3 against 19.0 sentences at the same length, 408 against 412 words).

Why coherence stays high while the judges prefer the twin: the coherence judge scores readable, on-topic,
non-repetitive text, and these essays are readable and on topic. The quality judges see overwrought style,
fabricated detail and the occasional broken word, and the untouched twin is sober and clean. Coherence 72 to 82
is where most ablated essays land (the distribution: one at 45, one at 62, fourteen at 72, seven at 78, fifteen
at 82, twenty-two at 92). Only the 45 and the 62 read as damaged; the rest read as a worse writer.

This is a different failure from removing the vector by steering under the neutral prompt (1.2). Ablation under
the exhortation prompt makes the essay louder and sloppier. Steering the vector out under the neutral prompt
makes it blander.

### 1.2 The striking steering cells

Three pairs read per cell plus cell-level counts. Short excerpts here; the full dumps are local scratch files.

**Remove at layer 16, r = -0.1 (5 / 37).** Same length (398 against 393 words), coherence 89. The steered
essays are textbook essays: "First, ... Secondly, ... Thirdly," a thesis restated in the conclusion, no title,
fewer concrete cases and numbers, more stock phrases ("plays a pivotal role", "fostering informed consumer
choices"). Untouched twins open with a hook or a title, name cases and figures, vary sentence length. Judges pick
the twin. The paper features agree (section 3): rare-word rate, semicolons and unique-word ratio drop by about one
standard deviation, positive-sentiment words rise.

**Remove at layer 6, r = -0.2 (0 / 54).** Shorter (360 against 393 words) and the same blandness, now with
coherence cost (mean 83, 30% of essays under 80). Part damage, part the same drift as above.

**Add at layer 6, r = +0.1 (22 / 3).** Longer (415 against 393 words), coherence 89, glitch rate 8% (baseline
8%). The steered essays give more specifics per point (a worker "forced to fund their own banking
infrastructure and health coverage", athletes "in the weight room by 6:00 AM"), use more sentences of shorter
length (20.0 against 21.5 words per sentence), more semicolons and rare words, fewer positive-sentiment words.
This is the direction the real exhortation moves the same features (section 3).

**Remove at layer 16, r = -0.1, prompt tokens only (8 / 20).** Slightly shorter (389 against 399 words), fewer
bold titles (0.17 against 0.42), coherence 89. Same blandness as the response-only removal, weaker. With the
vector removed on prompt and response tokens (1 / 47) the texts look like the response-only removal, one step
further.

### 1.3 Glitch rate per condition

Share of essays containing a non-Latin character or a fused word of 20 or more letters
(`outputs/steering/glitch_rate_w6.csv`):

| condition | glitch rate |
| --- | --- |
| unsteered baseline (10 cells) | 0.08 |
| max-effort prompt, untouched | 0.05 to 0.11 |
| remove L16 -0.1 (response / prompt / both) | 0.03 / 0.05 / 0.05 |
| remove L6 -0.2 | 0.00 |
| add L6 +0.1 | 0.08 |
| add L16 +0.1 | 0.17 |
| add L18 +0.1 (highest steering cell) | 0.22 |
| ablate E at layers 8 to 16, max-effort prompt | 0.13 |
| ablate rand0 at all 32 layers | 0.08 |
| ablate E at all 32 layers | 0.78 |

Removing the vector does not add glitches. Adding it at mid layers and high doses does (0.17 to 0.22 at layers
12 to 20 for r >= +0.075), which is where the positive side of the sweep turns down.

## 2. Coherence close-ups

Unsteered essays: mean 87.5 to 89.8 across runs, 80 to 90% of essays at or above 80. All 175 condition means are in
`outputs/steering/coherence_all_conditions.csv`; the sweep heatmap is
`results/2026-10-27_w6_sweep/coherence_heatmap.png`.

| steering form | cells | mean coherence | share >= 80 | lowest cell |
| --- | --- | --- | --- | --- |
| unsteered baseline, week-6 runs | 14 | 88.3 | 0.86 | 87.3 |
| remove, r = -0.05 and -0.1, all layers | 24 | 89.2 | 0.88 | 87.3 |
| remove, r = -0.2, all layers | 12 | 86.9 | 0.82 | 82.9 |
| add, r = +0.025 and +0.05, all layers | 24 | 87.2 | 0.80 | 84.6 |
| add, r = +0.075 and +0.1, layers 6 to 14 | 10 | 86.1 | 0.75 | 84.2 |
| add, r = +0.075 and +0.1, layers 16 to 28 | 14 | 84.7 | 0.71 | 80.6 |
| random directions, layer 16 | 4 | 87.1 | 0.81 | 85.1 |
| multi-layer | 5 | 86.8 | 0.80 | 85.3 |
| prompt-only and prompt+response | 4 | 87.5 | 0.82 | 84.9 |
| other readouts | 14 | 87.8 | 0.83 | 86.0 |
| ablate E, layers 8 to 16, max-effort prompt | 1 | 82.2 | 0.63 | |
| ablate E, all 32 layers, max-effort prompt | 1 | 2.4 | 0.00 | |

- **Where it drops.** Adding at r >= +0.075, more so from layer 16 on (80.6 at layer 16 +0.1, 81.3 at layer 18
  +0.1); removing at r = -0.2 (82.9 to 86 at layers 6 to 12); local ablation (82.2); all-layer ablation (2.4).
- **Where it holds.** Removing at -0.05 and -0.1 at every layer; adding at +0.025 and +0.05; random directions;
  multi-layer; both position modes; all other readouts. All within 2 points of baseline.
- **Where it rises.** Removing at r = -0.1 gives the highest coherence of any form: 89.4 mean over the 12 layers,
  top cells 90.3 (layers 18 and 22) with 93% of essays at or above 80, against 87.5 to 88.7 for the baseline in
  the same run. The difference is 1 to 2 points, within the spread between baseline cells (86.9 to 89.8), so it
  is at most a small effect. It fits the qualitative picture: removal yields plainer, safer, more conventional
  text, which the coherence judge likes and the quality judges do not.
- Coherence and win rate move together only at the extremes. Removal at -0.1 loses with coherence intact;
  addition at layer 6 wins with coherence intact; addition at layer 16 and above at high dose loses and loses
  coherence; local ablation loses with a moderate coherence cost.

## 3. Paper text features on the week-6 runs

Features computed with the paper's own code (`text_features.py`, the paper's `scalar_features`); per-cell
paired deltas (steered minus unsteered, same item and repeat) standardised by their SD, as in the paper's feature
tables. Reference: the paper's own direct-exhortation deltas for Qwen3.5-9B essays
(`data/processed/final_text_analysis_pair_deltas.csv.gz`). Table:
`outputs/steering/feature_deltas_key_cells_w6.csv`. Correlation across the 14 paper features between each cell's
standardised deltas and the paper's, and the share of features with the same sign:

| cell | r with paper exhortation signature | same sign |
| --- | --- | --- |
| max-effort prompt vs neutral, our pipeline (60 pairs) | +0.96 | 0.93 |
| add, layer 6, +0.1 | +0.51 | 0.57 |
| add, layer 14, +0.05 | +0.40 | 0.57 |
| add, layer 10, +0.1 | +0.38 | 0.64 |
| add, layer 16, +0.1 (the losing cell) | +0.43 | 0.50 |
| remove, layer 16, -0.1 | -0.03 | 0.50 |
| remove, layer 10, -0.1 | -0.43 | 0.36 |
| remove, layer 16, -0.1, prompt only | -0.74 | 0.14 |
| remove, layer 16, -0.1, prompt + response | -0.24 | 0.36 |
| ablate E, layers 8 to 16, max-effort prompt | +0.47 | 0.57 |
| ablate rand0, all layers, max-effort prompt | +0.60 | 0.64 |
| rand0, layer 16, -0.1 | -0.04 | 0.43 |

Feature by feature (standardised paired deltas; paper's exhortation column first):

| feature | paper exhortation | add L6 +0.1 | remove L16 -0.1 | ablate E L8-16 |
| --- | --- | --- | --- | --- |
| words | +0.46 | +0.66 | +0.12 | -0.10 |
| sentences | +0.20 | +1.20 | +0.20 | +0.81 |
| words per sentence | +0.16 | -0.61 | -0.16 | -0.99 |
| rare-word rate | +0.20 | +0.52 | -1.18 | +0.61 |
| semicolons and colons | +0.23 | +0.63 | -0.70 | +1.20 |
| unique-word ratio | -0.19 | +0.22 | -1.06 | -0.09 |
| MATTR (lexical diversity) | -0.27 | -0.10 | -0.20 | -1.00 |
| positive-sentiment words | -0.14 | -0.30 | +0.49 | -0.63 |
| negative-sentiment words | -0.04 | +0.10 | -0.35 | +0.43 |
| Flesch-Kincaid grade | +0.04 | -0.80 | -0.28 | -1.55 |
| mean word length | -0.20 | -0.32 | -0.03 | -1.37 |

What the features say:

- Our pipeline reproduces the paper's exhortation signature on essays almost exactly (r = 0.96): longer, more
  sentences, more rare words and semicolons, fewer positive-sentiment words, slightly less lexical diversity.
- **Adding the vector at the early layers moves the same features the same way** on length, sentences, rare
  words, semicolons, sentiment and diversity (r = 0.4 to 0.5). It differs on two: steered sentences get shorter
  and simpler (Flesch-Kincaid grade -0.5 to -0.8) where the real exhortation leaves them unchanged. The vector
  gives "more and denser", the prompt gives "more and the same style".
- **Removing the vector is not the mirror image of the exhortation.** It leaves length alone and flattens
  vocabulary: rare words -1.2 SD, semicolons -0.7, unique-word ratio -1.1, more positive-sentiment words. The
  correlation with the paper signature is near zero at layer 16 and negative at layer 10 and for the prompt-only
  mode. This is the blandness seen in the reading.
- **Local ablation under the exhortation prompt does not remove the exhortation's signature.** Rare words and
  semicolons go up, not down. What it does is break sentences into short, simple, repetitive ones (words per
  sentence -1.0 SD, grade -1.6, MATTR -1.0, word length -1.4). The exhortation prompt's push for "more" survives;
  the writing quality that normally comes with it does not.
- The losing add-cell at layer 16 (+0.1) has the same feature direction as the winning early-layer cells but
  twice the size on semicolons (+1.1), word length (-1.3) and grade (-1.2): the same push, overdone, plus 17%
  glitchy essays.

## 4. What this changes in the reading of week 6

- The removal effect is a loss of specificity and vocabulary with intact fluency, not damage. That answers the
  meeting's "coherence high, score low" question for steering. For ablation the answer is different: style
  inflation plus sentence-level degradation with occasional broken tokens.
- The early-layer addition reproduces most of the exhortation's text signature, including length, and judges
  reward it. The planned length control (week-7 plan) stays necessary, since the real exhortation also adds length.
- The week-7 necessity test (ablate at layers 8 to 16, judge against the neutral prompt) should be read with the
  feature table in hand: ablation under the exhortation prompt yields a text that is still "more" but worse
  written, so a loss against neutral can come from the writing damage rather than from losing the exhortation.
