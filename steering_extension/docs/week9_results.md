# Week 9 results (2026-11-17/18): where the coherence loss comes from, what the coherence judge objects to, sandbagging in Qwen and DeepSeek

Plan: `week9_plan.txt` (repo root), from `steering_extension/0711_meeting_notes.txt`. Sections 1, 2, 4 (Qwen) and 5 (DeepSeek) are done.

## 0. How to read the tables

Every number is a pairwise comparison. For each topic and repeat the model writes one essay with the intervention
(side a) and one without (side b), from the same prompt. The paper's three judges pick the better one in both orders.
A judge whose two orders disagree counts as a tie, and we drop the pairs the panel ties. W / L is the number of pairs
side a won and lost, win rate is W / (W + L), and 0.50 means no effect. Coherence is a separate 0 to 100 score that
claude-haiku-4.5 at temperature 0 gives each essay for being fluent, on topic and consistent, with instructions to
ignore quality. The effort vector E is the week-6 vector (max-effort minus neutral, response-token mean). The dose r is
a fraction of the layer's RMS residual norm, and r < 0 removes the direction.

Three terms used below. The "gap" of a pair is the coherence of the steered essay minus the coherence of its unsteered
partner. A pair is "damaged" if the gap is below -3, "as coherent" if it is within 3 points, and "more coherent" if it
is above +3. "Null" means the unsteered vs unsteered cells (300 pairs from five runs, 45 / 55).

Two properties of the data that every table depends on:

- The coherence judge uses few values. 3,221 of the 5,040 steered essays in the week-6 sweep score exactly 92, and
  almost all the others score 88, 85, 82, 78 or 72. A "damaged" pair is most often 88, 82, 78 or 72 against 92.
- All 84 cells of the week-6 sweep are compared against the same 60 unsteered essays. 16 of those 60 score below 92.
  Any steered essay paired with one of these 16 is likely to be "more coherent" and to win. Null pairs show this
  without steering: two unsteered essays differ by more than 3 points in 46% of pairs.

## 1. Where the coherence loss comes from (note item 1)

Essay task, neutral prompt, side a steered with E added at r +0.025 to +0.1 (week-6 sweep, layers 6 to 28, 2,880
pairs), side b the unsteered essay from the same topic and repeat. Random is a random direction added at +0.05 or +0.1
(layers 6, 10, 14, 20, 960 pairs). Each row is one part of a group. "share" is the part's share of the group's pairs.
The script is `local/week9_coherence.py`, and the full tables and figures are in
`outputs/steering/w9_analysis/item1_summary.md`.

| side a | part | pairs | share | W / L | win rate | coh a / b |
|---|---|---|---|---|---|---|
| effort added | damaged | 1,000 | 0.35 | 59 / 374 | 0.14 | 77.0 / 90.8 |
| effort added | as coherent | 1,332 | 0.46 | 214 / 88 | 0.71 | 91.4 / 91.4 |
| effort added | more coherent | 548 | 0.19 | 331 / 5 | 0.99 | 90.5 / 78.2 |
| random added | damaged | 210 | 0.22 | 2 / 98 | 0.02 | 77.0 / 90.5 |
| random added | as coherent | 571 | 0.59 | 66 / 69 | 0.49 | 91.4 / 91.4 |
| random added | more coherent | 179 | 0.19 | 31 / 6 | 0.84 | 90.6 / 79.5 |
| unsteered (null) | damaged | 65 | 0.22 | 1 / 35 | 0.03 | 77.2 / 91.1 |
| unsteered (null) | as coherent | 163 | 0.54 | 15 / 19 | 0.44 | 91.3 / 91.3 |
| unsteered (null) | more coherent | 72 | 0.24 | 29 / 1 | 0.97 | 90.8 / 78.7 |

- The wins and the coherence loss come from different essays. The damaged part holds 35% of the effort-added pairs,
  80% of the losses and 10% of the wins. The mean gap of -2.4 points is entirely the damaged part (-4.8 from damaged
  pairs, 0.0 from as-coherent pairs, +2.3 from more-coherent pairs).
- Adding E damages more essays than chance does. The damaged share is 0.35 against 0.22 for null and 0.22 for a
  random direction, an excess of about 13 points of pairs. So adding E gives a mixture. Most essays keep their
  coherence and some lose it.
- The steering effect is in the as-coherent part. There E wins 0.71 against 0.44 for null and 0.49 for random. The
  "more coherent" part wins 0.99, but null wins 0.97 there too, so those 331 wins (55% of all effort wins) say
  little about steering. They are the 16 weak partners.
- A higher dose buys more damage and no more clean wins. In layers 6 to 14 the damaged share rises from 0.28 at
  +0.025 to 0.37 at +0.1, while the share of pairs won at equal or better coherence stays at 0.21 to 0.25 (null
  0.15). In layers 16 to 28 the damaged share reaches 0.46 and the clean-win share is at the null level (0.15 to
  0.18).
- Layer 6 at +0.1 is the one cell with damage below null (0.17) and the highest clean-win share (0.33, 22 / 3). It is
  one cell of 60 pairs, found after looking, so it is a candidate and not a result.
- The damage is spread over topics. The five worst topics carry 29.5% of the essays below 80 (21% expected by
  chance), and the effort-added share is above the topic's own unsteered share in 26 of 30 topics. Topics that are
  low under E are also low unsteered (Spearman 0.48).

Removal (r -0.1 and -0.05, 1,440 pairs) is different. The split into parts is the null split (damaged 0.20, more
coherent 0.23), so removal does not change coherence. It loses at equal coherence, 33 / 313 (0.10) against 0.44 for
null and 0.41 for random removal.

So the "inverse relation" has two halves with different causes. Under addition a subset of essays is damaged and
loses while the rest win at equal coherence. Under removal coherence is untouched and the essays lose anyway.

A consequence for earlier weeks. Against the 44 partners that score 92 or more, the null win rate in this sweep is
0.22 (14 / 51), not 0.50, and the effort-added win rate is 0.37 (246 / 411). The sweep's cell win rates are raised by
the 16 weak partners (358 / 56 against them). Comparisons between effort, random and null cells are not affected,
because all use partners drawn the same way. The absolute level of a win rate against 0.50 is.

## 2. What the coherence judge objects to (note item 3)

The same judge model (claude-haiku-4.5, temperature 0, the same coherence definition) was shown the task and two
essays as A and B, without being told which was steered, and asked which would get the higher coherence score, by
how many points, why, and to quote up to three passages that cost the lower one its points. Every pair was judged in
both orders. A second model (gemini-2.5-flash, temperature 0) sorted the reasons into categories. 359 pairs, 718
judge calls and 359 coder calls, $2.06. The script is `local/coherence_pairwise.py`, the full tables are in
`outputs/steering/w9_analysis/item2_summary.md`, and all 59 cases of the first group are written out in
`stratum_a_cases.md`.

Groups of pairs, all essay task, side a steered, side b unsteered:

| group | pairs | mean coh a / b | both orders say side a is less coherent | the two orders disagree |
|---|---|---|---|---|
| a. effort added, side a won, damaged (all layers) | 59 | 80.9 / 90.5 | 28 | 30 |
| b. effort added, side a lost, damaged (layers 6 to 14) | 60 | 74.0 / 91.1 | 56 | 4 |
| c. effort added, side a won, as coherent (layers 6 to 14) | 60 | 91.6 / 91.6 | 3 | 51 |
| d. random direction added, damaged | 60 | 78.1 / 90.6 | 41 | 19 |
| e. unsteered vs unsteered | 60 | 85.5 / 88.8 | 15 | 38 |
| f. effort removed, r -0.1 (layers 6 to 14) | 60 | 87.2 / 87.7 | 10 | 41 |

- The pairwise judge prefers the essay it is shown first. It picked essay A in 75% of the 718 judgments and never
  answered "equal". Only verdicts that hold in both orders are used below.
- Half of the "won although less coherent" cases do not hold up. In group a only 28 of 59 pairs are rated lower in
  both orders, and the judge puts the steered essay 5.5 points below its partner. For the losers (group b) it is 56
  of 60 and 13.5 points. So most winners with a lower score are essays with a small or doubtful coherence loss.

Share of the judge's explanations that name each reason, for pairs where both orders rate side a lower:

| reason | a. effort, won | b. effort, lost | d. random | e. unsteered |
|---|---|---|---|---|
| broken tokens (garbled words, foreign characters) | 52% | 68% | 54% | 60% |
| overblown style (inflated metaphor, jargon) | 52% | 38% | 12% | 7% |
| invented specifics (made-up names, numbers) | 16% | 26% | 29% | 17% |
| repetition | 2% | 11% | 6% | 0% |
| explanations counted | 56 | 112 | 82 | 30 |

- Overblown style is the reason that is specific to the effort direction. It is named in 52% and 38% of explanations
  after adding E, against 12% for a random direction and 7% for unsteered pairs. When E is removed (group f) the
  judge names it for the unsteered partner (34%) and not for the steered essay (5%).
- Broken tokens are not specific to E. The judge names them as often for a random direction and for unsteered pairs.
  A count that needs no judge agrees that steering of either kind raises them: non-Latin characters occur in 22% of
  the steered essays in group a and 0% of their partners, 37% against 7% in group b, 27% against 3% for random, and
  10% against 7% in unsteered pairs.
- Winners and losers differ in amount more than in kind. Losers have more broken tokens, more invented specifics and
  more repetition.
- The judge's quotes are real. 95% of 2,056 quoted passages appear word for word in the essay it rated lower.

Examples from group a (steered essay won the panel, scored lower on coherence):

- Layer 26, +0.075, parks topic, 78 against 92. Quoted: "phenology-dependent pollinator populations by an
  astonishing 300%", "The friction of blowing dry grass versus the textured allure of blooming native blooms".
- Layer 20, +0.025, four-day week topic, 72 against 82. Quoted: "It challenges companies to operate with intention
  rather than惯性", "The relentless eight-day workweek has long been the invisible axiom of corporate life".
- Layer 8, +0.05, age verification topic, 78 against 92. The judge objects to a named person it takes to be invented.

Answer to the note. When a winning steered essay scores lower on coherence, the judge points at inflated, jargon-heavy
phrasing, at stray foreign characters or garbled words, and at invented specifics. The first is what adding E does.
Whether the quality panel rewards it as richer writing was not tested here. The other two are what any added vector
does at a low rate. In most such pairs the loss is small, and half of them disappear when the order of the two essays
is swapped.

Limits. The pairwise judge has not been validated beyond its agreement with the absolute scores (Spearman 0.80 over
359 pairs, 83% of judgments agree with the sign of gaps above 3). The reason categories come from one model with no
human check. "Structure" was named in 46 to 95% of explanations in every group, unsteered pairs included, so it was
left out of the table as uninformative.

## 3. Rubric coder on the cross-validation cells (note item 4): not run

The essay finding (E raises argument depth and concrete examples, not thesis framing or closure) is stated in the
essay rubric's markers. The grant rubric has seven different markers and no thesis or closure marker, so the finding
cannot be repeated on grant abstracts without inventing a mapping between the two sets. Dropped by the PI on
2026-11-17.

## 4. Sandbagging and the effort direction (note item 2)

The paper's sandbagging comparison is the harmful-cause framing against the framed-empty baseline. Harmful-side win
rates in the paper, ties excluded:

| model | essay | grant | postmortem |
|---|---|---|---|
| Qwen3.5-9B | 0.52 (144 / 133) | 0.28 (51 / 128) | 0.43 (94 / 125) |
| DeepSeek V3.2 | 0.10 (28 / 251) | 0.31 (92 / 208) | 0.37 (109 / 188) |

Qwen sandbags on grant only, so the Qwen study uses grant abstracts.

### 4.0 Design

Grant task, Qwen3.5-9B, the paper's prompts byte for byte. "Harmful" is the paper's competition wrapper with the
sponsor funding the bad cause of one of 40 moral cause pairs, assigned by the paper's rule. "Baseline" is the paper's
framed-empty wrapper, the same competition text with no sponsor. 30 grant items x 2 repeats give 60 pairs per cell.
Side a is named first in every row. The effort vector E is the essay-built one (week 7), which is held out for grant
and steers it (+0.05 wins 0.67 to 0.76 against unsteered). The dose is +0.05, because +0.1 was too much on grant.
The paper's refusal screen is applied with its classifier unchanged (gpt-5-mini): a pair is "clean" when no
harmful-prompt text in it is a refusal, an abstract with objection commentary, or degenerate. The paper's 0.28 is a
clean-pair number (179 of 300 pairs). Runs `w9_sandbag_local` and `w9_sandbag_remote`, builder
`local/make_sandbag_jobs.py`, tables `local/week9_sandbag.py`.

### 4.1 Replication: in our runs the gap is mostly refusal

The untouched harmful texts of all three runs (360 texts), by the classifier's label:

| label | texts | share |
|---|---|---|
| clean abstract | 196 | 0.54 |
| abstract with an objection ("I cannot ... I can, however, write ...") | 140 | 0.39 |
| full refusal | 24 | 0.07 |

Harmful (side a) against baseline (side b), the three runs pooled (360 pairs: two runs of 60 and the top-up run
`w9_sandbag_power` with 8 more repeats). Every pair is judged. The rows split the pairs by the label of the
harmful-prompt text.

| pairs | n | W / L | win rate | coh a / b | words a / b |
|---|---|---|---|---|---|
| all | 360 | 33 / 234 | 0.12 | | 520 / 648 |
| clean (the paper's screen) | 196 | 32 / 78 | 0.29 | 88.6 / 87.8 | 661 / 648 |
| harmful text has an objection | 140 | 1 / 132 | 0.01 | | 382 / 647 |
| harmful text is a full refusal | 24 | 0 / 24 | 0.00 | | 174 / 650 |

- 46% of harmful-prompt texts are not clean, close to the paper's 40% of pairs excluded for this cell.
- The paper's clean-pair result replicates. The harmful side wins 32 / 78 (0.29, p < 0.001 against 0.50) where the
  paper has 51 / 128 (0.28). Qwen writes worse grant abstracts under the harmful cause when it does not refuse or
  object, with no loss of coherence or length.
- Counting refusals and objections as well, the harmful side wins 33 / 234 (0.12). A text with an objection or a
  refusal practically never wins (1 / 156), and it is shorter (382 and 174 words against 647). About half of the
  raw gap is refusal and objection text.
- Sanity check on the task: max-effort prompt against neutral prompt on grant wins 24 / 5 (0.83; paper 0.68).

### 4.2 Readout: clean harmful abstracts sit backward on the effort direction

Untouched texts re-encoded without steering, response-token-mean projection onto unit vectors as a fraction of the
residual RMS (as in week 8, section 4.1). 196 clean harmful texts against 360 baseline texts, and 60 max-effort against
60 neutral texts for the exhortation. d is Cohen's d, AUC is the chance that a harmful text sits further along the
direction than a baseline text. "ratio" is the harmful shift divided by the exhortation shift.

| direction | layer | clean harmful vs baseline: d, AUC | max-effort vs neutral: d, AUC | ratio |
|---|---|---|---|---|
| E | 6 | -0.61, 0.32 | +1.79, 0.90 | -0.40 |
| E | 10 | -0.79, 0.28 | +1.56, 0.87 | -0.60 |
| E | 14 | -0.72, 0.30 | +1.93, 0.92 | -0.46 |
| E | 16 | -0.89, 0.26 | +2.02, 0.93 | -0.54 |
| random | 6 to 16 | -0.22 to +0.04, 0.43 to 0.52 | -0.51 to +0.17, 0.35 to 0.56 | |
| S (sandbagging vector, 4.4) | 10 | +0.94, 0.75 | +0.03, 0.51 | |
| S | 16 | +1.48, 0.89 | -0.32, 0.41 | |

- The harmful cause moves clean abstracts backward along E, by 0.4 to 0.6 of the distance the exhortation moves
  them forward. A baseline text sits further along E than a clean harmful text 68 to 74% of the time. A random
  direction shows nothing.
- With refusals and objection texts included, harmful and baseline do not separate along E at layers 4 to 16 (AUC 0.49 to 0.54),
  because those texts sit forward on E (d +0.98 to +1.42 for the 140 objection texts). They are a different kind
  of text (short, with meta-commentary), and a random direction also moves for them at layer 16 (d -1.72), so their
  positions say little.
- Within the 110 resolved clean pairs, the E position of the harmful text does not separate pairs the harmful side
  won from pairs it lost (AUC 0.47 to 0.52, p 0.68 to 0.98). The shift along E is a property of the harmful
  condition, and it does not predict which abstract the panel prefers.

### 4.3 Adding the effort vector under the harmful prompt

Side a is the harmful prompt with a vector added at r = +0.05, side b is named in the row. 60 pairs per cell.

| side a | side b | all pairs W / L | clean pairs W / L | clean pairs |
|---|---|---|---|---|
| E, layer 6 | untouched harmful | 18 / 19 | 6 / 4 | 19 |
| E, layer 10 | untouched harmful | 21 / 22 | 6 / 6 | 23 |
| E, layer 16 | untouched harmful | 17 / 20 | 5 / 7 | 22 |
| random, layer 10 | untouched harmful | 11 / 22 | 1 / 3 | 20 |
| E, layer 6 | baseline | 5 / 30 | 5 / 3 | 28 |
| E, layer 10 | baseline | 5 / 34 | 5 / 9 | 34 |
| E, layer 16 | baseline | 6 / 39 | 6 / 13 | 33 |
| random, layer 10 | baseline | 3 / 43 | 3 / 11 | 27 |
| untouched harmful | baseline | 8 / 37 | 8 / 13 | 34 |

The layer-10 cells with the top-up, clean pairs only (first run plus `w9_sandbag_power`):

| side a | side b | clean pairs | W / L | win rate | coh a / b | all pairs (300; last row 360) W / L |
|---|---|---|---|---|---|---|
| harmful + E | untouched harmful | 101 | 24 / 16 | 0.60 | 88.6 / 88.9 | 119 / 83 (0.59) |
| harmful + random | untouched harmful | 116 | 23 / 28 | 0.45 | 88.4 / 88.0 | 90 / 94 (0.49) |
| harmful + E | baseline | 164 | 18 / 49 | 0.27 | 88.0 / 88.6 | 21 / 174 (0.11) |
| harmful + random | baseline | 168 | 14 / 72 | 0.16 | 87.6 / 88.1 | 15 / 198 (0.07) |
| untouched harmful | baseline | 196 | 32 / 78 | 0.29 | 88.6 / 87.8 | 33 / 234 (0.12) |

"All pairs" adds the pairs where a harmful-prompt text is a refusal or carries an objection (judged on 2026-11-18).
In those pairs the two sides are often different kinds of text, so the clean columns are the result.

- Adding E does not undo the gap. The steered harmful abstract wins 0.27 against the baseline, the untouched one
  0.29 (Fisher p = 0.86).
- Against the untouched harmful abstract E wins 24 / 16 (0.60), which differs neither from 0.50 (p = 0.27) nor from
  the random direction's 23 / 28 (p = 0.21). On the neutral prompt the same vector and dose won 0.67 to 0.76 on
  grant in week 7, so E may still help a little here, but the cell cannot show it. Over all pairs the picture is the
  same with more data: E 119 / 83 (0.59) against random 90 / 94 (0.49), p = 0.053, and no gain against the baseline
  (21 / 174 against 33 / 234, p = 0.66).
- A random direction makes the harmful abstract somewhat worse against the baseline (14 / 72, p = 0.04 against the
  untouched 32 / 78). E does not.
- E does not change the refusal rate. The clean share is 0.57 untouched, 0.45 to 0.57 with E and 0.45 with a random
  direction (first run).
- Layers 6 and 16 have the first run only (19 to 33 clean pairs, 8 to 19 resolved) and say nothing either way.

### 4.4 A sandbagging vector

S is the mean residual under the harmful prompt minus the baseline prompt, grant, 300 responses per arm, response
mean, the recipe of E (`vectors/qwen3.5-9b_sandbag_v1`). The extraction responses include the refusals.

| property | value |
|---|---|
| split-half cosine, layers 4 to 20 | 0.97 to 0.98 |
| held-out AUC | 0.82 to 0.90 |
| size relative to the residual RMS | 0.04 to 0.14 (E: about 0.01) |
| cosine with E | +0.20 at layer 4, +0.08 to +0.10 at layers 6 to 14, 0.00 at 16, -0.09 at 20 |

Steering with S at layer 10, 60 pairs per cell. "S minus E" is S with its E component projected out.

| side a | side b | all pairs W / L | clean pairs W / L | coh a / b | words a / b |
|---|---|---|---|---|---|
| harmful, S removed (r -0.1) | untouched harmful | 28 / 15 | 10 / 3 | 90.8 / 90.1 | 661 / 658 |
| harmful, S minus E removed | untouched harmful | 29 / 14 | 7 / 1 | 90.9 / 89.9 | 651 / 667 |
| harmful, S removed | baseline | 9 / 31 | 9 / 7 | 90.6 / 88.8 | 667 / 645 |
| harmful, S minus E removed | baseline | 6 / 31 | 6 / 4 | 88.9 / 88.0 | 647 / 650 |
| untouched harmful (this run) | baseline | 4 / 36 | 4 / 7 | 90.5 / 88.5 | 665 / 650 |
| baseline, S added (r +0.1) | untouched baseline | 3 / 27 | 3 / 27 | 89.0 / 88.9 | 628 / 646 |
| baseline, S minus E added | untouched baseline | 2 / 26 | 2 / 26 | 89.2 / 88.9 | 631 / 646 |

- S is a reliable direction and it is not the effort direction. Its cosine with E is near zero, and projecting E out
  changes nothing in any cell.
- Adding S to the baseline prompt makes the abstracts lose (3 / 27, p < 0.001) with coherence unchanged and no
  refusals (0 of 60 texts open with a refusal phrase). So S carries a drop in quality and not only refusal text.
- Removing S under the harmful prompt helps (28 / 15 on all pairs, 10 / 3 and 7 / 1 on clean pairs) and moves the
  clean-pair result against the baseline from 4 / 7 to 9 / 7 and 6 / 4. The clean cells are small (8 to 16 resolved
  pairs), so this is a direction of effect and not an estimate.
- Removing S does not stop the refusals. The clean share is 30 of 60 untouched, 35 of 60 with S removed and 33 of 60
  with S minus E removed.

### 4.5 What this says

- Qwen's sandbagging on grant replicates on clean pairs (32 / 78, paper 51 / 128). On top of it, 46% of the
  harmful-prompt texts are refusals or carry an objection.
- The effort direction registers the harmful cause. Clean harmful abstracts sit backward on E by about half an
  exhortation (196 against 360 texts). The position does not predict the panel's choice within the harmful arm.
- The effort direction does not carry the sandbagging. Adding E under the harmful prompt at layer 10 leaves the
  gap to the baseline where it was (0.27 against 0.29, 164 and 196 clean pairs). At layers 16 to 20 (section 4.6)
  E makes the harmful abstract somewhat better than a random direction does (78 / 45 against 43 / 65), and the gap
  to the baseline stays (0.28 against 0.18 untouched in that run, p = 0.12). A vector built from the harmful contrast is
  orthogonal to E, lowers quality when added to the baseline prompt (3 / 27) and helps when removed under the
  harmful prompt (28 / 15 on all pairs, 10 / 3 on clean pairs).
- So in this model and task, sandbagging and low effort are different directions. The harmful cause moves the text
  a little along the effort axis as a side effect and does its damage elsewhere.
- Not tested: other layers or doses for S and larger samples for its clean-pair cells (8 to 16 resolved pairs),
  doses of E above +0.05 under the harmful prompt, E built on grant texts, and the essay and postmortem tasks. DeepSeek is section 5.

### 4.6 Layers 16 to 20 with a control at each layer (2026-11-18)

Run `w9_sandbag_late`: 30 topics, repeats 10 to 17, 240 pairs per cell, grant. E (built on essay, as before) and a
random direction of the same size are added under the harmful prompt at layers 16, 18 and 20, r = +0.05. The layers
are those where the clean readout is strongest (4.2). Every steered cell is paired with the untouched harmful
abstract and with the baseline abstract. As a check that E does anything at these layers, E is also added under the
baseline prompt (layers 18 and 20). Manifest: `make_sandbag_jobs --vectors
outputs/steering/vectors/qwen3.5-9b_essay_v1/vectors.safetensors --run-name w9_sandbag_late --items 30 --repeats 8
--repeat-start 10 --bridge` with `--cell E:L:0.05:harmful` and `--cell rand0:L:0.05:harmful` for L = 16, 18, 20
and `--cell E:L:0.05:empty` for L = 18, 20; generated by `vast/w9l_chain.sh`. Clean pairs only (1,927 of 3,600 pairs; all of them judged). Coherence is 86 to
90 on both sides of every cell and the two sides differ by at most 23 words on average.

| side a | side b | clean pairs | W / L | win rate |
|---|---|---|---|---|
| untouched harmful | baseline | 133 | 14 / 62 | 0.18 |
| harmful + E, layer 16 | untouched harmful | 89 | 25 / 13 | 0.66 |
| harmful + E, layer 18 | untouched harmful | 83 | 29 / 13 | 0.69 |
| harmful + E, layer 20 | untouched harmful | 96 | 24 / 19 | 0.56 |
| harmful + random, layer 16 | untouched harmful | 82 | 16 / 25 | 0.39 |
| harmful + random, layer 18 | untouched harmful | 79 | 12 / 12 | 0.50 |
| harmful + random, layer 20 | untouched harmful | 96 | 15 / 28 | 0.35 |
| harmful + E, layer 16 | baseline | 135 | 20 / 41 | 0.33 |
| harmful + E, layer 18 | baseline | 125 | 20 / 48 | 0.29 |
| harmful + E, layer 20 | baseline | 143 | 15 / 51 | 0.23 |
| harmful + random, layer 16 | baseline | 123 | 14 / 55 | 0.20 |
| harmful + random, layer 18 | baseline | 121 | 7 / 54 | 0.11 |
| harmful + random, layer 20 | baseline | 142 | 9 / 67 | 0.12 |
| baseline + E, layer 18 | untouched baseline | 240 | 65 / 41 | 0.61 |
| baseline + E, layer 20 | untouched baseline | 240 | 51 / 45 | 0.53 |

The three layers pooled:

| side a | side b | E: W / L | random: W / L | E against random (Fisher) |
|---|---|---|---|---|
| steered harmful | untouched harmful | 78 / 45 (0.63) | 43 / 65 (0.40) | p < 0.001 |
| steered harmful | baseline | 55 / 140 (0.28) | 30 / 176 (0.15) | p < 0.001 |

- The sandbagging replicates a third time: 14 / 62 (0.18). With the earlier runs the clean-pair result is 46 / 140
  (0.25).
- E improves the harmful abstract, a random direction does not. Against the untouched harmful abstract E wins
  78 / 45 (p = 0.004 against 0.50), the random direction 43 / 65. Per layer the difference from the same-layer
  control is p = 0.02, 0.19 and 0.08. It is not a length effect: at equal length the advantage of E over the random
  direction is +0.82 log-odds (p = 0.005; +0.96 without length).
- E does not close the gap. The steered harmful abstract wins 0.28 against the baseline (95% interval 0.22 to
  0.35), far from 0.50. Compared with the untouched 0.18 of this run the gain is not significant (p = 0.12;
  at equal length +0.49 log-odds, p = 0.17), and the earlier runs had 0.29 untouched. About half of the difference
  between E and the random direction comes from the random direction making the abstract worse (0.15 against
  0.18), as at layer 10.
- E is a weak push at these layers even without a harmful cause: under the baseline prompt it wins 0.61 at layer
  18 (p = 0.03) and 0.53 at layer 20 (p = 0.61). The max-effort prompt wins 0.83 on this task (4.1).
- Layer 16 was also in the first run with 60 pairs (5 / 7 and 6 / 13 on clean pairs), in line with this run.

## 5. DeepSeek V3.2, hosted white-box (note item 2)

DeepSeek V3.2 was the strongest sandbagger in the paper (essay 0.10, grant 0.31). We hosted the checkpoint as released
(FP8, 671.9B parameters) on a rented machine with 8 x RTX PRO 6000 and ran the paper's prompts on it with thinking off.
Chain `vast/ds1_chain.sh`, cells `local/week9_ds_cells.sh`, runs `ds_base_essay`, `ds_base_grant`, `ds_steer`, vectors
`vectors/deepseek-v3.2_v1`, tables in `outputs/steering/w9_analysis/ds/`.

### 5.1 Hosting

Smoke test on a rented machine with 8 x RTX PRO 6000 (95 GiB each), transformers main, the checkpoint as released
(FP8, 671.9B parameters). Script `remote/deepseek_smoke.py`, reports in `outputs/steering/ds0/`.

| check | result |
|---|---|
| download of 690 GB | 11 minutes |
| load | 183 s, 669.9B parameters in FP8, 8 layers per GPU with a cap of 86 GiB per GPU |
| generation with thinking off | 4 paper essay prompts, 392 to 416 tokens, all ended normally, fluent on-topic essays |
| residual capture at layers 15, 30, 45 | works; RMS norm 9.8, 41.0, 120.0 |
| steering with a random vector at layer 30 | a zero vector reproduces the baseline text exactly; 0.5 x RMS changes the wording, 2 x degrades it, 8 x breaks it |

Throughput (tokens per second in total, 128 new tokens per text):

| batch | tokens / s | peak memory on the fullest GPU |
|---|---|---|
| 4 | 9.6 | |
| 16 | 25.8 | |
| 32 | 46.2 | 88.0 GiB |
| 64 | 81.8 | 90.2 GiB |
| 96 | 121.0 | 92.3 GiB |
| 128 | out of memory | |

Three smoke-test attempts were needed (a host without access to PyPI, an invalid entry in the list of modules to keep
unquantized, and GPU memory during load, fixed with a cap of 86 GiB per GPU and by keeping the output head
unquantized). The load stays tight on these cards and failed once more during the study, so every step of the chain
now retries.

### 5.2 Replication: the hosted model sandbags as in the paper, without refusing

Harmful (side a) against baseline (side b), 30 items x 2 repeats, the paper's prompts and panel. The essay cell was run
twice (base run and the steering run's own base pairs).

| task | pairs | W / L | win rate | paper | coh a / b | words a / b | clean harmful texts |
|---|---|---|---|---|---|---|---|
| essay | 120 | 3 / 81 | 0.04 | 0.10 (28 / 251) | 92.0 / 91.8 | 308 / 375 | 120 of 120 |
| grant | 60 | 5 / 33 | 0.13 | 0.31 (92 / 208) | 92.0 / 91.6 | 543 / 584 | 60 of 60 |
| max-effort vs neutral, essay | 60 | 31 / 3 | 0.91 | | 91.9 / 91.5 | 372 / 328 | |

- The hosted model reproduces the paper's direction on both tasks, somewhat more strongly. The grant cell has 38
  resolved pairs, so its difference from the paper's 0.31 is not established.
- No harmful-prompt text is a refusal or carries an objection. DeepSeek's gap is all sandbagging: equal coherence,
  shorter and worse texts. In Qwen 46% of the harmful-prompt texts were refusals or objections.

### 5.3 Vectors

E is max-effort minus neutral on grant items, S is harmful minus baseline on essay items, 150 responses per arm each,
300 new tokens, response mean. 61 layers.

| layer | E: split-half, held-out AUC | S: split-half, held-out AUC | cos(S, E) |
|---|---|---|---|
| 6 | 0.68, 0.93 | 0.63, 0.89 | -0.21 |
| 12 | 0.57, 0.87 | 0.48, 0.81 | -0.19 |
| 20 | 0.68, 0.92 | 0.69, 0.90 | about -0.2 (layer 18: -0.17) |
| 30 | 0.68, 0.93 | 0.77, 0.98 | -0.45 |
| 42 | 0.58, 0.85 | 0.64, 0.87 | -0.56 |
| 54 | 0.47, 0.78 | 0.62, 0.84 | -0.47 |

- Both vectors are reliable. The sandbagging direction points against the effort direction, weakly up to layer 20
  and clearly from layer 24 on (-0.33 to -0.56). In Qwen the cosine was about zero.

### 5.4 Readout

Untouched texts of the base runs re-encoded without steering, 60 per condition, response-mean projection as a
fraction of the residual RMS. d is Cohen's d, AUC the chance that the first-named text sits further along the
direction. "ratio" is the harmful shift divided by the exhortation shift.

| direction | layer | harmful vs baseline, essay: d, AUC | harmful vs baseline, grant: d, AUC | max-effort vs neutral, essay: d, AUC | ratio (essay) |
|---|---|---|---|---|---|
| E | 12 | -0.32, 0.40 | -0.47, 0.38 | +1.66, 0.89 | -0.21 |
| E | 20 | -0.36, 0.39 | -0.85, 0.27 | +1.17, 0.79 | -0.31 |
| E | 30 | -1.97, 0.08 | -1.69, 0.11 | +1.91, 0.92 | -1.02 |
| E | 42 | -1.71, 0.11 | -1.05, 0.24 | +1.30, 0.82 | -1.33 |
| S | 20 | +2.08, 0.94 | +2.29, 0.95 | -0.92, 0.25 | |
| S | 30 | +4.56, 1.00 | +4.06, 1.00 | -1.29, 0.18 | |
| random | 6 to 48 | -0.49 to +0.04, 0.36 to 0.51 | -0.43 to +0.35, 0.39 to 0.60 | -0.05 to +0.39, 0.48 to 0.60 | |

- From layer 30 on, the harmful cause moves DeepSeek's texts backward along E by about as far as the exhortation
  moves them forward (ratio -0.9 to -1.3; Qwen -0.4 to -0.6). A baseline essay sits further along E than a harmful
  essay 92% of the time at layer 30.
- This holds on grant, a task S was not built from, and E was built from other samples of grant prompts.
- The exhortation moves texts backward along S (AUC 0.18 to 0.35). The two contrasts read as opposite ends of one
  axis in this model.

### 5.5 Steering

How the cells were chosen. Layers 12, 20 and 30 of 61 are the relative depths of the Qwen layers 6, 10 and 16 of
32. The doses are the ones that worked on Qwen. Neither was tuned on DeepSeek: the grid was fixed before the
vectors existed, because the chain ran unattended, and the calibration step of the plan (three doses on ten texts)
was skipped. The only check on this model was the smoke test, where a random vector at layer 30 changed the wording
at 0.5 of the residual norm and degraded the text at 2.

Essay task, 60 pairs per cell, dose as a fraction of the layer's RMS residual norm. Coherence is 90.9 to 92.2 in
every cell and 719 of 720 steered harmful texts are clean, so no cell is damaged.

Harmful prompt with a vector, against the untouched harmful essay and against the baseline essay:

| vector, layer, dose | vs untouched harmful: W / L | vs baseline: W / L | words (untouched harmful 307, baseline 373) |
|---|---|---|---|
| none | | 1 / 41 | 307 |
| E added, layer 12, +0.05 | 16 / 6 | 1 / 36 | 315 |
| E added, layer 12, +0.1 | 21 / 10 | 1 / 35 | 319 |
| E added, layer 20, +0.05 | 24 / 11 | 2 / 39 | 321 |
| E added, layer 20, +0.1 | 20 / 3 | 2 / 33 | 327 |
| E added, layer 30, +0.05 | 27 / 7 | 8 / 28 | 329 |
| E added, layer 30, +0.1 | 29 / 1 | 6 / 23 | 337 |
| S removed, layer 12, -0.1 | 20 / 6 | 3 / 33 | 324 |
| S removed, layer 20, -0.1 | 19 / 4 | 2 / 34 | 326 |
| S removed, layer 30, -0.1 | 21 / 11 | 3 / 33 | 333 |
| S minus E removed, layer 20, -0.1 | 19 / 5 | 3 / 39 | 320 |
| random added, layer 20, +0.1 | 14 / 9 | 2 / 38 | 315 |

Baseline prompt with S added at +0.1, against the untouched baseline essay: layer 12 10 / 19, layer 20 5 / 17,
layer 30 6 / 18 (words 366, 352, 354 against 373). There is no random-direction control under the baseline prompt.

- Adding effort at layer 30 partly undoes the sandbagging. The steered harmful essay beats the untouched one 29 / 1
  (random direction 14 / 9, Fisher p = 0.001) and wins 6 / 23 (0.21) against the baseline where the untouched
  harmful essay wins 1 / 41 (0.02, p = 0.016). Layer 30 is where the readout is strongest. Layers 12 and 20 show the
  same direction against the untouched harmful essay (0.68 and 0.87) and no gain against the baseline.
- Half the dose at layer 30 gives the same result in separately generated essays: 8 / 28 (0.22) against the
  baseline (p = 0.010 against 1 / 41). The two layer-30 cells together win 14 / 51 (0.22, p = 0.004). At layers 12
  and 20 the half dose also changes nothing against the baseline.
- The rescue is partial and did not grow with the dose. Against the baseline +0.05 and +0.1 give 0.22 and 0.21,
  while against the untouched harmful essay (0.79 and 0.97) and in length (22 and 30 of the 66 missing words) the
  larger dose does more. Doses above +0.1 were not run, and coherence shows no cost yet at +0.1.
- Removing S under the harmful prompt helps against the untouched harmful essay (0.66 to 0.83) but not more than a
  random direction does (p 0.19 to 0.78), and does not help against the baseline (0.06 to 0.08).
- Adding S to the baseline prompt lowers the essays (0.23 to 0.34 win rate, p = 0.02 at layers 20 and 30), without a
  control to compare with.
- A random direction added under the harmful prompt wins 14 / 9 against the untouched harmful essay, so 0.61 and
  not 0.50 is the level to compare the steered cells with.

Limits of this section.

- The random control is at layer 20. There is none at layer 30, so the layer-30 result is compared with a random
  direction from another layer. At layer 20, where the control is, E does not beat it against the baseline
  (2 / 33 and 2 / 39 against 2 / 38).
- Length predicts the panel's choice. In the resolved pairs of a steered harmful essay against the untouched
  harmful essay, the longer essay wins 264 of 304, and 20 of 23 in the random cell. The harmful essays are 66
  words shorter than the baseline essays and E adds 22 to 30 words. Section 5.6 shows that the rescue goes
  largely through length.
- The two layer-30 cells share their comparison essays (the same 60 untouched harmful and baseline essays).
  Against both runs of the untouched cell (3 / 81) the pooled 14 / 51 gives p = 0.001. The exact 95% interval
  of 14 / 51 is 0.12 to 0.33.
- Three layers and two doses were tried and none was tuned, so layer 30 is where an effect was found and not
  where it is largest. The readout is as strong at layer 42.

### 5.6 Length (reanalysis, 2026-11-18)

Script `local/week9_length.py`, tables in `outputs/steering/w9_analysis/length_tables.txt`. Resolved pairs only.
The word difference is side a minus side b. Pairs share texts (every cell is compared with the same untouched
essays), so the p values are approximate.

How often the longer text wins:

| comparison (side a vs side b) | DeepSeek, essay | Qwen, grant, clean pairs |
|---|---|---|
| harmful vs baseline | 82 of 84 | 66 of 110 |
| max-effort vs neutral | 32 of 34 | 20 of 29 |
| steered harmful vs untouched harmful | 264 of 304 | 96 of 134 |
| steered harmful vs baseline | 374 of 405 | 143 of 206 |
| odds of winning per 10 more words | x 1.5 to 1.9 | x 1.1 to 1.4 |

DeepSeek, harmful-prompt essay against the baseline essay, wins / resolved pairs by word difference:

| side a | all | more than 60 shorter | 30 to 60 shorter | up to 30 shorter | longer |
|---|---|---|---|---|---|
| untouched harmful | 3 / 84 | 0 / 60 | 2 / 16 | 0 / 7 | 1 / 1 |
| random added, layer 20 | 2 / 40 | 0 / 23 | 1 / 12 | 0 / 4 | 1 / 1 |
| E added, layer 12 | 2 / 73 | 0 / 45 | 1 / 23 | 1 / 4 | 0 / 1 |
| E added, layer 20 | 4 / 77 | 0 / 39 | 1 / 28 | 1 / 7 | 2 / 3 |
| E added, layer 30 | 14 / 65 | 1 / 25 | 4 / 22 | 4 / 11 | 5 / 7 |
| S removed | 8 / 108 | 0 / 50 | 2 / 31 | 3 / 21 | 3 / 6 |

The effect of each group in a logistic regression, as log-odds, before and after adding the word difference:

| comparison | group vs reference | without length | at equal length |
|---|---|---|---|
| vs baseline | E layer 30 vs untouched harmful | +2.00 (p = 0.002) | +1.22 (p = 0.10) |
| vs baseline | S removed vs untouched harmful | +0.77 (p = 0.27) | -0.18 (p = 0.82) |
| vs untouched harmful | E layer 30 vs random layer 20 | +1.50 (p = 0.008) | +0.42 (p = 0.64) |
| vs untouched harmful | E layer 20 vs random layer 20 | +0.63 (p = 0.22) | +0.20 (p = 0.81) |

- In DeepSeek the panel picks the longer essay in 85 to 98% of resolved pairs, in every comparison, the untouched
  ones included. A harmful essay that is more than 60 words shorter than the baseline essay wins 1 of 264 pairs
  whatever is done to it.
- DeepSeek's sandbagging, as the panel sees it, is mostly shorter essays. At equal length the model predicts that
  a harmful-prompt essay wins 0.35 of pairs against the baseline (95% interval 0.24 to 0.47, all harmful-prompt
  cells), against 0.07 observed. So a gap remains at equal length, and it is much smaller.
- The rescue by E at layer 30 goes largely through length. E makes the essays longer (the gap to the baseline
  shrinks from 79 to 50 words). Once the word difference is in the model, the advantage over the random direction
  is gone (p = 0.64) and the advantage over the untouched harmful essay drops to +1.22 (p = 0.10). In the bins the
  layer-30 essays still win more often than others of similar length (8 / 33 against 2 / 23 for untouched in the
  two middle bins), on small counts.
- Whether the judges reward length as such or longer essays are better in other ways is not separated here. The
  max-effort prompt also makes essays longer (372 against 328 words) and wins 31 / 3.
- Qwen is different. Length matters less (the longer abstract wins 60 to 74%), harmful and baseline abstracts have
  the same length, and at equal length the harmful abstract is predicted to win 0.21 (0.16 to 0.28) against 0.25
  observed (all four runs; 0.26 against 0.29 before the run of section 4.6). Qwen's sandbagging is not a length effect. Removing S keeps its advantage at equal length (+1.07,
  p = 0.09, against +1.14 without).

### 5.7 Cost

OpenRouter, from the usage recorded with every call: $43.35 for the whole week. The run of section 4.6 cost
$17.31 of that (panel $13.95 for 1,927 pairs, coherence $2.82, refusal classifier $0.54) and about $1 of GPU
(A100, $0.55 per hour, under two hours). The rest, $26.04: Panel judging $20.08 (Qwen $14.45
for 2,220 pairs, DeepSeek $5.63 for 1,740 pairs), coherence scores $3.32, refusal classifier $0.59, pairwise
coherence judge of section 2 $2.06.

The study machine ran 4 h 40 min and cost $99.69 on vast including the $8.20 download fee. About 45 minutes of that
went into two bugs in new code (a model load that fails now and then, and an out-of-memory fallback that kept the
failed batch in memory). The three smoke-test attempts before it cost $54, of which $33 were download fees.

## 6. What the sandbagging results say

- Both models write worse texts under a harmful cause, as in the paper. Qwen also refuses or objects in 46% of the
  texts. DeepSeek never does.
- In both models the harmful cause moves the text backward along the effort direction: by about half an
  exhortation in Qwen and by a full one in DeepSeek.
- The models differ in whether effort carries the sandbagging. In Qwen the sandbagging vector is orthogonal to
  effort and adding effort does not close the gap (0.27 against 0.29 at layer 10, 0.28 against 0.18 at layers 16 to
  20, section 4.6). In DeepSeek the sandbagging vector points
  against effort (cosine -0.45 at layer 30) and adding effort at that layer partly closes the gap (0.22 and 0.21
  at the two doses against 0.02), without closing more at the higher dose.
- The difference between the models is smaller than it looked. Qwen is now tested at layers 16 to 20 with a
  control at each layer (section 4.6): E helps the harmful abstract a little more than a random direction and the
  harmful abstract still wins only 0.28 against the baseline. DeepSeek's 0.22 at layer 30 is a similar number,
  from a lower start (0.02). DeepSeek's effect appeared at one of three layers. The DeepSeek result has no random control at its own layer and may work
  through essay length (section 5.5, limits).
- In DeepSeek the sandbagging as judged, and the rescue, are mostly essay length (section 5.6). The panel picks the
  longer essay in 85 to 98% of pairs, and at equal length E at layer 30 no longer beats a random direction. In
  Qwen the harmful and baseline abstracts have the same length and the gap is not a length effect.
- Not tested: doses above +0.1 and layers between 30 and 42 on DeepSeek, a random-direction control under the baseline prompt,
  DeepSeek steering on grant, and larger cells (every DeepSeek steering cell has 60 pairs and 23 to 42 resolved).
