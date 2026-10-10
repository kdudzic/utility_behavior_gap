# Steering-vector literature notes (for the extension's recipe choices)

Compiled 2026-10-10 from the PDFs in `academic_resources/`. Numbers quoted from the papers.
Used to justify the choices in `../PROPOSAL.md` Sections 4-6.

## Per-paper recipe facts

### CAA (Panickssery et al. 2024, 2312.06681)
- Vector: mean difference over hundreds of A/B contrast pairs at the answer-letter token position. 290-1000 pairs per behavior.
- Layer: sweep with multiplier ±1 on held-out MC; best layer 13/32 (Llama-2-7B-chat), 14-15 (13B).
- Application: single layer, all positions after the instruction, multiplier ±1 (MC) or ±2 (open-ended). |m| capped at 2 because open-ended text degrades.
- Controls: MMLU as A/B (0.63 → 0.57-0.65 at m=±1); GPT-4 0-10 rater on 50 prompts.
- Lesson: the vector doubles as a per-token monitor (dot product). Norms not normalized across layers. CAA refusal vector works in MC but not reliably in long-form (per Arditi).
- Relevant: has "Myopic Reward" and "Survival Instinct" vectors; steering stacks on system prompts.

### Refusal direction (Arditi et al. 2024, 2406.11717)
- Vector: diff-in-means harmful vs harmless (128 each), candidates over every layer × post-instruction token position.
- Selection: minimize bypass score subject to induce score > 0, KL at last token < 0.1 on harmless, layer < 0.8L (avoid unembedding-suppression directions). Selected layers ≈ 0.4-0.6 depth.
- Application: addition at one layer, all positions (induce); directional ablation x ← x − r̂r̂ᵀx at every layer, attention + MLP outputs, all positions (bypass); equivalent to weight orthogonalization.
- Key number: negative addition raises on-distribution CE (0.441) far more than ablation (0.213) vs baseline 0.195. Ablation is the surgical removal.
- Controls: MMLU/ARC/GSM8K/TruthfulQA/WinoGrande via LM Eval Harness; CE on Pile/Alpaca/self-generations.
- Compute: ≤14B on one 48 GB A6000; direction selection ~5 min.

### Persona Vectors (Chen et al. 2025, 2507.21509)
- Automated pipeline: trait description → 5 contrastive system-prompt pairs + 40 questions + judge rubric (Claude 3.7). 10 rollouts per question per prompt; responses filtered by trait judge.
- Vector: diff of mean residual activations averaged over response tokens. App. A.3: response-average beats prompt-average and prompt-last-token at matched steering norm.
- Layer: steering-efficacy sweep at fixed coefficient; Qwen2.5-7B layer 20 (evil/sycophancy), 16 (hallucination); Llama-3.1-8B layer 16.
- Application: h ← h + αv at one layer at each decoding step; α 0.5-2.5 (Qwen), 0.4-1.2 (Llama). Multi-layer variant with incremental vectors preserves MMLU better.
- Measurement: GPT-4.1-mini 0-100 trait score (94.7% human agreement); coherence 0-100, all reported results coherence > 75 (> 80 for prompt comparisons); MMLU tracked next to every curve.
- Monitoring: project last prompt token; projection-difference (vs natural response) beats raw projection. Between-condition r 0.75-0.83, within-condition r 0.25-0.81.
- Lessons: cross-trait specificity matrix (own r 0.76-0.97 vs cross 0.34-0.86); persona vectors moderately correlated (cos 0.2-0.6); SAE decomposition shows "trait" vectors bundle content and style; sycophancy trait samples dominated by roleplay/persona requests.

### Emotion Concepts (Sofroniew et al. 2026, 2604.07729, Claude Sonnet 4.5)
- Vector: 171 emotions, ~1200 stories each with the emotion word banned; mean over tokens from token 50; one-vs-rest mean centering; project out top PCs (50% variance) of neutral dialogues.
- Layer: ~2/3 depth for steering; earlier layers encode present-content connotation, later layers upcoming-token emotion.
- Dose: fraction of mean residual norm; 0.05-0.1 for agentic behavior, 0.5 for token-level preference.
- Findings: desperate +0.05 raises blackmail 22% → 72%; calm +0.05 → 0%; reward hacking 5% → 70% across −0.1…+0.1; anger non-monotonic (peak +0.025).
- Lessons: steering can change behavior with no textual trace (desperate-steered hacking looks calm) so text judges can miss effects; "deflection" vectors fire without driving behavior (monitoring ≠ causation); emotion vectors are character simulation yet load-bearing.
- Relevant: "desperate" fires on token-budget pressure and repeated failure; positive valence shifts stated preferences and sycophancy.

### Subjective experience / roleplay features (Berg et al. 2025, 2510.24797)
- Uses Goodfire SAE features labelled deception/roleplay on Llama-3.3-70B, set in [−0.6, +0.6].
- Suppressing roleplay/deception → 96% experience affirmation; amplifying → 16%; TruthfulQA truthfulness 0.44 vs 0.20.
- Lesson: "steer the roleplay feature and see what happens" needs condition-specific and out-of-domain controls; without base-model comparison one cannot separate filter relaxation from endogenous state. Cautionary template for any inference that a baseline behavior "is roleplay".

### Pain Axis (Tagliabue, Dung & Berg 2026, 2609.16247)
- Vector: denoised diff-in-means, pain sentences vs pooled matched controls (fear, negative emotion, world state, bodily sensation, neutral); project out PCs (50% control variance); final-token and mean-token readouts; layer by K-fold projection AUC (0.91-1.00).
- Crucial: best monitoring layer is too deep to steer (vector/residual ≈ 0.10); inject earlier where ratio ≈ 0.6.
- Dose ladder [−2,−1,0,+0.5,+1,+1.5,+2,+3]; behavioral window gate-like (0.5× nothing, 1× effect, 1.5× position-dependent chaos).
- Controls: 10 random matched-norm directions (random alone raises harmful choices to ~15%, baseline 0-4%); sibling vectors (fear inert, sadness a rescaled copy); PopQA 138 vs 137/200 (capability intact); label-wording swaps; natural elicitation activates probe but 0/560 behavior.
- 25 open models 2B-72B; ablation behaviorally null in 24/25.
- Relevant: a 10-option choice battery including effort, sycophancy, deception was unchanged under pain steering; "help user at cost to self" rose under every steering incl. random (generic-perturbation artefact).

### Hidden Valence (Kaiser & Berg 2026, 2609.35591)
- Vector: 56 passages × 4 positive and 4 negative states, 96 neutral; mean residual at the middle layer; v = (I − UᵀU)(h̄₊ − h̄₋) with U = first 10 neutral PCs. No layer search.
- Dose: d·ρ·R with R = RMS residual norm on neutral text; ρ per model from two hurdles (coherence heuristic ≥ 75% pass; "arrival": re-encoding steered text shifts projection |t| ≥ 2). ρ = 0.30 Qwen/OLMo, 0.15 Gemma, 0.60-0.70 Llama/Mistral.
- Controls: 8-24 orthogonal Gaussian random directions (centre near zero); three orthogonal concept directions (indoor/outdoor etc.) give smaller or sign-symmetric effects. Signed dose-response = concept-specific; sign-symmetric = perturbation.
- Separates text channel (model reads its own steered words) from hidden KV-cache channel.
- Coupling of valence to choice appears after SFT/DPO while the direction itself is constant across checkpoints (cos > 0.995).

## Converged 2026 recipe (what the proposal adopts)

1. Many diverse contrast items generated by a frontier model, concept word not required in text; pooled or matched negatives.
2. Response-token mean readout for steering vectors; last-prompt-token for monitoring.
3. Diff of means; optional denoising by projecting out neutral-corpus PCs; sibling and random vectors by the identical recipe.
4. Layer in the 0.3-0.7 depth band chosen by steering efficacy at fixed relative dose with a coherence floor; monitoring layer chosen separately by held-out AUC.
5. Dose as a fraction of residual norm; calibrate per model with a coherence hurdle; report full signed dose curves; expect narrow windows and non-monotonicity.
6. Behavioral readouts over self-report; validated LLM judges; capability panel and coherence next to every curve.
7. Ablation (projection-out) for necessity; negative addition only for signed dose curves.
8. Specificity: random matched-norm floors, sibling-vector profile comparison, signed vs sign-symmetric, capability invariance, monitoring-vs-causation kept as separate channels, label/position counterbalancing.
