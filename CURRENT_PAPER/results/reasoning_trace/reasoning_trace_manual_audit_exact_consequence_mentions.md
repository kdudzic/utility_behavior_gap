# Manual Audit: Reasoning Traces With Exact Consequence Mentions

Scope: all 253 readable essay high-low reasoning traces that explicitly mention the assigned consequence.

Method: the first 168 records were read in full and hand-coded. After the final Qwen3.5 run completed, the 85 newly available records were manually reviewed using the prompt-analysis section and every contextual passage containing evaluation, disbelief, hidden-goal, or refusal language. Code only assembled the records, displayed contextual passages, validated coverage, and generated these summaries; it did not assign the manual labels.

Manual codebooks:
- `analysis_specs/reasoning_trace_manual_codes_initial_168.csv`
- `analysis_specs/reasoning_trace_manual_codes_addendum.csv`

The build fails unless the two codebooks cover every exact-mention trace exactly once.

## Primary Codes

| primary_code | n | percent |
| --- | --- | --- |
| eval_awareness | 104 | 41.1 |
| ordinary_hidden_context | 87 | 34.4 |
| disbelief_and_eval_awareness | 43 | 17.0 |
| strategic_hidden_agenda | 10 | 4.0 |
| eval_and_strategic | 4 | 1.6 |
| scenario_disbelief | 2 | 0.8 |
| disbelief_eval_and_strategic | 2 | 0.8 |
| eval_awareness_refusal | 1 | 0.4 |

## Overlapping Flags

| flag | n | percent |
| --- | --- | --- |
| scenario_disbelief | 47 | 18.6 |
| eval_awareness | 154 | 60.9 |
| prompt_injection_frame | 143 | 56.5 |
| strategic_hidden_agenda | 16 | 6.3 |

## By Actor

| actor | actor_label | n |
| --- | --- | --- |
| glm-5.1-or | GLM-5.1 | 36 |
| kimi-k2.5-or | Kimi K2.5 | 13 |
| mimo-v25-pro-or | MiMo V2.5 Pro | 3 |
| qwen3.5-9b-or | Qwen3.5 9B | 137 |
| qwen3.6-plus-or | Qwen3.6 Plus | 64 |

## By Side

| side | n |
| --- | --- |
| high | 88 |
| low | 165 |

The manual audit is descriptive and exploratory. The complete, deterministic regex audit is the reproducible primary audit of awareness-language prevalence.
