"""Shared helpers for building steering-extension manifests in the paper's job schema."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from utility_behavior_gap.io_utils import read_csv_rows  # noqa: E402
from utility_behavior_gap.job_builder import common_job  # noqa: E402
from utility_behavior_gap.paths import INPUTS  # noqa: E402
from utility_behavior_gap.prompts import (  # noqa: E402
    MODGRID_NEUTRAL_TARGET,
    USER_MAX_EFFORT_STRONG_INSTRUCTIONS,
    USER_ROLE_STRONG_INSTRUCTIONS,
    USER_ROLE_WEAK_INSTRUCTIONS,
    build_essay_system_prompt,
    build_modgrid_fund_prompt,
)

STEER_RUNS = ROOT / "outputs" / "steering" / "runs"
LOCAL_ACTOR = "qwen3.5-9b-or"  # paper actor id; model field records the local HF backend
# Translation is excluded from the extension (PI decision 2026-10-17); only these three tasks are used.
MAX_TOKENS = {"essay": 900, "grant_proposal_abstract": 1400, "incident_postmortem": 3000}
TASKS = tuple(MAX_TOKENS)


def task_items(task: str | None = None) -> list[dict[str, str]]:
    rows = read_csv_rows(INPUTS / "task_items.csv")
    out = []
    per_task_index: dict[str, int] = {}
    for r in rows:
        idx = per_task_index.get(r["task"], 0)
        per_task_index[r["task"]] = idx + 1
        r = dict(r)
        r["item_index"] = str(idx)
        if r["task"] not in MAX_TOKENS:
            continue  # translation excluded
        if task is None or r["task"] == task:
            out.append(r)
    return out


def framed_neutral_prompt(task_row: dict[str, str]) -> str:
    task = task_row["task"]
    block = build_essay_system_prompt(task_row["item_label"]) if task == "essay" else task_row["base_prompt"]
    return build_modgrid_fund_prompt(task, block, target=MODGRID_NEUTRAL_TARGET)


def effort_prompt(task_row: dict[str, str]) -> str:
    return f"{framed_neutral_prompt(task_row)}\n\n{USER_MAX_EFFORT_STRONG_INSTRUCTIONS[task_row['task']]}"


def role_strong_prompt(task_row: dict[str, str]) -> str:
    return f"{framed_neutral_prompt(task_row)}\n\n{USER_ROLE_STRONG_INSTRUCTIONS[task_row['task']]}"


def role_weak_prompt(task_row: dict[str, str]) -> str:
    return f"{framed_neutral_prompt(task_row)}\n\n{USER_ROLE_WEAK_INSTRUCTIONS[task_row['task']]}"


def make_job(*, pair_uid: str, comparison: str, task_row: dict[str, str], condition_a: str, condition_b: str, prompt_a: str, prompt_b: str, repeat: int, extra: dict | None = None) -> dict:
    job = common_job(
        pair_uid=pair_uid,
        comparison=comparison,
        actor=LOCAL_ACTOR,
        task_row=task_row,
        domain="",
        condition_a=condition_a,
        condition_b=condition_b,
        prompt_a=prompt_a,
        prompt_b=prompt_b,
        predicted_condition=condition_a,
        other_condition=condition_b,
        repeat=str(repeat),
        framing="modgrid_neutral_competition_wrapper",
        source_note="steering_extension_local_hf",
    )
    job["max_tokens"] = MAX_TOKENS[task_row["task"]]
    job["model"] = "Qwen/Qwen3.5-9B (local hf, bf16)"
    if extra:
        job.update(extra)
    return job


def write_manifest(jobs: list[dict], run_name: str) -> Path:
    payload = "\n".join(json.dumps(j, ensure_ascii=False, sort_keys=True) for j in jobs)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:12]
    run_id = f"{run_name}__hash-{digest}"
    run_dir = STEER_RUNS / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = run_dir / "generation_jobs.jsonl"
    rows = [
        {
            **j,
            "run_id": run_id,
            "run_dir": str(run_dir),
            "run_manifest_path": str(manifest),
            "run_generations_path": str(run_dir / "generations.jsonl"),
            "run_generation_failures_path": str(run_dir / "generation_failures.jsonl"),
            "run_judge_votes_path": str(run_dir / "judge_votes.jsonl"),
        }
        for j in jobs
    ]
    with manifest.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"wrote {len(rows)} jobs -> {manifest}")
    return manifest
