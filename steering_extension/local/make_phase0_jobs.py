"""Phase 0 replication manifests: the paper's framed-neutral essay effort (and optionally role)
contrasts for the local Qwen3.5-9B. Prompts are byte-identical to the paper's canonical prompt
book; only the backend differs (local HF transformers instead of OpenRouter)."""
from __future__ import annotations

import argparse

from steering_extension.local.common import effort_prompt, framed_neutral_prompt, make_job, role_strong_prompt, role_weak_prompt, task_items, write_manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="essay")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--contrasts", default="effort", help="comma list of effort,role")
    ap.add_argument("--run-name", default="phase0_mini")
    args = ap.parse_args()
    jobs = []
    for rep in range(args.repeats):
        for row in task_items(args.task):
            if "effort" in args.contrasts:
                jobs.append(make_job(pair_uid=f"framed_user_max_effort:{row['task']}:{row['item_index']}:r{rep}", comparison="framed_user_max_effort", task_row=row, condition_a="user_strong", condition_b="user_normal", prompt_a=effort_prompt(row), prompt_b=framed_neutral_prompt(row), repeat=rep))
            if "role" in args.contrasts:
                jobs.append(make_job(pair_uid=f"framed_user_prompt_role:{row['task']}:{row['item_index']}:r{rep}", comparison="framed_user_prompt_role", task_row=row, condition_a="user_strong", condition_b="user_normal", prompt_a=role_strong_prompt(row), prompt_b=role_weak_prompt(row), repeat=rep))
    write_manifest(jobs, args.run_name)


if __name__ == "__main__":
    main()
