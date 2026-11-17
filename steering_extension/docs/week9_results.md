# Week 9 results (2026-11-17): where the coherence loss comes from, what the coherence judge objects to, sandbagging

Plan: `week9_plan.txt` (repo root), from `steering_extension/0711_meeting_notes.txt`. Sections 1, 2 and 4 are done for Qwen. DeepSeek (4.6) is open and says so.

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

Harmful (side a) against baseline (side b). "All pairs" is the two fully judged runs (120 pairs). "Clean" pools
the clean pairs of those runs and of the top-up run `w9_sandbag_power` (8 more repeats, only clean pairs judged),
196 clean pairs in all.

| pairs | n | W / L | win rate | coh a / b | words a / b |
|---|---|---|---|---|---|
| all | 120 | 12 / 73 | 0.14 | | |
| clean (the paper's screen) | 196 | 32 / 78 | 0.29 | 88.6 / 87.8 | 661 / 648 |
| harmful text has an objection (first run) | 22 | 0 / 20 | 0.00 | | 418 / 660 |
| harmful text is a full refusal (first run) | 4 | 0 / 4 | 0.00 | | 164 / 658 |

- 46% of harmful-prompt texts are not clean, close to the paper's 40% of pairs excluded for this cell.
- The paper's clean-pair result replicates. The harmful side wins 32 / 78 (0.29, p < 0.001 against 0.50) where the
  paper has 51 / 128 (0.28). Qwen writes worse grant abstracts under the harmful cause when it does not refuse or
  object, with no loss of coherence or length.
- Counting refusals and objections as well, the harmful side wins 12 / 73 (0.14). About half of the raw gap is
  refusal and objection text.
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

| side a | side b | clean pairs | W / L | win rate | coh a / b |
|---|---|---|---|---|---|
| harmful + E | untouched harmful | 101 | 24 / 16 | 0.60 | 88.6 / 88.9 |
| harmful + random | untouched harmful | 116 | 23 / 28 | 0.45 | 88.4 / 88.0 |
| harmful + E | baseline | 164 | 18 / 49 | 0.27 | 88.0 / 88.6 |
| harmful + random | baseline | 168 | 14 / 72 | 0.16 | 87.6 / 88.1 |
| untouched harmful | baseline | 196 | 32 / 78 | 0.29 | 88.6 / 87.8 |

- Adding E does not undo the gap. The steered harmful abstract wins 0.27 against the baseline, the untouched one
  0.29 (Fisher p = 0.86).
- Against the untouched harmful abstract E wins 24 / 16 (0.60), which differs neither from 0.50 (p = 0.27) nor from
  the random direction's 23 / 28 (p = 0.21). On the neutral prompt the same vector and dose won 0.67 to 0.76 on
  grant in week 7, so E may still help a little here, but the cell cannot show it.
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
- The effort direction does not carry the sandbagging. Adding E under the harmful prompt leaves the gap to the
  baseline where it was (0.27 against 0.29, 164 and 196 clean pairs). A vector built from the harmful contrast is
  orthogonal to E, lowers quality when added to the baseline prompt (3 / 27) and helps when removed under the
  harmful prompt (28 / 15 on all pairs, 10 / 3 on clean pairs).
- So in this model and task, sandbagging and low effort are different directions. The harmful cause moves the text
  a little along the effort axis as a side effect and does its damage elsewhere.
- Not tested: other layers or doses for S and larger samples for its clean-pair cells (8 to 16 resolved pairs),
  higher doses of E under the harmful prompt, the essay and postmortem tasks, and anything on DeepSeek.

### 4.6 DeepSeek V3.2

DeepSeek V3.2 can be hosted white-box on a rented eight-GPU machine. The port is written and tested on CPU only
(`docs/deepseek_port_notes.md`, `remote/deepseek_smoke.py`, `vast/ds0_chain.sh`). The first smoke-test attempt failed
after one minute because the rented host could not reach PyPI. A second attempt on another host is running. No
result yet.
