"""Build extraction contrast prompts (held out from the essay evaluation items).
Translation is excluded from all extension work (PI decision 2026-10-17): extraction uses grant and postmortem only.

E     : exhortation present (pos) vs absent (neg), framed-neutral wrapper, grant + postmortem tasks.
R_id  : world-class role (pos) vs skilled role (neg), same wrapper, non-essay tasks.
R_act : "act as / pretend you are" world-class persona (pos) vs the direct world-class cue (neg).
Each item is repeated --repeats times so several sampled responses enter the means.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from steering_extension.local.common import ROOT, effort_prompt, framed_neutral_prompt, role_strong_prompt, role_weak_prompt, task_items
from utility_behavior_gap.prompts import USER_ROLE_STRONG_INSTRUCTIONS

ACT_AS = {
    "grant_proposal_abstract": "For this task, pretend you are a world-class grant writer and act as that person would.",
    "incident_postmortem": "For this task, pretend you are a world-class site reliability engineer and act as that person would.",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="grant_proposal_abstract,incident_postmortem")
    ap.add_argument("--items-per-task", type=int, default=14)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--contrasts", default="E,R_id")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "steering" / "contrasts" / "contrasts.jsonl")
    args = ap.parse_args()
    if "translation" in args.tasks:
        ap.error("translation is excluded from the steering extension (PI decision 2026-10-17)")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for task in args.tasks.split(","):
        for row in task_items(task)[: args.items_per_task]:
            for rep in range(args.repeats):
                cid = f"{task}:{row['item_index']}:r{rep}"
                if "E" in args.contrasts.split(","):
                    rows.append({"contrast": "E", "arm": "pos", "cid": cid, "prompt": effort_prompt(row)})
                    rows.append({"contrast": "E", "arm": "neg", "cid": cid, "prompt": framed_neutral_prompt(row)})
                if "R_id" in args.contrasts.split(","):
                    rows.append({"contrast": "R_id", "arm": "pos", "cid": cid, "prompt": role_strong_prompt(row)})
                    rows.append({"contrast": "R_id", "arm": "neg", "cid": cid, "prompt": role_weak_prompt(row)})
                if "R_act" in args.contrasts.split(","):
                    rows.append({"contrast": "R_act", "arm": "pos", "cid": cid, "prompt": f"{framed_neutral_prompt(row)}\n\n{ACT_AS[task]}"})
                    rows.append({"contrast": "R_act", "arm": "neg", "cid": cid, "prompt": f"{framed_neutral_prompt(row)}\n\n{USER_ROLE_STRONG_INSTRUCTIONS[task]}"})
    with args.out.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} contrast prompts -> {args.out}")


if __name__ == "__main__":
    main()
