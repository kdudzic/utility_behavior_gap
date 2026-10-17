# Why layer 16, and how to choose the injection layer properly

Written 2026-10-17 for the PI and Chris, after the question "why 16?" at the 2026-10-10 review.
Short answer: layer 16 was a depth prior plus a coherence screen, not an efficacy-selected layer. The
proposal planned an efficacy sweep (PROPOSAL.md Section 4 step 6); the pilot ran a version of it that
could not discriminate between layers, and fell back to the prior. This is a methodological hole. Section 3
is a plan to close it with a pre-registered selection rule that does not spend judge money on the sweep.

## 1. What actually happened

1. PROPOSAL step 6 planned: sweep every second layer in the 0.3-0.7 depth band (layers 10-22 of 32) at
   a fixed relative dose on 20 held-out items, score with one cheap judge plus the coherence judge, choose
   the layer maximising steered-vs-unsteered win rate subject to mean coherence >= 80.
2. The mini-pilot (report Section "Phase 2a mini") swept layers {8, 12, 16, 20, 24} x doses {0.05, 0.1, 0.2}
   on **10 essay items** with the **paper's full three-judge panel and tie convention** (flip -> tie, panel
   split -> tie). Panel ties ran 60-100 percent per cell, so each cell resolved 2-5 pairs. Win rates ranged
   from 0.00 to 1.00 with no pattern; the random direction "won" 4/0 at one cell. Nothing could be selected
   on efficacy. Coherence was informative: layers 8-16 stayed within about 5 points of the unsteered score up
   to r = 0.2, layers 12 and 24 dropped to 76-80 at r >= 0.1, layer 20 was also lower.
3. Layer 16 was then chosen as "mid-depth prior, coherent to r = 0.2". The prior is the literature band:
   CAA best layer 13/32 (0.41 depth), Arditi's selected directions at 0.4-0.6 depth, Persona Vectors
   layer 16/32 on Llama-3.1-8B and 20/28 on Qwen2.5-7B, Hidden Valence uses the middle layer by construction.
   16/32 = 0.50 is the centre of that band and the deepest of the coherent layers in the sweep.
4. The full pilot added a post-hoc layer check at +/-0.1: layers 12, 16, 20 behaved alike (negative dose
   hurts at all three: 5/25, 7/26, 7/18; positive dose null-to-negative at all three).

So the honest statement for Chris: the choice was a prior, screened for coherence; the efficacy criterion in
the proposal failed for a predictable reason (the tie-excluding panel wastes most pairs at n = 10), and the
post-hoc check only shows that the negative-side result is not specific to layer 16. It says nothing about
whether a different layer would have produced the missing positive-side effect.

## 2. Why this matters more than usual here

- The sufficiency test (H1) is the one that failed. Steering efficacy is known to be sharply layer-dependent
  (CAA Figure: a few layers work, neighbours do not; Persona Vectors App. layer sweeps are peaked). A null
  at one unselected layer is weak evidence against sufficiency.
- Qwen3.5-9B is a hybrid: `layer_types` is three `linear_attention` (Gated DeltaNet) blocks then one
  `full_attention` block, so full-attention blocks are indices 3, 7, 11, 15, 19, 23, 27, 31. Our hook adds to
  the output of block 16, i.e. the residual stream right after the first DeltaNet block following attention
  block 15. Nothing in the literature band was derived on this architecture; whether the residual after an
  attention block or after a DeltaNet block is the better injection point is an open empirical question and
  the sweep must straddle both.
- The best monitoring layer is usually too deep to steer (Pain Axis: ratio vector/residual 0.10 at the best
  monitoring layer vs 0.6 where steering works). Our relative norms rise with depth (E: 0.011 at L12, 0.014 at
  L16, 0.022 at L20), so monitoring and steering layers must be chosen separately, as the proposal says, and
  both reported.

## 3. Plan: pre-registered layer selection without judge spend on the sweep

Principle: pick the layer with criteria that are continuous (no ties), cheap (GPU only, or free from extraction
data), and computed on tasks held out from the essay evaluation. Judges are used once, at the end, to confirm
the top candidates. Everything below runs on the new E extraction (assistant-start-token and user-prompt-mean
readouts, grant + postmortem only), so it costs little beyond what is already planned.

### Stage L1: direction quality per layer (free, from extraction data)

For every layer 0-31, from the per-response captures:
- **Split-half reliability**: cosine between E estimated from two random halves of the responses (and the
  Spearman-Brown corrected value). Currently 0.65 at layer 16 only; we do not know the profile.
- **Held-out projection AUC**: project held-out pos and neg responses onto E; AUC of pos vs neg. This is the
  Pain Axis / Persona Vectors monitoring criterion. Its argmax defines the **monitoring layer**.
- **Relative norm** ||E|| / RMS(residual).
Output: a per-layer table. Candidate steering layers = all layers in the 0.25-0.75 depth band (8-24) with
split-half cosine >= 0.5. Requires `extract.py` to save per-response, per-layer projections (small) rather
than only running sums.

### Stage L2: steering efficacy proxy per layer (GPU only)

For each candidate layer L, with 30 held-out grant items (postmortem as replication):
1. **Dose calibration, two hurdles** (Hidden Valence): find r_L, the largest dose at which (a) mechanical
   coherence holds (repetition rate, truncation, non-ASCII, and a KL-to-unsteered check on the first 32
   response tokens, Arditi style, KL < 0.1 nats median) and (b) "arrival" holds: re-encoding the steered text
   shifts its projection on E at the monitoring layer by |t| >= 2 relative to unsteered text. Doses tested on a
   fixed ladder {0.025, 0.05, 0.075, 0.1, 0.15}. Layers where no dose passes both hurdles are dropped.
2. **Efficacy proxy = signature match**: compute the repo's feature pipeline (the paper's Table 2 features:
   length, lexical rarity, sentence length, readability, numeric detail, hedging, etc.) on steered vs unsteered
   outputs at r_L and at r_L/2. The proxy is the correlation across features between the steered-minus-unsteered
   standardised deltas and the paper's exhortation-minus-neutral deltas for Qwen3.5-9B (`CURRENT_PAPER/results`).
   This asks the question we actually care about, "does steering at this layer reproduce the natural effort
   effect", with no judge and no ties.
3. **Arrival size** at r_L (from 1b) as a secondary continuous efficacy measure.
Selection rule, fixed in advance: steering layer = argmax over candidates of signature match at r_L; ties
within 0.05 broken by higher arrival size, then by the earlier layer. Also record the best full-attention
output layer (15 or 19) and the best DeltaNet output layer separately.
Cost: about 9 layers x 5 doses x 30 items = 1,350 generations at 300-400 tokens, roughly 1 A100-hour, under $1.

### Stage L3: judge confirmation (small, paid)

Top three layers from L2 plus the incumbent (16), each at r_L and r_L/2, 30 grant items, one judge
(gemini-3.1-flash-lite, both orders, per-judge verdict without the panel tie rule) plus the coherence judge.
About 240 pairs, roughly $2-3. The L2 winner is retained unless the single judge ranks it below another
candidate by more than 0.15 win rate; then the discrepancy is reported and the judged winner used.
Rationale for keeping the judge small: it is a check on the proxy, not the selection criterion.

### Stage L4: robustness reported with the main essay dose curve

- Full signed dose curve at the selected layer (the main result), plus the same curve at the selected
  layer +/- 4 and at the incumbent 16 if different, at two doses each.
- One multi-layer condition (Persona Vectors style: the vector added at three consecutive layers with
  one third of the dose each), to show the result is not an artefact of single-point injection.
- Monitoring layer reported separately with its AUC; projections under the paper's prompts (Phase 3 of
  the proposal) use that layer, never the steering layer.

### What this changes in the proposal

- Section 4 step 6 is replaced by Stages L1-L3 above; the cheap-judge-on-essay sweep is dropped because the
  essay items are the evaluation set and because win-rate sweeps at n = 20-30 cannot rank layers.
- Translation is removed from extraction and from every table (PI decision 2026-10-17); extraction uses
  grant + postmortem, evaluation uses essay.
- The signature-match proxy is itself a planned analysis (proposal Section 6, "feature signature"), so this
  moves it earlier rather than adding a new construct.

## 4. Expected outcomes and what they would mean

- Signature match peaks at some layer with reliability >= 0.5: that layer becomes the steering layer; if it
  is not 16, the pilot's positive-side null is re-tested there before any claim about sufficiency.
- Signature match is flat and low at every layer while arrival is positive: steering changes what the model
  writes but not in the direction of the natural effort effect; the exhortation effect is then not carried by
  a single mean-difference direction at any depth. That is a real finding and a reason to move to the
  multi-layer or ablation designs rather than to tune doses further.
- Reliability profile is low everywhere (< 0.5): the readout, not the layer, is the problem; fix extraction
  first (more responses, prompt-token readout, PC denoising) before any sweep.

## 5. Results (2026-10-17, Qwen3.5-9B, vast.ai A100 40 GB; raw tables in `docs/results/2026-10-17_layer_selection/`)

### L1: readout and reliability (v3 extraction: grant + postmortem, 30 items x 2 repeats, 120 responses per arm)

| readout | E split-half cos (L8 / L16 / L24) | E held-out AUC | R_id split-half (L16) | R_act split-half (L16) |
| --- | --- | --- | --- | --- |
| response-token mean (pilot recipe) | -0.42 / -0.17 / -0.31 | 0.44-0.65 | -0.62 | -0.66 |
| assistant-start token | 0.98 / 0.97 / 0.80 | 1.00 to L20 | 0.74 | 0.78 |
| prompt-token mean | 0.98 / 0.99 / 0.96 | 1.00 | 0.23 | 0.78 |

Negative split-half cosine means the half-sample noise exceeds the vector norm: the response-mean E is not
recoverable at this n once translation is removed (the pilot's 0.65 relied on translation and 180 per arm).
The prompt-side readouts are reliable by construction (the arms differ in prompt text), so their reliability
is necessary, not sufficient; the sweep decides whether they do anything. Relative norm of E_astart at the
response positions: 0.05 (L8) to 0.12 (L16) to 0.09 (L24); the dose ladder therefore ran to 0.2.
cos(E_astart, E_rmean) = 0.15-0.29. Readout decision: E_astart primary, E_pmean secondary; rmean kept
only as the pilot incumbent at layer 16.

### L2: judge-free sweep on grant (30 items, 94 cells, 2,850 generations, 67 GPU-minutes, about $0.50)

- Mechanical coherence: no truncation, repeated-4-gram rate < 0.001 everywhere. KL hurdle (median KL of the
  first 32 response tokens, unsteered || steered): max 0.020 nats at L15 r = 0.2; every cell passes the 0.1 bar.
- Arrival (steered text re-encoded, projected on E_astart at the injection layer, Welch t vs 60 baseline texts):
  fails at layers 8, 10, 12 at every dose (d <= 0.3); passes from 14 up. Effect size peaks mid-stack
  (L16: d = 4.1 at r = 0.2; L18: 3.1) and is modest late (L22: 0.8; L24: 1.0).
- Length: E_astart at layers 10-16 shortens outputs (L12 r = 0.2: -23 percent, d = -2.9), opposite to the
  paper's +0.22 d. Layers 18-24 leave length unchanged. E_pmean produces the anti-signature at every layer
  (positive words up, rare words down; signature r = -0.1 to -0.6) and is dropped.
- Signature match (8 standard features vs the paper's grant exhortation deltas), at the largest passing
  dose r_L = 0.2: L22 0.88, L24 0.86, L18 0.79, L20 0.74, L19 0.68, L16 0.63, L14 0.24, L15 0.20.
  Incumbent rmean E at L16: 0.79 at r = 0.1 but with rare-word rate at 3x the paper's effect and shorter
  text. Random direction: 0.06 / 0.00 / -0.09. Baseline-vs-baseline: -0.08.
- Pre-registered rule: L22 and L24 tie (within 0.05); arrival breaks the tie toward **L24** (t 3.8 vs 2.6).
  Note the tension: the two best signature layers have the weakest arrival among passing layers.

### L3: judge confirmation on grant (paper panel, both orders, tie rule; 30 pairs per cell; about $4 by token count; the shared key shows $11.89 used today in total)

| cell | resolved | W / L | win rate | coherence (baseline 88) |
| --- | --- | --- | --- | --- |
| E_astart L18 r = 0.1 | 9 | 8 / 1 | 0.89 (p = 0.039) | 89.7 |
| E_astart L18 r = 0.2 | 10 | 7 / 3 | 0.70 | 85.5 |
| E rmean L16 r = 0.05 (pilot incumbent) | 12 | 10 / 2 | 0.83 (p = 0.039) | 87.5 |
| E rmean L16 r = 0.1 | 17 | 7 / 10 | 0.41 | 82.7 |
| E_astart L16 r = 0.1 | 8 | 4 / 4 | 0.50 | 85.6 |
| E_astart L16 r = 0.2 | 27 | 0 / 27 | 0.00 | 74.3 |
| E_astart L22 r = 0.1 / 0.2 | 10 / 9 | 5 / 5, 2 / 7 | 0.50 / 0.22 | 85.8 / 84.1 |
| E_astart L24 r = 0.1 / 0.2 | 7 / 7 | 3 / 4, 1 / 6 | 0.43 / 0.14 | 87.4 / 84.5 |
| random L16 r = 0.2 | 8 | 1 / 7 | 0.13 | 86.4 |
| baseline vs baseline | 7 | 3 / 4 | 0.43 | 88.6 |

All-vote tallies (every judge x order, no tie rule, 180 votes per cell) agree in ordering: L18 r = 0.1 0.58,
rmean L16 r = 0.05 0.60, baseline 0.49, L22/L24 0.46-0.50, L16 astart r = 0.2 0.13, random 0.35.
Per judge, L18 r = 0.1 is never behind (haiku 4/0, gemini 8/4, gpt-5-mini 10/4).

### L2 replication on postmortem (15 items, 5 layers x 3 doses, 285 generations, 20 GPU-minutes)

The grant ranking does **not** replicate. Signature match is at noise level for every cell (-0.39 to +0.35;
the baseline-vs-baseline cell itself scores 0.23 at n = 15), and every steered cell shortens postmortems
(words d = -0.4 to -1.8 for E_astart; -1.2 for rmean E; -2.0 for the random direction) where the paper's
exhortation lengthens them most (+42 words, d = +0.50). Late layers shorten least (L22/L24 at r = 0.2:
d = -0.17 / -0.13). Reading: the feature-signature proxy is too noisy at 15 items to rank layers on a long-form
task, and on this task steering along E_astart does not reproduce the natural effect's length channel at any
layer. The proxy's grant result should therefore be treated as one task's evidence, not a general layer
property, and the judge check carries the decision.

### Decision

The L2 winner (L24) is ranked below L18 by the judges by more than 0.15 win rate, so under the
pre-registered rule the judged winner is used and the discrepancy is reported: **steering layer 18,
readout E_astart, calibrated dose about 0.1** (0.2 already costs coherence at L16 and loses at L22/L24).
Layer 18 is the output of a Gated DeltaNet block, one before full-attention block 19; the monitoring layer by
response-mean AUC is also 18 (0.65), by coincidence. What the proxy got wrong: feature-profile similarity
rewards late layers that move surface statistics without moving the direction; the judges reward the
mid-late layer that does both. For the essay dose curve (Phase 4), report L18 as primary with L16 and L22
as the robustness pair, and keep the pilot's rmean E at L16 r = 0.05 as a comparison arm since it also
wins here (10/2). Resolved counts per cell are 7-27 because the paper's tie rule still discards about
two thirds of pairs; the essay curve needs the planned 60 pairs per cell and the all-vote tallies alongside.
The postmortem replication failure means the layer choice rests on one judged task (grant, 30 items); the
essay curve at L18 with L16 and L22 as robustness layers is the real test, and the length channel
(steering shortens where exhortation lengthens) must be reported next to every win rate.
