# Week 7 report: what the steered texts look like, coherence, paper metrics, random controls, transfer, role cues, necessity

Date: 2026-10-30. Covers all eight items of `week7_plan.txt` (from the meeting note `steering_extension/2810_meeting_notes.md`).
Sections 1 to 3 use the week-6 outputs; sections 4 to 7 use the new GPU batch. Tables in `results/2026-10-30_w7/`.

## 0. How to read every table in this report

**Every number is a comparison with an unsteered text.** The design is pairwise. For each topic and repeat the
model writes one essay with the intervention (steering or ablation) and one without, from the same prompt. The
paper's three judges (claude-haiku-4.5, gemini-3.1-flash-lite-preview, gpt-5-mini) see the two essays side by
side, in both orders, and pick the better one. A judge whose two orders disagree counts as a tie; the panel
majority decides; panel ties are dropped. The win rate is the share of resolved pairs in which the judges picked
the intervened essay. There is no absolute quality score. A win rate of 0.50 means the intervention made no
difference to the judges; 0.88 means the intervened essay won 88% of the pairs against its own unsteered twin.

Each table names the prompt both essays were written from, and what the opponent essay is. Columns:

- W / L / T: pairs the intervened essay won, lost, tied (ties excluded from the win rate). 60 pairs per cell
  (30 topics x 2 repeats) unless stated.
- p: two-sided exact binomial test of the win rate against 0.5.
- words: mean length of the intervened essay / of the opponent essay.
- coherence: mean 0 to 100 score from a separate single judge (readable, on-topic text, independent of
  quality), intervened essay / opponent essay. Unsteered essays score 87 to 89.

Two kinds of reference rows appear in the tables. "Unsteered vs unsteered" pairs two unsteered essays from the
same prompt; it should land near 0.50 and shows how far a 60-pair cell can wander by chance. "Random direction"
rows apply the same dose with a random direction of the same size instead of the effort direction; they show
how much of an effect comes from perturbing the model at all.

Vocabulary. The vector is the effort direction: mean hidden state over the model's own answer tokens under the
max-effort prompt minus the same under the neutral prompt, built from 300 responses per side (v4, grant and
postmortem prompts). Steering adds the vector at one layer's output while the model writes; dose r is the size of
the added vector as a fraction of the hidden state's typical size at that layer; r > 0 adds the direction, r < 0
removes it. Ablation projects the direction out of the hidden state at the listed layers, at every token. The
model is Qwen3.5-9B (32 layers). Prompts are the paper's: the framed-neutral essay prompt (no instruction about
effort), the max-effort prompt (the neutral prompt plus the exhortation), the world-class and skilled role-cue
prompts.

Cost of the new batch: 2,700 pairs, 5,400 generations and 600 extraction responses (1 h 20 min of one A100 at
$0.65/h), 16,200 judge votes and 3,000 coherence scores (about $25 to 30). Generation ran without the hub kernels
because `kernels-community/fla` no longer imports under transformers main; the torch fallback is about 25% slower.

## 1. Qualitative study: what the texts look like (plan item 1)

### 1.1 Ablation at layers 8 to 16 under the max-effort prompt

Week-6 cell: max-effort prompt, direction removed at layers 8 to 16, against the untouched max-effort essay from
the same topic. Result 3 / 17 (0.15, p = 0.003), coherence 82.2 against 87.7, 63% against 83% of essays at or
above 80. I read the 17 losing pairs side by side. Four things change.

The register goes purple. Ablated essays pile up metaphors and slogans where the twin argues plainly:

> "Second, these funds are the CD4 count of our democracy: a measure of its immune strength against division."
> (ablated, coherence 72; its twin opens "In an era dominated by 24-hour global cycles ... it is local news outlets
> that hold the keys to neighborhood safety, municipal accountability, and civic engagement", coherence 92)

> "Demand age verification not as a restriction, but as an act of supreme compassion. Let us be the generation
> that remembers what it means to be safe in a world burning with data." (ablated, coherence 62)

Invented specifics appear. Ablated essays reach for numbers and anecdotes that do not exist: "a turnout of
ninety-eight percent", "When the streets of Canberra hum with 12 million voices", "a 15% surge in local business
sales along those corridors". The twins stay general or hedge.

Broken tokens appear inside fluent text: "drowned out by theregarul routine", "ensuring that the沉默 is the
exception", "Contrast this withparallel it in a town". 13% of ablated essays contain a non-Latin character or a
fused word of 20 or more letters, against 5% of untouched max-effort essays (table 1.3).

Form shifts. Ablated essays carry a bold title more often (0.73 against 0.42 per essay) and split the same length
into more, shorter sentences (21.3 against 19.0 sentences at 408 against 412 words).

Why coherence stays at 82 while the judges pick the twin. The coherence judge scores readable, on-topic,
non-repetitive text, and these essays are readable and on topic. The quality judges see overwrought style,
fabricated detail and the occasional broken word, next to a twin that is sober and clean. The coherence scores of
the 60 ablated essays were 45 (one), 62 (one), 72 (fourteen), 78 (seven), 82 (fifteen), 92 (twenty-two). Only the
45 and the 62 read as damaged text. The rest read as a worse writer. In the pair quoted first above, both essays
are fluent (72 and 92) and the judges chose the twin 3 to 0.

### 1.2 The striking steering cells

Neutral essay prompt, steered essay against the unsteered essay from the same topic. Three pairs read per cell.

Remove at layer 16, r = -0.1 (5 / 37, coherence 89.3 against 88.7, words 398 against 393). The steered essays are
textbook essays. They run "First, ... Secondly, ... Thirdly," restate the thesis in the conclusion, drop the title,
name fewer concrete cases and numbers, and lean on stock phrases ("plays a pivotal role", "fostering informed
consumer choices"). A steered opening: "In an era defined by rapid industrialization and increasing environmental
awareness, the ethical responsibility of corporations extends far beyond profit generation." Its twin: "In an era
defined by climate urgency, the responsibility to combat environmental degradation extends beyond government
regulation and individual consumer choices; it fundamentally rests upon corporate transparency." Both score 92 on
coherence; the judges took the twin 3 to 0. The paper features agree (section 3): rare-word rate, semicolons and
unique-word ratio fall by about one standard deviation and positive-sentiment words rise. Removal makes the essay
blander, not broken.

Remove at layer 6, r = -0.2 (0 / 54, coherence 83.1 against 88.7, words 360 against 393). Same blandness, now
shorter, and 30% of essays under 80 on coherence. Part damage, part the same drift.

Add at layer 6, r = +0.1 (22 / 3, coherence 89.2 against 88.7, words 415 against 393). The steered essays give
more specifics per point. On gig workers: "They face wage stagnation, no minimum wage guarantees, and no sick
leave, all while bearing the crushing weight of business expenses like insurance, taxes, and vehicle maintenance.
When an individual is forced to fund their own banking infrastructure and health coverage solely to access a
job, they are not running a business; they are working a job." The twin for the same topic states the claim in
one sentence and moves on. Steered essays use more sentences of shorter length (20.0 against 21.5 words per
sentence), more semicolons and rare words, fewer positive-sentiment words. Coherence is unchanged and the glitch
rate equals the baseline (8%). Section 3 shows this is the direction the real exhortation moves the same features.

Remove at layer 16, r = -0.1, prompt tokens only (8 / 20, coherence 88.8 against 89.0, words 389 against 399).
The same blandness as the response-only removal, weaker, with fewer bold titles (0.17 against 0.42 per essay).
Removing on prompt and response tokens together (1 / 47, coherence 88.5 against 89.0) reads like the
response-only removal one step further.

### 1.3 Glitch rate per condition

Share of essays containing a non-Latin character or a fused word of 20 or more letters
(`glitch_rate_w6.csv`).

| condition (neutral prompt unless stated) | glitch rate |
| --- | --- |
| unsteered (10 cells) | 0.08 |
| max-effort prompt, untouched | 0.05 to 0.11 |
| remove at layer 16, r = -0.1 (response / prompt / both) | 0.03 / 0.05 / 0.05 |
| remove at layer 6, r = -0.2 | 0.00 |
| add at layer 6, r = +0.1 | 0.08 |
| add at layer 16, r = +0.1 | 0.17 |
| add at layer 18, r = +0.1 (highest steering cell) | 0.22 |
| max-effort prompt, direction ablated at layers 8 to 16 | 0.13 |
| max-effort prompt, random direction ablated at all 32 layers | 0.08 |
| max-effort prompt, direction ablated at all 32 layers | 0.78 |

Removing the direction adds no glitches. Adding it at mid layers and high doses does (0.17 to 0.22 at layers 12
to 20 for r at or above +0.075), which is where the positive side of the week-6 sweep turns down.

## 2. Coherence under every form of steering tried so far (plan item 2)

All 175 condition means are in `coherence_all_conditions.csv`; the sweep heatmap is
`../2026-10-27_w6_sweep/coherence_heatmap.png`. Unsteered essays score 86.9 to 89.8 across runs (mean 88.3), with
80 to 90% at or above 80.

| steering form (neutral prompt unless stated) | cells | mean coherence | share at or above 80 | lowest cell | unsteered in same runs |
| --- | --- | --- | --- | --- | --- |
| remove, r = -0.05 and -0.1, all layers | 24 | 89.2 | 0.88 | 87.3 | 88.3 |
| remove, r = -0.2, all layers | 12 | 86.9 | 0.82 | 82.9 | 88.3 |
| add, r = +0.025 and +0.05, all layers | 24 | 87.2 | 0.80 | 84.6 | 88.3 |
| add, r = +0.075 and +0.1, layers 6 to 14 | 10 | 86.1 | 0.75 | 84.2 | 88.3 |
| add, r = +0.075 and +0.1, layers 16 to 28 | 14 | 84.7 | 0.71 | 80.6 | 88.3 |
| random directions, layer 16 (week 6) | 4 | 87.1 | 0.81 | 85.1 | 88.3 |
| random directions, layers 6 to 20 (week 7) | 24 | 88.2 | 0.85 | 86.7 | 89.0 |
| several layers at once | 5 | 86.8 | 0.80 | 85.3 | 87.5 |
| prompt-only and prompt plus response | 4 | 87.5 | 0.82 | 84.9 | 89.0 |
| other readouts | 14 | 87.8 | 0.83 | 86.0 | 88.4 |
| max-effort prompt, direction ablated at layers 8 to 16 | 1 | 82.2 | 0.63 | | 87.7 |
| role prompts, direction ablated at layers 8 to 16 | 2 | 80.6 | 0.55 | 79.6 | 88.9 |
| max-effort prompt, direction ablated at all 32 layers | 1 | 2.4 | 0.00 | | 86.3 |

Where coherence drops. Adding at r at or above +0.075, more so from layer 16 on (80.6 at layer 16, 81.3 at layer
18); removing at r = -0.2 (82.9 to 86 at layers 6 to 12); ablation of the direction at layers 8 to 16 under any
prompt (80 to 82); ablation at all 32 layers (2.4, gibberish).

Where it holds. Removing at -0.05 and -0.1 at every layer; adding at +0.025 and +0.05; random directions at any
layer; several layers at once; both position modes; every other readout. All within 2 points of unsteered.

Where it rises. Removing at r = -0.1 gives the highest coherence of any form, 89.4 mean over 12 layers, with the
top cells at 90.3 (layers 18 and 22, 93% of essays at or above 80) against 87.5 to 88.7 for unsteered essays in the
same run. The difference is 1 to 2 points, inside the spread between unsteered cells (86.9 to 89.8), so at most a
small effect. It fits section 1: removal produces plainer, safer, more conventional text, which the coherence
judge likes and the quality judges do not.

Coherence and win rate move together only at the extremes. Removal at -0.1 loses with coherence intact.
Addition at layer 6 wins with coherence intact. Addition at layer 16 and above at high dose loses and loses
coherence. Ablation loses with a 6 to 9 point coherence cost.

## 3. The paper's text features on our outputs (plan item 3)

The paper reports, besides the judge win rate, a set of text features and their direction under each prompt
contrast (its feature tables). I computed the same features with the paper's own code (`text_features.py`
calls the paper's `scalar_features`) on every week-6 and week-7 run. For each cell the per-pair difference
(intervened minus unsteered, same topic and repeat) is standardised by its standard deviation, as in the paper.
The reference is the paper's own direct-exhortation feature deltas for Qwen3.5-9B essays
(`data/processed/final_text_analysis_pair_deltas.csv.gz`). The paper's utility measures (its other metric
family) need new model calls and the Utility Engineering fits and are not computed here.

Correlation across the 14 paper features between a cell's standardised deltas and the paper's exhortation
deltas, and the share of features with the same sign (`feature_deltas_key_cells_w6.csv`):

| cell | r with the paper's exhortation signature | same sign |
| --- | --- | --- |
| max-effort prompt vs neutral prompt, our pipeline, no steering (60 pairs) | +0.96 | 0.93 |
| add at layer 6, +0.1 | +0.51 | 0.57 |
| add at layer 14, +0.05 | +0.40 | 0.57 |
| add at layer 10, +0.1 | +0.38 | 0.64 |
| add at layer 16, +0.1 (the losing cell) | +0.43 | 0.50 |
| remove at layer 16, -0.1 | -0.03 | 0.50 |
| remove at layer 10, -0.1 | -0.43 | 0.36 |
| remove at layer 16, -0.1, prompt tokens only | -0.74 | 0.14 |
| remove at layer 16, -0.1, prompt and response | -0.24 | 0.36 |
| max-effort prompt, direction ablated at layers 8 to 16, vs untouched max-effort | +0.47 | 0.57 |
| max-effort prompt, random direction ablated at all layers, vs untouched max-effort | +0.60 | 0.64 |
| random direction at layer 16, -0.1 | -0.04 | 0.43 |
| skilled prompt, add at layer 6, +0.1 (week 7) | +0.59 | 0.71 |
| world-class prompt, add at layer 6, +0.1 (week 7) | +0.49 | 0.57 |
| world-class prompt vs skilled prompt, no steering (week 7) | +0.38 | 0.57 |
| max-effort prompt, direction ablated at layers 8 to 16, vs neutral essay (week 7) | +0.60 | 0.64 |
| max-effort prompt, random direction ablated at layers 8 to 16, vs neutral essay (week 7) | +0.90 | 0.86 |

Feature by feature, standardised paired deltas, the paper's exhortation column first:

| feature | paper exhortation | our exhortation prompt | add layer 6 +0.1 | remove layer 16 -0.1 | ablate at 8 to 16 under max-effort |
| --- | --- | --- | --- | --- | --- |
| words | +0.46 | +0.54 | +0.66 | +0.12 | -0.10 |
| sentences | +0.20 | +0.26 | +1.20 | +0.20 | +0.81 |
| words per sentence | +0.16 | +0.11 | -0.61 | -0.16 | -0.99 |
| rare-word rate | +0.20 | +0.30 | +0.52 | -1.18 | +0.61 |
| semicolons and colons | +0.23 | +0.42 | +0.63 | -0.70 | +1.20 |
| unique-word ratio | -0.19 | -0.30 | +0.22 | -1.06 | -0.09 |
| MATTR (lexical diversity) | -0.27 | -0.32 | -0.10 | -0.20 | -1.00 |
| positive-sentiment words | -0.14 | -0.21 | -0.30 | +0.49 | -0.63 |
| negative-sentiment words | -0.04 | +0.01 | +0.10 | -0.35 | +0.43 |
| Flesch-Kincaid grade | +0.04 | 0.00 | -0.80 | -0.28 | -1.55 |
| mean word length | -0.20 | -0.11 | -0.32 | -0.03 | -1.37 |

What the features say.

Our pipeline reproduces the paper's exhortation signature on essays (r = 0.96): longer, more sentences, more rare
words and semicolons, fewer positive-sentiment words, a little less lexical diversity.

Adding the vector at the early layers moves the same features the same way on length, sentences, rare words,
semicolons, sentiment and diversity (r = 0.4 to 0.6). It differs on two. Steered sentences get shorter and simpler
(Flesch-Kincaid grade -0.5 to -0.8) where the real exhortation leaves them unchanged. The vector gives "more and
denser"; the prompt gives "more, in the same style".

Removing the vector is not the mirror image of the exhortation. It leaves length alone and flattens vocabulary
(rare words -1.2 SD, semicolons -0.7, unique-word ratio -1.1, positive-sentiment words +0.5). The correlation with
the paper's signature is near zero at layer 16 and negative at layer 10 and in prompt-only mode. This is the
blandness of section 1.2.

Ablating the direction under the max-effort prompt does not remove the exhortation's signature. Rare words and
semicolons go up, not down. It breaks sentences into short, simple, repetitive ones (words per sentence -1.0 SD,
grade -1.6, MATTR -1.0, word length -1.4). The prompt's push for "more" survives; the writing quality that
normally comes with it does not. This is the purple, sloppy text of section 1.1.

The losing add-cell at layer 16 (+0.1) has the same feature direction as the winning early-layer cells but twice
the size on semicolons (+1.1), word length (-1.3) and grade (-1.2), plus 17% glitchy essays. The same push,
overdone.

## 4. Random controls on the sweep grid (plan item 5)

Neutral essay prompt. Each row compares an essay steered with a random direction of the same size as the effort
vector against the unsteered essay from the same topic. Two random directions (rand0, rand1), layers 6, 10, 14,
20, doses -0.1, +0.05, +0.1, 1,440 pairs (`w7_random_dose_summary.csv`). The unsteered-vs-unsteered row is from
the same run.

| steered with | layer | r | W / L / T | win rate | p | words steered / unsteered | coherence steered / unsteered |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nothing (unsteered vs unsteered) | | | 5 / 15 / 40 | 0.25 | 0.04 | 397 / 394 | 86.7 / 89.0 |
| rand0 | 6 | -0.1 | 10 / 10 / 40 | 0.50 | 1.0 | 397 / 394 | 88.5 / 89.0 |
| rand1 | 6 | -0.1 | 2 / 18 / 40 | 0.10 | 0.0004 | 384 / 394 | 89.2 / 89.0 |
| rand0 | 6 | +0.05 | 3 / 12 / 45 | 0.20 | 0.04 | 389 / 394 | 88.2 / 89.0 |
| rand1 | 6 | +0.05 | 7 / 10 / 43 | 0.41 | 0.63 | 405 / 394 | 87.8 / 89.0 |
| rand0 | 6 | +0.1 | 7 / 15 / 38 | 0.32 | 0.13 | 396 / 394 | 88.1 / 89.0 |
| rand1 | 6 | +0.1 | 9 / 10 / 41 | 0.47 | 1.0 | 403 / 394 | 87.7 / 89.0 |
| rand0 | 10 | -0.1 | 3 / 15 / 42 | 0.17 | 0.008 | 382 / 394 | 89.0 / 89.0 |
| rand1 | 10 | -0.1 | 10 / 12 / 38 | 0.45 | 0.83 | 409 / 394 | 88.2 / 89.0 |
| rand0 | 10 | +0.05 | 9 / 9 / 42 | 0.50 | 1.0 | 408 / 394 | 86.7 / 89.0 |
| rand1 | 10 | +0.05 | 7 / 7 / 46 | 0.50 | 1.0 | 392 / 394 | 88.5 / 89.0 |
| rand0 | 10 | +0.1 | 5 / 9 / 46 | 0.36 | 0.42 | 406 / 394 | 88.3 / 89.0 |
| rand1 | 10 | +0.1 | 6 / 13 / 41 | 0.32 | 0.17 | 387 / 394 | 88.0 / 89.0 |
| rand0 | 14 | -0.1 | 4 / 6 / 50 | 0.40 | 0.75 | 388 / 394 | 88.1 / 89.0 |
| rand1 | 14 | -0.1 | 12 / 8 / 40 | 0.60 | 0.50 | 399 / 394 | 88.8 / 89.0 |
| rand0 | 14 | +0.05 | 5 / 12 / 43 | 0.29 | 0.14 | 394 / 394 | 88.5 / 89.0 |
| rand1 | 14 | +0.05 | 4 / 14 / 42 | 0.22 | 0.03 | 394 / 394 | 87.5 / 89.0 |
| rand0 | 14 | +0.1 | 10 / 9 / 41 | 0.53 | 1.0 | 404 / 394 | 89.1 / 89.0 |
| rand1 | 14 | +0.1 | 8 / 11 / 41 | 0.42 | 0.65 | 388 / 394 | 88.0 / 89.0 |
| rand0 | 20 | -0.1 | 3 / 14 / 43 | 0.18 | 0.01 | 398 / 394 | 88.0 / 89.0 |
| rand1 | 20 | -0.1 | 5 / 9 / 46 | 0.36 | 0.42 | 397 / 394 | 88.7 / 89.0 |
| rand0 | 20 | +0.05 | 1 / 12 / 47 | 0.08 | 0.003 | 392 / 394 | 87.9 / 89.0 |
| rand1 | 20 | +0.05 | 5 / 10 / 45 | 0.33 | 0.30 | 397 / 394 | 89.1 / 89.0 |
| rand0 | 20 | +0.1 | 6 / 8 / 46 | 0.43 | 0.79 | 399 / 394 | 88.4 / 89.0 |
| rand1 | 20 | +0.1 | 7 / 12 / 41 | 0.37 | 0.36 | 399 / 394 | 87.9 / 89.0 |
| all 24 random cells pooled | | | 148 / 265 | 0.36 | | 396 / 394 | 88.2 / 89.0 |

Random directions are not neutral at these doses. Pooled, the random-steered essay wins 0.36; by dose 0.35 at
-0.1, 0.32 at +0.05, 0.40 at +0.1. Coherence and length are unchanged, so the judges see a small, real loss of
quality from any perturbation of this size, not broken text. Week 6's four random cells at layer 16 pointed the
same way (37 / 43, 0.46).

The unsteered-vs-unsteered cell in this run came out 5 / 15 (0.25, p = 0.04). The seven such cells across all runs
are 11/10, 10/7, 11/13, 10/7, 8/10, 5/15 and 16/7, pooled 71 / 69. This one is the low end of ordinary scatter at
20 resolved pairs, and the next run's null cell (section 5) came out 16 / 7 on the other side.

The effort vector against the pooled random cells at the same layer and dose (both against unsteered essays from
the same prompts; Fisher exact test between the two W / L counts):

| layer | r | effort vector (week 6) | random directions pooled | p | coherence, effort / random / unsteered |
| --- | --- | --- | --- | --- | --- |
| 6 | -0.1 | 0.19 (7/30) | 0.30 (12/28) | 0.30 | 88.7 / 88.9 / 88.7 |
| 6 | +0.05 | 0.62 (15/9) | 0.31 (10/22) | 0.03 | 88.0 / 88.0 / 88.7 |
| 6 | +0.1 | 0.88 (22/3) | 0.39 (16/25) | 0.0001 | 89.2 / 87.9 / 88.7 |
| 10 | -0.1 | 0.06 (2/29) | 0.33 (13/27) | 0.009 | 88.8 / 88.6 / 88.7 |
| 10 | +0.05 | 0.67 (12/6) | 0.50 (16/16) | 0.37 | 88.0 / 87.6 / 88.7 |
| 10 | +0.1 | 0.82 (18/4) | 0.33 (11/22) | 0.0008 | 86.1 / 88.2 / 88.7 |
| 14 | -0.1 | 0.07 (3/37) | 0.53 (16/14) | 0.00003 | 90.0 / 88.5 / 88.7 |
| 14 | +0.05 | 0.81 (17/4) | 0.26 (9/26) | 0.0001 | 88.3 / 88.0 / 88.7 |
| 14 | +0.1 | 0.52 (13/12) | 0.47 (18/20) | 0.8 | 84.2 / 88.6 / 88.7 |
| 20 | -0.1 | 0.22 (7/25) | 0.26 (8/23) | 0.77 | 88.8 / 88.4 / 88.7 |
| 20 | +0.05 | 0.65 (13/7) | 0.21 (6/22) | 0.003 | 86.6 / 88.5 / 88.7 |
| 20 | +0.1 | 0.33 (10/20) | 0.39 (13/20) | 0.79 | 83.9 / 88.2 / 88.7 |

The positive effect is direction-specific. Every early-layer winning cell (layer 6 at +0.05 and +0.1, layer 10
at +0.1, layer 14 at +0.05, layer 20 at +0.05) beats its random control, with random at 0.2 to 0.4 in the same
cells.

The negative effect is direction-specific at layers 10 and 14 (0.06 and 0.07 against 0.33 and 0.53). At layers 6
and 20 the random controls lose almost as much as the effort vector (0.30 and 0.26 against 0.19 and 0.22), so
removal at -0.1 there is not distinguishable from generic damage at 60 pairs.

Week 6's "removal hurts at every layer" has to be read against a random floor near 0.35, not 0.5. The
effort-specific part of the removal effect is clearest at layers 10 to 16.

## 5. Cross-validation: a vector built from essays, tested on grant (plan item 6)

The effort direction was rebuilt from essay responses only (30 essay topics x 10 repeats, 300 per side, same
recipe; `outputs/steering/vectors/qwen3.5-9b_essay_v1/`). Its cosine with the v4 vector (built from grant and
postmortem) is 0.60 to 0.71 at every layer and 0.00 with the random directions; its split-half reliability is as
poor as v4's (0.24 at layer 16). It was then injected while the model wrote grant abstracts from the paper's
grant prompt (30 items x 2 repeats, max_tokens 1400). Each row compares the steered abstract with the unsteered
abstract from the same item (`w7_crossval_grant_dose_summary.csv`).

| steered with | layer | r | W / L / T | win rate | p | words steered / unsteered | coherence steered / unsteered |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nothing (unsteered vs unsteered) | | | 16 / 7 / 37 | 0.70 | 0.09 | 659 / 662 | 88.6 / 88.2 |
| essay-built effort vector | 6 | -0.1 | 1 / 40 / 19 | 0.02 | < 0.0001 | 623 / 662 | 88.8 / 88.2 |
| essay-built effort vector | 6 | +0.05 | 15 / 7 / 38 | 0.68 | 0.13 | 664 / 662 | 86.7 / 88.2 |
| essay-built effort vector | 6 | +0.1 | 13 / 11 / 36 | 0.54 | 0.84 | 676 / 662 | 84.3 / 88.2 |
| essay-built effort vector | 10 | -0.1 | 2 / 46 / 12 | 0.04 | < 0.0001 | 621 / 662 | 88.9 / 88.2 |
| essay-built effort vector | 10 | +0.05 | 14 / 7 / 39 | 0.67 | 0.19 | 667 / 662 | 84.0 / 88.2 |
| essay-built effort vector | 10 | +0.1 | 9 / 18 / 33 | 0.33 | 0.12 | 704 / 662 | 82.3 / 88.2 |
| essay-built effort vector | 16 | -0.1 | 0 / 49 / 11 | 0.00 | < 0.0001 | 639 / 662 | 87.3 / 88.2 |
| essay-built effort vector | 16 | +0.05 | 13 / 4 / 43 | 0.76 | 0.049 | 682 / 662 | 85.8 / 88.2 |
| essay-built effort vector | 16 | +0.1 | 5 / 25 / 30 | 0.17 | 0.0003 | 683 / 662 | 78.0 / 88.2 |
| rand0 | 10 | -0.1 | 8 / 12 / 40 | 0.40 | 0.50 | 662 / 662 | 88.6 / 88.2 |
| rand0 | 10 | +0.05 | 8 / 8 / 44 | 0.50 | 1.0 | 670 / 662 | 88.3 / 88.2 |
| rand0 | 10 | +0.1 | 10 / 7 / 43 | 0.59 | 0.63 | 665 / 662 | 86.6 / 88.2 |

The direction transfers across tasks. A vector that never saw a grant abstract steers grant abstracts. Removal at
-0.1 loses 1/40, 2/46 and 0/49 with coherence intact (the random direction at the same layer and dose: 8/12,
Fisher p = 0.0005). Addition at +0.05 wins 0.67 to 0.76 at all three layers (random 0.50). The shape matches the
essay sweep: +0.1 is already too much at layers 10 and 16 (0.33 and 0.17, coherence 82 and 78). Grant abstracts
are longer than essays (660 words); removal shortens them by 25 to 40 words and addition at +0.1 lengthens them
by 20 to 40, as on essays.

## 6. Role cues: does the direction act without the exhortation? (plan item 7)

The paper's framed role-cue prompts, world-class ("You are a world-class essayist") and skilled ("You are a
skilled essay writer"), with no exhortation. The first four rows compare the intervened essay with the untouched
essay written from the same role prompt and topic. The fifth row compares an untouched world-class essay with an
untouched skilled essay from the same topic; it is the paper's own role contrast, reproduced as a reference
(`w7_role_cell_summary.csv`).

| essay written from | intervention | opponent | W / L / T | win rate | p | words int. / opp. | coherence int. / opp. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| world-class prompt | direction ablated at layers 8 to 16 | untouched world-class essay | 3 / 31 / 26 | 0.09 | < 0.0001 | 390 / 404 | 79.6 / 88.8 |
| skilled prompt | direction ablated at layers 8 to 16 | untouched skilled essay | 6 / 27 / 27 | 0.18 | 0.0003 | 384 / 401 | 81.5 / 89.0 |
| world-class prompt | direction added at layer 6, +0.1 | untouched world-class essay | 11 / 13 / 36 | 0.46 | 0.84 | 414 / 404 | 84.5 / 88.8 |
| skilled prompt | direction added at layer 6, +0.1 | untouched skilled essay | 17 / 5 / 38 | 0.77 | 0.02 | 413 / 401 | 86.9 / 89.0 |
| world-class prompt | none | untouched skilled essay | 8 / 6 / 46 | 0.57 | 0.79 | 404 / 401 | 88.8 / 89.0 |
| max-effort prompt (week 6) | direction ablated at layers 8 to 16 | untouched max-effort essay | 3 / 17 / 40 | 0.15 | 0.003 | 408 / 412 | 82.2 / 87.7 |
| neutral prompt (week 6) | direction added at layer 6, +0.1 | untouched neutral essay | 22 / 3 / 35 | 0.88 | < 0.0001 | 415 / 393 | 89.2 / 88.7 |

Ablation hurts under both role prompts, as much as under the exhortation prompt. The model uses this direction
whenever it writes a competent essay, not only when told to try hard. The coherence cost is the same 7 to 9
points as before.

Adding the direction helps under the weak role cue and not under the strong one. Under "skilled" it reproduces
the neutral-prompt win (0.77 against 0.88). Under "world-class" it does nothing (0.46). One reading: the
world-class cue already pushes the model along this direction, and adding more overshoots. The text features
fit. The world-class-vs-skilled contrast itself correlates 0.38 with the exhortation's feature signature, and
adding the direction under world-class drives semicolons and rare words further than under skilled (+0.87 and
+0.82 SD against +0.35 and +0.44). This rests on one dose per prompt; a dose curve under the world-class prompt
would settle it.

The paper's role contrast reproduces weakly here (8 / 6, 0.57; the paper reports 0.57, our week-4 Phase 0 had
0.55).

## 7. Clean necessity test (plan item 8)

The model gets the max-effort prompt and the direction is removed at layers 8 to 16 while it writes. The
opponent is an essay written from the neutral prompt (no exhortation) with nothing removed. The question is
whether the exhortation still helps once the direction is gone. The last row, from week 6, is the reference:
the untouched max-effort essay beats the neutral essay (`w7_necessity_cell_summary.csv`).

| essay written from | removed while writing | opponent | W / L / T | win rate | p | words int. / opp. | coherence int. / opp. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| max-effort prompt | effort direction, layers 8 to 16 | untouched neutral essay | 7 / 19 / 34 | 0.27 | 0.03 | 401 / 396 | 82.0 / 87.3 |
| max-effort prompt | random direction, layers 8 to 16 | untouched neutral essay | 12 / 8 / 40 | 0.60 | 0.50 | 419 / 398 | 89.1 / 88.1 |
| max-effort prompt (week 6) | nothing | untouched neutral essay | 14 / 7 / 39 | 0.67 | 0.19 | 410 / 395 | 86.1 / 89.1 |

With the direction removed, the exhortation no longer helps; the essay falls below the neutral one. With a random
direction removed instead, the exhortation keeps its advantage (0.60 against 0.67 untouched). The random
ablation shows the ablation operation itself is harmless; the loss is specific to this direction.

Text features agree. Under random ablation the exhortation's feature signature is fully present (r = 0.90 with the
paper's). Under ablation of the effort direction the "more rare words and semicolons" part survives (+0.84 and
+1.68 SD) but sentences get short and simple (words per sentence -0.70, grade -1.54), as in section 3.

Caveat. The ablated essays lose 5 coherence points (82 against 87), so part of the 0.27 is writing damage rather
than a lost exhortation effect. An ablation that keeps coherence is the next step for this cell.

## 8. What changes in the hypotheses

H1, adding the direction reproduces the exhortation's effect: supported, and now direction-specific. The
early-layer wins beat matched random controls (p = 0.03 to 0.0001), the direction built from essays transfers to
grant abstracts (0.67 to 0.76 at +0.05), and it works under the weak role cue. It adds nothing under the strong
role cue. The text features it moves are the exhortation's, except that it also shortens and simplifies
sentences.

H2, removing the direction cancels the effect: supported, with a correction. Random perturbation alone costs
about 15 points of win rate. The effort-specific removal effect is clear at layers 10 to 16 and on grant at all
three layers tested, not at layers 6 and 20. Under the exhortation prompt, ablating the direction removes the
exhortation's advantage (0.27 against neutral) while a random ablation does not (0.60). Removal by steering
makes text bland with fluency intact; removal by ablation makes it overwrought and sloppy with a coherence cost.

H3, random directions do nothing: not quite. Random directions at |r| = 0.05 to 0.1 lose 0.32 to 0.40 of pairs with
coherence intact. The right null for a steering cell is the matched random cell, not 0.5. Week 6's conclusions
survive this re-reading where it matters (the positive early-layer cells, removal at layers 10 to 16).

## 9. Caveats and next steps

- 60 pairs per cell with 30 to 45 ties, so 15 to 40 resolved pairs; the null cells scatter from 0.25 to 0.70. No
  single cell between about 5/15 and 15/5 should be read on its own.
- Ablation costs 5 to 9 coherence points under every prompt. An ablation that keeps coherence (fewer layers,
  response tokens only, or orthogonalised to the mean activation) would make the necessity result cleaner.
- The role-cue result rests on one dose; run a short dose curve under the world-class prompt.
- The positive effect lengthens essays by about 20 words, as the real exhortation does (+15). A length control
  is still not done.
- Cross-validation ran one way (essay-built vector on grant); the reverse is the week-6 sweep itself.
- Essay and grant tasks, the 9B model only.
