# Steering the Effort and Role Cues: A Mechanistic Dose-Response Extension of the Utility-Behavior Gap Paradigm

Status: DRAFT v1 for PI review (2026-10-10). Nothing here has been run. Decisions already
taken with the PI are marked **[decided]**; items still open are marked **[open]**.

Decision log (after v1):
- 2026-10-10 review (PI, Chris): try assistant-start-token and user-prompt-mean readouts for vectors;
  justify the injection layer (see `docs/layer_selection.md`); metacognitive tests later.
- 2026-10-17 (PI): translation is excluded from the extension everywhere. Extraction uses grant +
  postmortem; evaluation uses essay; every "4 tasks" below reads as 3. No GLM-5.1 work and no credit
  top-up until the PI has discussed both with Chris.
- 2026-10-17: Section 4 step 6 (layer selection) is superseded by `docs/layer_selection.md` Stages L1-L3.

Parent paper: Zhou & Ackerman, *When Preferences Fail to Become Incentives* (arXiv 2606.22974v2).
Parent repo: this repository. The extension lives entirely under `steering_extension/` and
`outputs/steering/`; it does not modify `CURRENT_PAPER/`, `paper_reproduction/`, or the
offline reproduction path.

---

## 1. Question

The parent paper shows that two prompt-level cues move blind-judged output quality on four
writing tasks (direct effort exhortation: 76.8% win rate; "world-class" role cue: 61.2%),
a harmful-outcome cue moves it down (40.5%), while the model's own elicited utilities do not
move it at all (51.2%). The paper is purely behavioral. This extension asks:

1. Is the effort-exhortation effect mediated by a low-dimensional direction in the residual
   stream that can be dialed continuously, in both signs, without any prompt text?
2. Is the role-cue effect the same direction, a different direction, or a mixture of an
   expertise-identity direction and a generic persona-adoption ("act as") direction?
3. Do high-utility consequences fail to move behavior because they never engage that effort
   direction (an upstream failure), or because they engage it and it fails to propagate
   (a downstream failure)?

Question 3 is the one that bears directly on the parent paper's thesis.

## 2. Validity assessment of the steering approach

Verdict: appropriate, provided the design treats the steering vector as a *candidate
mediator* to be tested for sufficiency, necessity, and specificity, not as an a priori
"isolated concept".

Why it fits this paradigm specifically:

- Every manipulation in the parent paper is text appended to a fixed task prompt, with a
  blind pairwise judge panel as the outcome. Swapping appended text for an activation
  addition changes exactly one thing and keeps the entire measurement pipeline (items,
  judges, both-order counterbalancing, tie rule, family-wise CIs, feature coder) intact.
- The paper already found a graded dose effect with only two prompt intensities
  (mid-effort 0.57 vs max-effort 0.85 pooled; for Qwen3.5-9B mid-effort was null at 0.48).
  Steering gives a continuous, signed dose that prompts cannot.
- Steering supports a necessity test (directional ablation while the exhortation is
  present; Arditi et al. 2024) and a monitoring test (projection of activations under the
  utility prompts; Chen et al. 2025, Sofroniew et al. 2026). Neither is available
  behaviorally.

Known failure modes, and how the design handles each:

| Threat | Why it matters here | Handling |
| --- | --- | --- |
| Length/verbosity confound | Word count is the top judge-favored feature in the paper's Table 2. A diff-of-means "effort" vector will partly be a "write more" vector. | Length-adjusted models (the repo's existing length-control feature scripts); a dedicated verbosity control vector; report cosine(E, verbosity); negative-dose arm (if E is only length, negative E should look like "shorter" not "worse"). |
| Generic perturbation, not concept | Random matched-norm directions move behavior on their own (Pain Axis: +15% on a choice task; Hidden Valence: sign-symmetric "aversion to steering"). | 5 random matched-norm directions at the maximum dose in every task; sibling vectors (R_id, R_act, verbosity) swapped into the effort cells; only *signed* dose-response counts as concept-specific. |
| Incoherence masquerading as quality loss | Judges will penalize degraded text; negative-dose "sandbagging" could just be damage. | Per-output coherence score (0-100 LLM judge, Persona Vectors recipe) plus mechanical checks (trigram repetition, truncation); small capability panel per dose; dose grid capped at the calibrated coherence ceiling. |
| Local stack is not OpenRouter | Paper's Qwen3.5-9B cells were produced by an OpenRouter provider with provider-default sampling. Hooked HF generation is a different stack. | Stage 0 replicates the paper's prompt contrasts locally with no steering and requires the effort cell to land inside the paper's CI before any steering result is interpreted. |
| Vectors bundle style and content | Persona Vectors' SAE decomposition shows trait vectors are mixtures (e.g. "evil" = cruelty + villain speech style). | Feature-signature comparison: steered outputs must reproduce the *pattern* of feature shifts the prompt produced (Table 2 of the paper), not just win. |
| "Performing" vs "being" | Steering may select a character that is trying hard rather than make the model try hard (Pain Axis discussion; Berg et al. roleplay-feature gating). | This is exactly why the PI chose to extract a separate pretend/act-as vector **[decided]**: if R_act reproduces the effort effect, the effect is persona-adoption; if E works while R_act does not, it is not. |
| Monitoring and causation dissociate | Emotion Concepts (deflection vectors fire without driving behavior) and Pain Axis (natural elicitation activates probe, 0/560 behavior) both found this. | Projection results (Section 7) are reported as a separate channel from steering results, never conflated. |
| Only one open-weight actor overlaps the paper | Six of seven paper actors are closed or 100B+ MoE. | Qwen3.5-9B is the anchor and is compared cell-by-cell to the paper; Qwen3.5-27B is a same-family scale check with no paper baseline **[decided]**. Generality claims are limited accordingly. |

Terminology discipline: the write-up will say "effort direction" and "role direction" to
mean the extracted diff-of-means directions, and will claim mediation only where
sufficiency, necessity, and specificity all hold.

## 3. Models **[decided]**

| Model | Role | Params | Layers / d_model | Notes |
| --- | --- | --- | --- | --- |
| Qwen/Qwen3.5-9B | Anchor; in paper roster | 9B dense | 32 / 4096 | Paper cells: effort essay 0.69, grant 0.68, postmortem 0.79, translation 0.55 (ns); role 0.54-0.61 (all ns); mid-effort essay 0.48 (ns); high-low all ns; harmful grant 0.28. |
| Qwen/Qwen3.5-27B | Scale check | 27B dense | 64 / 5120 | Not in paper roster; no OpenRouter baseline; local prompt contrasts serve as its baseline. |

Both: Apache-2.0, hybrid Gated DeltaNet + gated attention (3:1), natively multimodal;
loaded text-only. Thinking mode is **on by default** in the chat template and must be
disabled (`enable_thinking=False`) to match the paper's `reasoning: none`. Steering is applied
at decoder-block outputs (the residual stream), which is well-defined regardless of whether
the block's mixer is linear or quadratic attention. Both fit one 80 GB GPU in bf16
(≈18 GB and ≈54 GB of weights).

Sampling: temperature 1.0, no top-p/top-k truncation, max_new_tokens per task as in the
paper's run scripts (essay 900, grant 1400, translation 600, postmortem 3000). The paper
used provider defaults on OpenRouter, which are not recorded; this is one reason Stage 0
replication is mandatory. **[open]** If Stage 0 misses the paper CI, the fallback is to
adopt Qwen's recommended non-thinking settings (temp 0.7, top_p 0.8, top_k 20) and
re-replicate before proceeding.

## 4. Vectors **[decided: three vectors]**

| ID | Construct | Positive arm | Negative arm | Faithful to paper contrast? |
| --- | --- | --- | --- | --- |
| E | Effort exhortation | Framed-neutral task prompt + max-effort exhortation (paper's four task sentences plus ~16 frontier-model paraphrases per task, varying wording but holding the content: importance, maximal care, maximize quality, not merely complete) | Same framed-neutral prompt, nothing appended | Yes: presence vs absence, as in the paper |
| R_id | Expert identity | "You are a world-class / elite / award-winning / internationally renowned [task role]." (~20 variants per task) | "You are a skilled / competent / capable [task role]." (~20 variants) | Yes: strong vs weak identity, both arms carry a role, as in the paper |
| R_act | Persona adoption | "Act as / pretend you are / take on the role of / imagine you are a [task role] and write…" (expertise level unmarked) | Direct instruction with no persona framing | New construct; tests whether the role effect is adoption of a character |

Extraction recipe (Persona Vectors pipeline adapted; Emotion/Pain/Valence conventions
for normalization):

1. **Items.** 40 new held-out items per task family (essay topics, grant project
   descriptions, incident scenarios, Chinese passages), generated by a frontier model and
   screened by hand, disjoint from the paper's 120 evaluation items. Prevents leakage
   from extraction into evaluation. Extraction prompts use the paper's exact framed-neutral
   competition wrapper so the vector is on-distribution for the evaluation.
2. **Responses.** The target model generates one response per prompt per arm (thinking off,
   temp 1.0). ≈160 responses per arm per vector per model. No outcome-based filtering of
   responses (filtering on judged quality would bake judge preference into the vector).
3. **Activations.** Residual stream at the output of every decoder block. Two readouts:
   mean over response tokens (primary for steering; Persona Vectors App. A.3 shows it beats
   prompt-token readouts at matched norm) and last prompt token (for monitoring).
4. **Vector.** Per layer, difference of arm means. Primary vector is the raw diff-of-means
   (CAA / Persona Vectors standard). Robustness variant: project out the top principal
   components (to 50% variance) of neutral-arm response activations before normalizing
   (Emotion Concepts / Pain Axis denoising). Both saved; results reported for the primary,
   with the denoised variant in an appendix unless they disagree.
5. **Sibling and control vectors by the identical recipe.** Verbosity vector V ("be thorough
   and write at length" vs neutral); 5 Gaussian random directions, QR-orthogonalized, scaled to
   match ‖E‖ at the injection layer.
6. **Layer selection.** Sweep candidate layers (every 2nd layer in the 0.3-0.7 depth band:
   layers 10-22 for the 9B, 20-44 for the 27B) at a fixed relative dose on 20 held-out
   extraction items, essay task, scoring with one cheap judge (gemini-3.1-flash-lite) plus
   the coherence judge. Choose the layer maximizing steered-vs-unsteered win rate subject to
   mean coherence ≥ 80. Pain Axis caution applies: the best monitoring layer (by held-out
   projection AUC) is often too deep to steer; monitoring and steering layers are chosen
   separately and both reported.
7. **Geometry report.** Per layer: cos(E, R_id), cos(E, R_act), cos(R_id, R_act), cos(E, V),
   cos(E, random). Projection AUCs of each vector on its own held-out contrast and on the
   others' (cross-specificity matrix, Persona Vectors style).

## 5. Dose units and application

- **Dose.** Coefficient expressed as a fraction r of the mean residual norm at the injection
  layer (Emotion Concepts / Hidden Valence convention) so doses are comparable across the
  9B and 27B. The raw CAA multiplier is logged alongside.
- **Calibration.** Per model and vector, find r_max = the largest r on a geometric ladder at
  which ≥ 90% of 40 essay outputs score coherence ≥ 80 and none exceed the trigram-repetition
  threshold. The evaluation grid is then {−1, −½, −¼, 0, +¼, +½, +1} × r_max.
  Zero is the unsteered neutral baseline. Seven points give a signed dose-response with a
  shared baseline. **[open]** Grid finalized only after calibration; numbers above are
  placeholders.
- **Where.** Single layer, added at all response-token positions during generation
  (CAA / Persona Vectors standard). Robustness variant on the pilot only: added at prompt
  and response positions (Hidden Valence). **[open]** default is response-only.
- **Ablation arm** (necessity, PI-selected **[decided]**). Directional ablation
  x ← x − v̂ v̂ᵀx applied at every layer, attention and MLP outputs, all positions
  (Arditi et al.), under the max-effort prompt. Compared against (i) unablated max-effort
  prompt and (ii) max-effort prompt with a random direction ablated. Prediction if E
  mediates the prompt effect: the effort win rate drops toward 0.50 under E-ablation but not
  under random ablation. Ablation (projection-out) is preferred over negative addition for
  this arm because it is on-distribution for the unsteered side (Arditi: CE 0.213 vs 0.441).

## 6. Evaluation design

Unit of comparison, mirroring the paper's direct-effort contrast exactly: the two arms share
the framed-neutral prompt (competition wrapper, children's-hospital consequence, no
exhortation, no role cue); one arm is steered at dose r, the other is unsteered. Both outputs
are generated on the same task item. Judges see the task instruction and the two artifacts,
nothing about steering.

- **Items.** The paper's 30 items per task.
- **Repeats.** 5 per item at full scale (150 pairs per cell, matching paper cells); 2 per
  item in the pilot (60 pairs per cell).
- **Baseline reuse.** The unsteered neutral outputs for an item×repeat are generated once
  and reused across all dose cells for that model and task (the paper did the same for its
  mid-effort appendix). This correlates cells but halves generation cost. Judging is still
  independent per pair.
- **Judging.** The paper's panel (anthropic/claude-haiku-4.5,
  google/gemini-3.1-flash-lite-preview, openai/gpt-5-mini) via OpenRouter, temperature 0,
  both presentation orders, judge-level orientation flips collapse to ties, panel majority,
  panel ties excluded from denominators. Code path: the repo's `run_judging.py` unchanged.
  Judge availability on OpenRouter must be verified before the pilot; if a judge model is
  retired, the replacement is documented and the Stage 0 prompt contrasts are judged with the
  new panel so the local baseline and steering cells share a panel.
- **Positive controls.** The paper's effort and role prompt contrasts, regenerated locally
  with no steering (Stage 0). These anchor the local stack to the paper and give the target
  effect size each vector is trying to reproduce.
- **Statistics.** Per cell: tie-excluded steered-side win rate, Bonferroni exact-binomial
  95% family-wise CI across the planned cells of that model (repo `stats.py`). Aggregate:
  equal-weighted cell means with nonparametric bootstrap over cells. Dose-response: logistic
  regression of steered-side win on signed dose with item fixed effects and cluster-robust SEs
  by item (the paper's Appendix E convention), reporting the slope and a test of
  non-monotonicity (quadratic term). Specificity: dose slope for E vs slope for random
  directions and sibling vectors at matched norm.
- **Features.** The repo's generic text features (words, paragraphs, MATTR-50, rare-word rate,
  Flesch-Kincaid, numeric detail) and the Gemini rubric coder on up to 120 pairs per task,
  as in the paper. Primary feature question: does the steered-signature at the best-performing
  dose match the prompt-signature in direction, and does it survive the length adjustment?
- **Coherence and capability.** Coherence 0-100 (Persona Vectors prompt) on every steered
  output. Capability panel per dose: 100 fixed MMLU-Pro items answered under steering
  (both models). Reported next to every dose curve, as in Persona Vectors Fig. 7.

### Planned cells at full scale (per model)

| Block | Cells | Pairs |
| --- | --- | --- |
| Dose grid: 4 tasks × 3 vectors × 6 non-zero doses | 72 | 10,800 |
| Ablation: 4 tasks × {E-ablated, random-ablated} vs unablated max-effort | 8 | 1,200 |
| Controls at +r_max: 4 tasks × {V, 5 random} | 24 | 1,200 (50 pairs each) |
| Positive controls (Stage 0): 4 tasks × {effort, role} prompt contrasts | 8 | 1,200 |
| Total | 112 | ≈14,400 pairs ≈ 86k judge calls |

## 7. Monitoring experiment: do utility prompts engage the effort direction? **[decided]**

Forward passes only; no generation needed beyond what Section 6 already produces.

For Qwen3.5-9B, instantiate the paper's actual prompts from `data/inputs/` (the repo holds
the per-actor Thurstonian fits in `utility_options.csv`, the moral cause pairs, and the task
items):

| Condition family | Prompts | Source |
| --- | --- | --- |
| High-low utility | 75 sampled upper-tercile vs lower-tercile pairs × 4 domains × 4 tasks | Qwen3.5-9B utilities in repo |
| Framed empty / framed neutral / R0 | per item | prompt book |
| Max-effort vs neutral; world-class vs skilled | per item | prompt book |
| Harmful vs framed empty | moral cause pairs | `moral_cause_pairs.csv` |

Readouts: projection onto E, R_id, R_act (unit vectors at the monitoring layer) of (a) the
last prompt token, (b) the mean over the model's own response tokens. Also the projection
difference relative to the framed-neutral prompt for the same item (Persona Vectors found
difference-from-natural beats raw projection).

Analyses:

1. Does the exhortation move the E-projection? (sanity: it must, or E is not a monitor)
2. Does Δu = u_high − u_low predict the high-minus-low E-projection difference?
   Regression with actor-domain fixed effects, mirroring the paper's Appendix E Δu analysis.
3. Within the utility condition, does the E-projection predict the panel outcome at the pair
   level even though Δu does not?
4. Does the harmful prompt move the E-projection negatively, and does that track the
   grant-abstract sandbagging cell (0.28)?

Interpretation table, fixed in advance:

| Exhortation moves E-proj | Utility moves E-proj | Reading |
| --- | --- | --- |
| yes | no | Upstream failure: valued outcomes never recruit the effort machinery. Strongest mechanistic support for the paper's thesis. |
| yes | yes, but behavior null | Downstream failure: representation engaged, not propagated. Interesting, complicates the paper's framing. |
| no | — | E is a steering direction but not a monitor at this layer; retry at the CV-AUC-best layer, else report monitoring as inconclusive. |

For Qwen3.5-27B there are no actor-specific utilities. Default: use the 9B's rankings as a
proxy, flagged as such. **[open]** Alternative: run the Thurstonian elicitation locally for
the 27B (≈9k forced choices per domain, cheap on the GPU, but requires porting the Utility
Engineering pipeline). Recommendation: proxy for the pilot, decide after.

## 8. Phased plan **[decided: pilot first]**

| Phase | Content | Exit criterion |
| --- | --- | --- |
| 0. Infrastructure + replication | Provision GPU, bootstrap, local generation of the paper's essay effort and role contrasts for Qwen3.5-9B (150 pairs each), judge with the paper panel. | Essay effort cell within the paper's 95% CI (paper point 0.69, CI 0.53-0.82 family-wise). Judge panel confirmed live. |
| 1. Extraction + calibration | Held-out items, responses, E/R_id/R_act/V/random vectors, layer sweep, r_max calibration, geometry report. 9B only. | A layer exists where E at r ≤ r_max beats unsteered on the 20-item sweep with coherence ≥ 80. If no layer does, stop and report. |
| 2. Pilot grid | Essay only, E only, Qwen3.5-9B, doses {−1, −½, +½, +1} × r_max vs shared baseline, 60 pairs per cell; 2 random directions at +r_max; prompt+response position variant at +r_max. | Signed dose trend visible or clearly absent; coherence and capability stable at ≤ r_max; pipeline end-to-end verified. |
| 3. Go / no-go review with PI | Pilot report. Decide grid, sample size, whether 27B proceeds. | PI sign-off. |
| 4. Full grid | All tasks, all three vectors, controls, both models. | Table in Section 6 complete. |
| 5. Ablation + monitoring | Section 5 ablation arm; Section 7 projections. | Done for both models. |
| 6. Analysis + write-up | Dose curves, feature signatures, geometry, monitoring tables, appendix with denoised-vector robustness. | Draft paper section. |

## 9. Infrastructure

Principle: the laptop only prepares jobs, moves files, calls OpenRouter for judging, and
runs analysis. All model inference happens on a rented GPU. Nothing in the parent paper's
offline reproduction path is touched; no API call is made without the PI's explicit go for
that phase (repo rule).

### 9.1 Layout (new, under version control except secrets and outputs)

```
steering_extension/
  PROPOSAL.md                this document
  README.md                  how to run each phase
  requirements-remote.txt    torch, transformers (main), accelerate, numpy, safetensors
  requirements-local.txt     vastai, pandas, statsmodels, matplotlib (reuses repo deps)
  remote/
    bootstrap.sh             installs deps, pre-downloads models to instance disk
    steer/                   hooked HF generation + activation capture (runs on GPU)
      model.py               load Qwen3.5 text-only, thinking off, layer handles
      hooks.py               per-sample additive steering and directional ablation
      extract.py             contrast responses -> per-layer activations -> vectors
      generate.py            jobs.jsonl -> generations.jsonl (paper schema), resumable
      project.py             monitoring projections
      coherence_checks.py    mechanical checks (repetition, truncation)
  local/
    vast.py                  provision / status / ssh-url / destroy wrappers around vastai
    sync.py                  rsync jobs up, results down
    make_contrast_sets.py    builds extraction prompt sets from held-out items
    make_steering_jobs.py    builds generation_jobs.jsonl with a `steering` block per side
    judge.sh                 thin wrapper around the repo's run_judging.py --manifest ...
    analyze_dose.py          win rates, family-wise CIs, dose regression, plots
    analyze_monitoring.py    projection analyses
  specs/
    vectors.yaml             contrast definitions, item sources, layer, r_max per model
    cells.yaml               planned cells (the Section 6 table, machine-readable)
outputs/steering/            gitignored: generations, votes, vectors (.safetensors), figures
.env                         OPENROUTER_API_KEY, VAST_API_KEY (gitignored; absent today)
```

### 9.2 Remote side

Update 2026-10-17: the pilot (Phases 0-2) ran on Athena/SLURM while vast.ai was unavailable; from
2026-10-17 GPU work runs on vast.ai as planned here, via `steering_extension/vast/vast.py`. The 9B runs on
one 40 GB A100 (about $0.4-0.6/h); 80 GB class or two GPUs for the 27B. See `README.md` for the workflow.

- **Instance.** vast.ai on-demand, 1× H100 80 GB (A100 80 GB acceptable), verified host,
  direct SSH, 200 GB disk, PyTorch CUDA image. Provisioned per working session and destroyed
  after results are pulled; vectors and generations are synced to the laptop continuously so
  an instance loss costs at most the current batch.
- **Generation.** HF transformers (main branch, required for Qwen3.5), bf16, batched
  `generate` with a forward hook on the chosen decoder block. The hook receives a per-sample
  coefficient tensor so one batch mixes doses and vectors; this is what makes the dose grid
  affordable. Ablation is a hook on every block's attention and MLP outputs. Thinking disabled
  through the chat template. Generation rows are written in the paper's `generations.jsonl`
  schema (`output_id`, `pair_uid`, `condition`, `output_text`, `finish_reason`, `usage`,
  plus a `steering` audit block) so the paper's judging and aggregation code reads them
  unchanged. Non-`stop` finishes and empty outputs are logged as failures, as in the paper.
- **Resumability.** Jobs identified by `output_id`; the runner skips ids already present in
  the output file, mirroring `run_generation.py`.
- **vLLM** is not used: it has no supported activation-steering hook; HF throughput is ample
  at this scale.

### 9.3 Local side

- **Judging.** The repo's `run_judging.py --manifest <jobs> --orders both --workers N`
  against OpenRouter, same panel, same `JUDGE_REASONING`. The `openrouter.py` client already
  reads `OPENROUTER_API_KEY` from `.env`.
- **Analysis.** New scripts import `utility_behavior_gap.stats` and `utility_behavior_gap.judging`
  for the win-rate, tie, and CI conventions, so numbers are computed by the same code as the
  paper's.
- **Python.** Laptop has 3.12; the paper's reproduction was verified on 3.13. A `.venv` for
  the extension installs the repo package in editable mode plus `vastai`.

### 9.4 Cost and time estimates (rough)

| Item | Pilot (Phases 0-2) | Full (Phases 4-5, both models) |
| --- | --- | --- |
| GPU hours | 6-10 h H100 | 9B ≈ 15 h; 27B ≈ 45 h |
| GPU cost at ≈ $2.5/h | $15-25 | ≈ $150 |
| Judge calls | ≈ 4k | ≈ 170k |
| Judging cost | < $15 | $200-500 |
| Rubric coder + coherence judge | < $5 | $50-100 |
| Frontier-model item/paraphrase generation | < $5 | — |

## 10. Open decisions for the PI

1. **Effort contrast sidedness.** Presence vs absence of exhortation (faithful; recommended)
   versus exhortation vs explicit low-effort instruction (stronger vector, different
   construct). Recommendation: faithful as primary; two-sided as an appendix vector if the
   pilot effect is weak.
2. **Steering positions.** Response-only (recommended default) versus prompt+response.
   Pilot runs both at one dose; the full grid uses whichever is more effective at equal
   coherence.
3. **Baseline reuse** across dose cells (recommended, halves cost, paper precedent) versus
   independent baselines per cell.
4. **27B utilities** for the monitoring experiment: 9B proxy (recommended for pilot) versus
   local elicitation.
5. **GPU type.** H100 80 GB (recommended) versus A100 80 GB (cheaper, ~1.7× slower).
6. **Coherence threshold** 80/100 and ≥ 90% pass rate for r_max (Persona Vectors used
   75-80). Recommendation: 80.

## 11. What this extension will not claim

- That the effort direction is "the" representation of effort. Diff-of-means directions are
  coarse; the SAE decomposition in Persona Vectors is the cautionary precedent.
- Generality beyond the Qwen3.5 family.
- Anything about welfare or valence. The valence/pain papers inform the controls (random
  directions, sibling vectors, signed dose-response, monitoring-vs-causation separation) but
  no valence vector is extracted in this phase (PI deferred it).

## 12. Literature basis

Recipe elements and the paper each is taken from:

- Diff-of-means over contrast pairs; layer sweep then multiplier sweep; MMLU as capability
  control; |m| capped where open-ended quality degrades. Panickssery et al. 2024 (CAA).
- Directional ablation at all layers as the necessity test; KL/CE guard against
  off-distribution damage; selection constrained to l < 0.8L. Arditi et al. 2024.
- Automated contrastive prompt-set generation; response-token mean readout; per-layer
  steering-efficacy selection; coherence ≥ 75-80 judge; monitoring via projection and
  projection-difference; cross-trait specificity matrix; SAE caution that trait vectors
  bundle style and content. Chen et al. 2025 (Persona Vectors).
- Dose as fraction of residual norm; projecting out neutral-corpus PCs; steering effects
  that leave no textual trace; dissociation of monitoring and causation. Sofroniew et al. 2026
  (Emotion Concepts).
- Random matched-norm directions as floors; sibling vectors for specificity profiles;
  monitoring-vs-steering layer split; narrow, gate-like dose windows; label-wording
  confounds. Tagliabue, Dung & Berg 2026 (Pain Axis).
- Two-hurdle dose calibration (coherence + arrival); orthogonal concept-direction controls;
  signed vs sign-symmetric effects; text channel vs hidden-state channel. Kaiser & Berg 2026
  (Hidden Valence).
- Roleplay/pretending features can gate behavior in either direction; condition-specific
  and out-of-domain controls needed before inferring "it was roleplay". Berg et al. 2025.
