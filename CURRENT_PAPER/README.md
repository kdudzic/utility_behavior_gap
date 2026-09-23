# Current Paper Artifacts

Use [the artifact map](../paper_reproduction/ARTIFACTS.md) to distinguish current
paper results from retained history. Nothing is selected by modification time.

## Main Figures

- [Direct exhortation](figures/direct_instruction_main.png)
- [High-low utility](figures/highlow_model_task_lollipop.png)
- [Framed role cue](figures/framed_user_prompt_role_model_task_lollipop.png)
- [Harmful vs framed empty](figures/moral_low_vs_framed_empty_model_task_lollipop.png)
- [High utility vs framed empty](figures/high_utility_vs_framed_empty_model_task_lollipop.png)
- [Utility magnitude trends](figures/utility_trend_two_panel_gap_and_absolute_framed_empty.png)

The family-wise intervals in these model/task figures are not the same estimand
or correction as the overall/task bootstrap summaries. Use
[the unified aggregate reference](../paper_reproduction/reference/aggregate_winrate_bootstrap_cis.csv)
for those summaries; older aggregate Markdown files retain their historical methods.

## Feature Tables

- [Direct](features/direct_instruction_main_feature_table.tex)
- [Utility, matching direct dimensions](features/highlow_main_feature_table.tex)
- [Role](features/framed_user_prompt_role_feature_table.tex)
- [Harmful vs framed empty](features/moral_low_vs_framed_empty_feature_table.tex)
- [Feature directionality](features/feature_directionality_by_contrast_table.tex)

Each has a matching CSV/Markdown file. The offline runner refits the underlying
models using the updated vocabulary inputs in `data/processed/`, not the older
large `final_text_analysis_pair_deltas.csv` retained here.

## Reasoning Appendix

- [Report including the larger Qwen sample](docs/appendix_reasoning_trace_analysis.md)
- [Suspicion-exclusion table](results/reasoning_trace/reasoning_suspicion_disbelief_exclusion.md)
- [Original reasoning-on figure](figures/highlow_reasoning_traces_medium_essay_lollipop.png)
- [Suspicion-filtered figure](figures/highlow_reasoning_suspicion_filtered_essay_lollipop.png)
- [Classifier protocol](../analysis_specs/reasoning_trace_stance_classifier.md)

## Definitions and Reproduction

- [Approved actor prompt book](docs/canonical_prompt_book.md)
- [Literal judge prompts](docs/judge_prompts.md)
- [Editable feature definitions](../analysis_specs/feature_definitions.yaml)
- [Offline reproduction guide](../paper_reproduction/README.md)

Amount and early moral high-low artifacts, unframed role results, and older
feature tables remain in this directory for provenance. Their presence does
not make them current paper results. Existing PDFs are historical exports;
the reproduction command writes PNG figures only.
