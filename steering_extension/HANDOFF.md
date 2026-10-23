# Handoff: current state of the steering extension

Read this first in any new Claude Code session, on any machine. It replaces the conversation
history: everything a new instance needs to continue is here or linked from here.
Update it at the end of every working session (section "Session log", plus any section that changed),
commit, and push. The repo is public: no keys, account emails, balances, or personal details here.

Last updated: 2026-10-23.

## 1. What the project is

Mechanistic extension of Zhou & Ackerman, "When Preferences Fail to Become Incentives" (this repo).
Question: is the paper's effort-exhortation effect (and role-cue effect) carried by a single direction in
Qwen3.5-9B's residual stream, and does steering along it act like a dose?
Hypotheses: H1 adding the direction to a neutral prompt wins like the exhortation does; H2 removing it
cancels the effect; H3 random directions of the same size do nothing and fluency stays intact.
Design and phase plan: `PROPOSAL.md` (its decision log at the top overrides older text).
Rules: repo `AGENTS.md`, steering section. Literature: `docs/literature_notes.md`.

## 2. Where things stand

| phase | status | write-up |
| --- | --- | --- |
| 0 replication of paper cells | done, matches paper (effort 0.70 vs 0.67; role 0.55 vs 0.57) | `docs/mini_pilot_report.md` |
| 1 vectors | done twice: v2 (pilot, with translation), v3 (no translation, three readouts) | `docs/mini_pilot_report.md`, `docs/layer_selection.md` |
| 2 essay dose curves | done for old vector at L16 (pilot), redone for new vector at L18, old vector layer profile | `docs/essay_redo_L18.md`, `docs/essay_rmean_layers.md` |
| 3 PI review | in progress; weekly decks `docs/pilot_deck.md`, `docs/week5_deck.md` | |
| 4 full grid, 27B | not started; needs fresh PI go | |

Vocabulary used with the PI:
- **old vector** = `E` key, response-token-average readout (Persona Vectors recipe).
- **new vector** = `E_astart` key, residual at the assistant-start token (last prompt token).
- **prompt-average vector** = `E_pmean` key, mean over user-prompt tokens. Dropped (moves text the wrong way).
- **dose r** = fraction of the layer's RMS residual norm. Injection only at generated tokens (`response` mode).

## 3. Key results so far (Qwen3.5-9B, essays unless stated, paper judge panel, ties excluded)

- Old vector, remove (r = -0.1): loses at layers 8 / 12 / 16 (0.12 / 0.09 / 0.06, all p < 0.001), weaker at 20 / 24 (n.s.).
- Old vector, add (r = +0.05) at L16: three runs 11/6, 16/5, 12/9; pooled 39/20 (0.66). Weak, sign stable, size not.
- Higher positive doses (+0.1 and up) lose and hurt fluency.
- New vector (E_astart) at L16 / 18 / 22: no significant cell at any dose on essays; 63-80 percent ties.
  It is a perfect detector of "an exhortation was present" (held-out AUC 1.0) but a weak steerer.
- Random matched-norm directions: null everywhere.
- Steering never reproduces the real exhortation's +17-20 word length effect.
- Lessons: split-half reliability of the whole vector was the wrong filter (old vector is noisy yet causal);
  feature-signature proxy for layer choice failed (retired); readout matters more than layer.
- Role vectors: response readout unreliable at n = 120 per arm; prompt-side readouts reliable but now known
  to be weak steerers. No role steering run yet.

## 4. Open questions and candidate next steps (none authorised yet unless the PI says so)

1. Rebuild the old vector with more data (300+ responses per arm, grant + postmortem), optionally PC-denoised.
2. Directional-ablation necessity arm under the real max-effort prompt (cheap, never run).
3. Role vectors with the response readout at larger n.
4. Full dose curve of the old vector at a second layer (8 or 12).
5. GLM-5.1 and 27B: on hold until the PI and Chris decide; GLM-5.1 white-box needs 8x80 GB.

## 5. Decisions taken by the PI (do not re-litigate)

- Models: Qwen3.5-9B anchor, 27B later. Vectors: E, R_id, R_act.
- Translation excluded from everything since 2026-10-17 (code enforces it).
- Use the SPAR OpenRouter key by default; personal key only on explicit request.
- GPU work on vast.ai (Athena login nodes closed since 2026-10-17; SLURM runner kept).
- Paid calls need an explicit go per phase. Scientific choices (dose, layer, readout, positions) are discussed first.

## 6. How to run things

Full commands: `README.md`. Short version from the repo root:
```bash
export PYTHONPATH=$PWD:$PWD/src
.venv/bin/python -m steering_extension.local.keys --check          # keys present, nothing leaked
.venv/bin/python -m steering_extension.vast.vast status            # instances on the shared account
.venv/bin/python -m steering_extension.vast.vast up --gpu A100_PCIE --disk 100
.venv/bin/python -m steering_extension.vast.vast push && .venv/bin/python -m steering_extension.vast.vast bootstrap --wait
.venv/bin/python -m steering_extension.vast.vast run --name X --env STEER_USE_KERNELS=1 steering_extension.steer.generate --manifest <run>/generation_jobs.jsonl --batch-size 32
.venv/bin/python -m steering_extension.vast.vast pull && .venv/bin/python -m steering_extension.vast.vast down --yes
bash steering_extension/local/judge.sh <run_dir> 8                 # paid
.venv/bin/python -m steering_extension.local.analyze_dose --run-dir <run_dir>
```
Gotchas: the vast account is shared, never touch instances you did not create; `vast down` must report
"verified gone"; raw outputs live in gitignored `outputs/steering/` and are NOT in git (copy compact tables
into `docs/results/<date>_<name>/`). Keys live outside the repo in `~/.config/utility_behavior_gap/secrets.env`
and must be copied to a new machine by hand.

## 7. How the PI likes to work

- Plain, simple language; short answers when asked; numbers in small tables.
- Say clearly what was and was not tested; do not overstate (e.g. which vector a layer result applies to).
- Run long GPU/judge jobs in the background and report when done.
- Decks: markdown in `docs/`, `##` per slide, front matter as in `docs/pilot_deck.md`; the PI converts with `md2pptx`.

## 8. Session log

- 2026-10-10: proposal drafted; Phases 0-2 pilot on Athena (old vector, L16 dose curve).
- 2026-10-17: moved to vast.ai; secrets hardened; translation dropped; three-readout v3 extraction; layer
  procedure (grant sweep, judge check, postmortem); essay redo with new vector (null); old-vector layer profile;
  week 5 deck.
- 2026-10-23: this handoff file created so any machine can continue from git alone.
