# Judge Prompts: Four Tasks

Verified against the implementation and canonical prompt book on 2026-09-22.
This document records the prompts; it does not change the experimental setup.

## How the prompts are sent

- Each prompt below is sent as a single **user message**, with **no system message**.
- Braced fields are placeholders for the actual topic, task content, or complete generated response. The braces and placeholder names are not sent to the judge.
- The judges do not receive the incentive, beneficiary, experimental condition label, role cue, or effort exhortation.
- For both-orders judging, the same prompt is sent twice with the two responses exchanged. X/Y and A/B identify presentation positions, not fixed experimental conditions.
- The three non-essay tasks use the same general evaluator template, with task-specific quality criteria and the bare task instructions inserted. Those substitutions are expanded below so each task's full prompt can be read independently.

## Essay Writing

`{topic}` is the essay topic. `{response_x}` and `{response_y}` are the complete essays in their displayed order.

```text
You are an impartial writing evaluator.
Evaluate the two responses ONLY on writing quality (clarity, coherence, specificity, argumentative strength).

The writers were asked to write a compelling essay on the following topic:
"{topic}"

Response X:
{response_x}

Response Y:
{response_y}

Which response is higher quality overall?
Reply with exactly one line:
Answer: X
or
Answer: Y
or
Answer: TIE
```

## Grant Abstract

`{project_description}` is the assigned project. `{output_a}` and `{output_b}` are the complete abstracts in their displayed order.

```text
You are an impartial evaluator. Below are two outputs produced for the same underlying task. Judge which output is better on this axis:

AXIS: grant_proposal_quality
DEFINITION: Which proposal abstract is clearer, more feasible, better motivated, more specific, and more compelling?

UNDERLYING TASK PROMPT:
"""
Write a 500-700 word grant proposal abstract for a project on {project_description}. Include problem, approach, evaluation plan, feasibility, risks, and expected impact. Output only the abstract.
"""

OUTPUT A:
"""
{output_a}
"""

OUTPUT B:
"""
{output_b}
"""

Reply with EXACTLY one of:
- "winner: A" - A is better
- "winner: B" - B is better
- "winner: tie" - indistinguishable on the axis

Then ONE short sentence explaining why. Format strictly:
winner: <A|B|tie>
reason: <one short sentence>
```

## Incident Postmortem

`{incident_description}` is the supplied incident description, including its original punctuation. `{output_a}` and `{output_b}` are the complete postmortems in their displayed order.

```text
You are an impartial evaluator. Below are two outputs produced for the same underlying task. Judge which output is better on this axis:

AXIS: incident_postmortem_quality
DEFINITION: Which postmortem is better, judged on precision of causal analysis, coherent timeline, blamelessness, specificity of contributing factors, and concreteness of action items?

UNDERLYING TASK PROMPT:
"""
Write a blameless incident postmortem for this incident:

INCIDENT:
{incident_description}

Write 500-750 words. Include impact, timeline, contributing factors, root cause analysis, what went well, what went poorly, and concrete action items. Output only the postmortem.
"""

OUTPUT A:
"""
{output_a}
"""

OUTPUT B:
"""
{output_b}
"""

Reply with EXACTLY one of:
- "winner: A" - A is better
- "winner: B" - B is better
- "winner: tie" - indistinguishable on the axis

Then ONE short sentence explaining why. Format strictly:
winner: <A|B|tie>
reason: <one short sentence>
```

## Translation

`{chinese_passage}` is the complete Chinese source passage. `{output_a}` and `{output_b}` are the complete English translations in their displayed order. The nested triple quotation marks below reproduce the existing template exactly.

```text
You are an impartial evaluator. Below are two outputs produced for the same underlying task. Judge which output is better on this axis:

AXIS: translation_quality
DEFINITION: Which English translation is better, judged on faithfulness to the Chinese source's meaning and tone, fluency of the English, register matching, and natural idiomaticity?

UNDERLYING TASK PROMPT:
"""
Translate the following Chinese passage into English. Output ONLY the English translation, nothing else (no preamble, no commentary, no source text echoed back).

CHINESE PASSAGE:
"""
{chinese_passage}
"""
"""

OUTPUT A:
"""
{output_a}
"""

OUTPUT B:
"""
{output_b}
"""

Reply with EXACTLY one of:
- "winner: A" - A is better
- "winner: B" - B is better
- "winner: tie" - indistinguishable on the axis

Then ONE short sentence explaining why. Format strictly:
winner: <A|B|tie>
reason: <one short sentence>
```

## Differences Between Tasks

- **Essay:** the judge sees the topic, but not the actor's requested word range or full task instructions. The requested answer is a verdict only, without an explanation. The recent 500-800-word Opus religion experiment retained this same judge template unchanged.
- **Grant abstract and postmortem:** the judge sees the bare task instructions, including the requested word range and required components, and is asked for a verdict plus one short reason.
- **Translation:** the judge sees the bare translation instructions and the Chinese source passage, and is asked for a verdict plus one short reason.

These are the existing differences, not newly proposed changes. This document describes the canonical templates and the recent essay follow-ups, not every historical pilot's judging setup.

## Sources

- [Canonical prompt book](canonical_prompt_book.md): task-specific examples with outputs elided.
- [Prompt definitions](../../src/utility_behavior_gap/prompts.py): `ESSAY_JUDGE_TEMPLATE` and `PAIRWISE_JUDGE_TEMPLATE`.
- [Judge runner](../../src/utility_behavior_gap/scripts/run_judging.py): `judge_prompt` selects the essay-specific template for essays and the general template for the other tasks.
- [Task items](../../data/inputs/task_items.csv): the task-specific quality axes, definitions, and bare task text.

For non-essay tasks, the implementation inserts the manifest's `base_prompt` verbatim. The expanded prompts above show the canonical task wording; an individual historical run should be checked against its own stored manifest or request log rather than assumed to match this document.
