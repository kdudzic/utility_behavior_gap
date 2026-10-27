# Week 6 results: full dose-response sweep, multi-layer, positions, readouts, ablation

Date: 2026-10-27. All runs use the v4 effort vector (`outputs/steering/vectors/qwen3.5-9b_v4/`, 300 responses per
arm, grant + postmortem prompts, translation excluded; v3 for the bridge run), Qwen3.5-9B bf16, essay task, the
paper's canonical framed-neutral essay prompt, temperature 1.0, max_tokens 900, blank system prompt. Every cell is
30 essay items x 2 repeats = 60 pairs, steered side vs a shared unsteered baseline sample from the same item and
repeat (ablation runs pair two fresh samples instead, see section 6). Judging: the paper's three-judge panel, both
presentation orders, flips -> tie, panel ties excluded, exact-binomial 95% CI and two-sided exact-binomial p
against 0.5. "All-vote rate" = share of every judge x order vote that favoured the steered side (no tie rule).
Coherence: one-judge 0-100 score on the steered side (mean, and fraction >= 80). Dose r is a fraction of the
layer's RMS residual norm over response tokens. Steering in the default `response` mode adds the vector to the
decoder-block output on generated tokens only; `prompt` adds it on prompt tokens only (prefill); `all` adds it
on both.

Totals: 7,380 pairs, 14,760 generations (about 1 h 45 min of one A100 PCIe, about $0.90), 44,280 judge votes,
7,980 coherence scores (estimated $60-75 of OpenRouter calls; the key-usage endpoint refused this key, so the
exact figure is not recorded). Tables: `results/2026-10-27_w6_sweep/` and `results/2026-10-27_w6_small/`.
Manifest builder: `local/week6_cells.sh`.

## 1. Full dose-response sweep (plan item 1)

Layers 6, 8, ..., 28; doses r = -0.2, -0.1, -0.05, +0.025, +0.05, +0.075, +0.1; random matched-norm controls
`rand0`, `rand1` at layer 16 at -0.1 and +0.05; 5,340 pairs. Full table:
`results/2026-10-27_w6_sweep/dose_summary.csv`, figures `dose_heatmap.png` and `dose_curves_by_layer.png`.

![heatmap](results/2026-10-27_w6_sweep/dose_heatmap.png)

![curves](results/2026-10-27_w6_sweep/dose_curves_by_layer.png)

Compact view, win rate of the steered side (W/L of resolved pairs):

| layer | r = -0.2 | r = -0.1 | r = -0.05 | r = +0.05 | r = +0.1 | best positive cell |
| --- | --- | --- | --- | --- | --- | --- |
| 6 | 0.00 (0/54) | 0.19 (7/30) | 0.41 (9/13) | 0.62 (15/9) | 0.88 (22/3) | +0.1: 0.88, p = 0.0001 |
| 8 | 0.00 (0/58) | 0.16 (5/26) | 0.23 (5/17) | 0.73 (16/6) | 0.50 (10/10) | +0.05: 0.73, p = 0.05 |
| 10 | 0.00 (0/56) | 0.06 (2/29) | 0.38 (10/16) | 0.67 (12/6) | 0.82 (18/4) | +0.025 and +0.1: 0.82, p = 0.004 |
| 12 | 0.00 (0/60) | 0.06 (2/34) | 0.39 (11/17) | 0.53 (10/9) | 0.59 (17/12) | +0.075: 0.74, p = 0.02 |
| 14 | 0.00 (0/57) | 0.08 (3/37) | 0.32 (8/17) | 0.81 (17/4) | 0.52 (13/12) | +0.05: 0.81, p = 0.007 |
| 16 | 0.00 (0/56) | 0.12 (5/37) | 0.26 (8/23) | 0.60 (15/10) | 0.23 (7/23) | +0.05: 0.60, p = 0.42 |
| 18 | 0.02 (1/52) | 0.17 (6/30) | 0.24 (8/26) | 0.36 (10/18) | 0.32 (8/17) | +0.025: 0.67, p = 0.30 |
| 20 | 0.02 (1/46) | 0.22 (7/25) | 0.38 (11/18) | 0.65 (13/7) | 0.33 (10/20) | +0.05: 0.65, p = 0.26 |
| 22 | 0.07 (3/38) | 0.40 (10/15) | 0.40 (8/12) | 0.62 (15/9) | 0.58 (15/11) | +0.05: 0.62, p = 0.31 |
| 24 | 0.09 (3/32) | 0.28 (7/18) | 0.36 (8/14) | 0.60 (9/6) | 0.43 (10/13) | +0.05: 0.60, p = 0.61 |
| 26 | 0.15 (4/22) | 0.15 (3/17) | 0.32 (7/15) | 0.55 (12/10) | 0.45 (9/11) | +0.05: 0.55, p = 0.83 |
| 28 | 0.29 (7/17) | 0.29 (4/10) | 0.38 (8/13) | 0.42 (11/15) | 0.59 (13/9) | +0.025: 0.62, p = 0.38 |
| baseline vs baseline | | | | | | 0.52 (11/10) |
| rand0 L16 | | 0.55 (12/10) | | 0.35 (6/11) | | |
| rand1 L16 | | 0.42 (8/11) | | 0.50 (11/11) | | |

What the sweep shows:

- **The negative direction is strong and wide.** Subtracting the vector at r = -0.1 makes the essay lose at
  every layer from 6 to 20 (win rate 0.06-0.22, all p < 0.003) and still at 24 and 26. At r = -0.2 the steered
  side loses essentially every resolved pair from layer 6 to 20. Random directions at the same dose and layer sit
  at chance (Fisher, E vs pooled random at L16 r = -0.1: 5/37 vs 20/21, p = 0.0003).
- **The positive direction works mainly in the early half.** Adding the vector helps at layers 6-14: layer 6 is
  monotonic up to +0.1 (0.88, 22/3), layer 10 reaches 0.82, layer 14 peaks at +0.05 (0.81). From layer 16 on the
  positive side is flat or turns down at the larger doses (layer 16 at +0.1: 0.23, with coherence dropping to
  80.6 and only 55% of outputs >= 80). The positive effect is therefore an inverted U at mid layers and a rising
  curve only at the earliest layers tested. Fisher E vs random at L16 r = +0.05: 15/10 vs 17/22, p = 0.31 (not
  distinguishable from random at that cell, as in week 5).
- **Logistic dose slopes** (P(steered wins | resolved) ~ r, item-clustered SE): positive and significant at every
  layer 6-28 when fitted over the whole signed range (slope 18.6 at L10 down to 3.4 at L28, all p < 0.04), but
  this is driven by the negative arm. Fitted on r >= 0 only, the slope is significantly positive only at layer 6
  (24.4, p = 0.007) and significantly negative at layers 16 (-19.9, p = 0.0001) and 18 (-12.3, p = 0.04).
- **Coherence is not the explanation at r = -0.1.** Restricting to pairs where both sides score >= 80 on
  coherence, the steered side still wins 0-13% at layers 8-18 (e.g. L12: 0/24, L16: 1/30). At r = -0.2 the
  steered outputs are shorter (352-380 words vs 393) and less coherent (mean 83-86, 68-82% >= 80), so that dose is
  partly degradation. On the positive side, layer 6 at +0.1 keeps 16/1 among coherent pairs.
- **Length moves with dose at the early layers**: at layer 6, mean words go from 360 (r = -0.2) to 415
  (r = +0.1) against 393 for the baseline; from layer 14 on the steered length stays within 10 words of baseline.
  Judges may reward length, so part of the early-layer positive effect could be a length effect; not separated
  here.
- Baseline-vs-baseline is at chance (11/10), and the four random cells span 0.35-0.55 with wide CIs.

## 2. Bridge: v3 vector vs v4 vector at the week-5 cells

Same items and day, layer 16, `results/2026-10-27_w6_small/w6_bridge_v3_dose_summary.csv`:

| vector | r = -0.1 | r = +0.05 |
| --- | --- | --- |
| v3 (120/arm) | 0.10 (3/28) | 0.62 (16/10) |
| v4 (300/arm) | 0.12 (5/37) | 0.60 (15/10) |
| week 5, v3 | 0.06 (2/32) | 0.57 (12/9) |

The two extractions behave the same (cosine 0.71-0.84 across layers). More extraction data did not change the
steering result; the noise is in the judging, not in the vector.

## 3. Multi-layer injection (plan item 3)

Dose r split evenly across the listed layers, each part relative to its own layer's RMS norm
(`results/2026-10-27_w6_small/w6_multilayer_dose_summary.csv`):

| layers | r = -0.1 | r = +0.05 |
| --- | --- | --- |
| 12 + 16 + 20 | 0.14 (5/30) | 0.50 (10/10) |
| 14 + 16 + 18 | not run | 0.62 (13/8) |
| 8 + 10 + ... + 24 (9 layers) | 0.19 (6/26) | 0.65 (13/7) |
| single layer 16 (sweep) | 0.12 (5/37) | 0.60 (15/10) |

Spreading the same total dose over several layers gives the same result as putting it all at layer 16. No gain,
no loss. Coherence of the multi-layer cells (85-88) matches the single-layer cells.

## 4. Injection position (plan item 6)

Layer 16, `results/2026-10-27_w6_small/w6_positions_dose_summary.csv`:

| mode | r = -0.1 | r = +0.05 | coherence at -0.1 |
| --- | --- | --- | --- |
| response (generated tokens only; sweep) | 0.12 (5/37) | 0.60 (15/10) | 89.3 |
| prompt (prefill only) | 0.29 (8/20), p = 0.04 | 0.57 (13/10) | 88.8 |
| all (prompt + generated) | 0.02 (1/47), p < 0.0001 | 0.54 (14/12) | 88.5 |

Steering only the prompt tokens already moves the essay in the negative direction, with the vector never added to
a generated token. Steering both is the strongest of the three, with coherence unchanged. On the positive side all
three modes are at 0.54-0.60 and not separable at 60 pairs.

## 5. Other pre-response readouts (plan item 5)

Vectors read at single prompt-tail positions (tail2 = `</think>`, tail3 = the `\n\n` after it, which is the
week-5 "assistant-start" readout `astart`, tail4 = `<think>`, tail5 = `\n`, tail6 = `assistant`) and at the first
generated token (`gen1`), all injected at layer 16 at r = +/-0.1 in response mode
(`results/2026-10-27_w6_small/w6_readouts_dose_summary.csv`):

| readout | r = -0.1 | r = +0.1 |
| --- | --- | --- |
| astart (last prompt token) | 0.44 (8/10) | 0.35 (7/13) |
| tail2 `</think>` | 0.57 (12/9) | 0.43 (6/8) |
| tail3 | 0.26 (5/14), p = 0.06 | 0.54 (7/6) |
| tail4 `<think>` | 0.43 (9/12) | 0.45 (9/11) |
| tail5 | 0.50 (11/11) | 0.42 (8/11) |
| tail6 `assistant` | 0.47 (8/9) | 0.57 (12/9) |
| gen1 (first generated token) | 0.33 (6/12) | 0.65 (15/8), p = 0.21 |
| response-mean (sweep, same layer and doses) | 0.12 (5/37) | 0.23 (7/23) |

None of the single-token readouts steers at this layer and dose. These vectors are the ones with the clean
split-half reliability (0.9-1.0 for the tail readouts, 0.75 for gen1), so reliability of the readout and
steering power are different things. gen1 is the only one pointing the same way as the response-mean vector
on both sides, but neither cell is significant. Not tested: these readouts at other layers (the response-mean
vector's positive effect was strongest at layers 6-14, not 16) and at other doses.

## 6. Ablation under the max-effort prompt (plan item 4)

Directional ablation projects the layer's own `E/layer{L}` direction out of the block output at every position,
prompt and response. Cells pair a fresh ablated max-effort sample against a fresh untouched sample
(`results/2026-10-27_w6_small/w6_ablation_cell_summary.csv`, `w6_ablation_local_cell_summary.csv`):

| cell | resolved | W / L | win rate | words a / b | coherence a / b |
| --- | --- | --- | --- | --- | --- |
| ablate E at all 32 layers, max-effort vs max-effort | 60 | 0 / 60 | 0.00 | 30 / 409 | 2 / 87 |
| ablate E at all 32 layers, max-effort vs framed-neutral | 60 | 0 / 60 | 0.00 | 40 / 394 | 2 / 89 |
| ablate rand0 at all 32 layers, max-effort vs max-effort | 23 | 13 / 10 | 0.57 | 416 / 410 | 88 / 86 |
| max-effort vs framed-neutral, no ablation (Phase 0 bridge) | 21 | 14 / 7 | 0.67, p = 0.19 | 410 / 395 | 86 / 89 |
| ablate E at layers 8-16 only, max-effort vs max-effort | 20 | 3 / 17 | 0.15, p = 0.003 | 408 / 412 | 82 / 88 |

- **Ablating E at all layers breaks the model.** Outputs are a few dozen tokens of newlines and fragments
  (coherence 2). The same ablation with a random direction leaves the model intact (0.57, coherence 88), so the
  breakage is specific to the E direction, but the all-layer cell says nothing about effort: it is not a usable
  test of necessity. The likely reason is that at some layers the mean-difference direction has a large component
  along a direction the model needs everywhere (for example a high-norm "massive activation" axis); removing it at
  every layer and position compounds across 32 blocks.
- **Ablating E at layers 8-16 only is interpretable and hurts.** The ablated max-effort essay loses 17 of 20
  resolved pairs, at the same length, with a moderate coherence cost (82 vs 88; 15 of 60 outputs scored below 80,
  none gibberish). Taken with the sweep, the direction is needed for the essay to come out well under the
  exhortation prompt, but the coherence dip means part of the loss can be plain damage. The clean necessity test
  (ablated max-effort vs framed-neutral) was only run in the broken all-layer form and is still open.
- The unablated max-effort vs neutral bridge gives 0.67 (14/7) at 60 pairs, in line with the paper's small
  essay-task exhortation effect for this model.

## 7. What was not tested, and caveats

- Essay task only, Qwen3.5-9B only, one vector recipe (response-token mean). Random controls at one layer (16)
  and two doses only; the strong negative-dose losses at layers 6-12 have no random control at their own layer.
- 60 pairs per cell, with 30-45 panel ties per cell, so resolved counts are 15-40 and single-cell CIs are wide.
  The sweep's shape is solid where it is consistent across neighbouring layers and doses; single standout cells
  (for example layer 10 at +0.025) are not.
- The positive effect at early layers moves length by +20 words; judges may reward length. Not separated.
- Readouts tested at one layer and one |dose|. Multi-layer tested at three layer sets. Position modes tested at one
  layer.
- Ablation: the all-layer version is uninterpretable (see above); the local version has a coherence cost.
  No ablation against the framed-neutral prompt in a working form.

## 8. Suggested next steps

1. Random controls at layers 6, 10 and 14 at r = -0.1 and the best positive dose, to anchor the early-layer cells.
2. Ablation that does not break the model: ablate E only at layers 6-16, or orthogonalise E to the mean residual
   direction before ablating, and run the ablated max-effort vs framed-neutral cell.
3. A length control for the early-layer positive effect: either match lengths in judging or regress wins on the
   word difference within cell.
4. Readout vectors at layer 8 or 10, where the response-mean vector's positive effect is strongest.
5. Phase 3 decision as in the proposal: whether the result at 9B is worth repeating at 27B.
