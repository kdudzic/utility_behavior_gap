"""Build extraction contrast prompts (held out from the essay evaluation items).
Translation is excluded from all extension work (PI decision 2026-10-17): extraction uses grant and postmortem only.

E     : exhortation present (pos) vs absent (neg), framed-neutral wrapper, grant + postmortem tasks.
R_id  : world-class role (pos) vs skilled role (neg), same wrapper, non-essay tasks.
R_act : "act as / pretend you are" world-class persona (pos) vs the direct world-class cue (neg).
R_wide    (week 8, essay only): 20 world-class-essayist paraphrases (pos) vs 20 novice-essay-writer paraphrases (neg),
          the proposal's paraphrased recipe with a wider expertise gap than the paper's world-class vs skilled.
R_content (week 8, essay only): the paper's "You are a world-class essayist." (pos) vs "You are a world-class <other
          profession>." (neg, 20 professions): identity content at a fixed expertise level.
Paraphrases are cycled over (item, repeat) so each is used equally often.
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
    "essay": "For this task, pretend you are a world-class essayist and act as that person would.",
}


WORLD_CLASS_ESSAYIST = [
    "You are a world-class essayist.",
    "You are an award-winning essayist whose work sets the standard in the field.",
    "You are one of the finest essay writers alive.",
    "You are an internationally renowned essayist.",
    "You are an elite essayist with a reputation for brilliance.",
    "You are a master essayist admired by critics and readers alike.",
    "You are a celebrated essayist at the very top of the profession.",
    "You are a legendary essayist whose essays are studied as models of the form.",
    "You are a world-renowned essayist of extraordinary skill.",
    "You are an essayist of the highest rank, widely regarded as the best in the world.",
    "You are a preeminent essayist whose prose is admired everywhere.",
    "You are a distinguished essayist with a global reputation for excellence.",
    "You are a virtuoso essayist.",
    "You are a first-rate essayist at the peak of your powers.",
    "You are a brilliant essayist whose work appears in the most prestigious outlets.",
    "You are an acclaimed essayist known for essays of exceptional depth and craft.",
    "You are the kind of essayist other essayists look up to.",
    "You are a superb essayist, among the best of your generation.",
    "You are a top-tier essayist with decades of celebrated work.",
    "You are a world-leading essayist.",
]
NOVICE_ESSAYIST = [
    "You are a novice essay writer.",
    "You are a beginner at essay writing.",
    "You are an inexperienced essay writer still learning the basics.",
    "You are a student writing one of your first essays.",
    "You are an amateur essay writer with little practice.",
    "You are new to essay writing.",
    "You are an unpractised writer who rarely writes essays.",
    "You are a first-time essay writer.",
    "You are a beginner essayist with no formal training.",
    "You are a rookie essay writer.",
    "You are an essay writer at the very start of learning the craft.",
    "You are a casual writer who has written only a few essays.",
    "You are a novice writer with limited experience of essays.",
    "You are an entry-level essay writer.",
    "You are a beginner who is still getting the hang of essays.",
    "You are an inexperienced writer attempting an essay.",
    "You are a learner who is just starting to write essays.",
    "You are a newcomer to essay writing.",
    "You are an essay-writing beginner.",
    "You are an untrained essay writer.",
]
WORLD_CLASS_OTHER = [f"You are a world-class {p}." for p in [
    "software engineer", "surgeon", "chess grandmaster", "structural engineer", "mathematician", "violinist", "architect",
    "chef", "marine biologist", "tax accountant", "airline pilot", "physicist", "cardiologist", "sculptor", "football coach",
    "geologist", "pastry chef", "cryptographer", "astronomer", "carpenter"]]


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
                k = (int(row["item_index"]) * args.repeats + rep) % len(WORLD_CLASS_ESSAYIST)  # cycle the paraphrases evenly
                if "R_wide" in args.contrasts.split(",") and task == "essay":
                    rows.append({"contrast": "R_wide", "arm": "pos", "cid": cid, "prompt": f"{framed_neutral_prompt(row)}\n\n{WORLD_CLASS_ESSAYIST[k]}"})
                    rows.append({"contrast": "R_wide", "arm": "neg", "cid": cid, "prompt": f"{framed_neutral_prompt(row)}\n\n{NOVICE_ESSAYIST[k]}"})
                if "R_content" in args.contrasts.split(",") and task == "essay":
                    rows.append({"contrast": "R_content", "arm": "pos", "cid": cid, "prompt": f"{framed_neutral_prompt(row)}\n\n{USER_ROLE_STRONG_INSTRUCTIONS[task]}"})
                    rows.append({"contrast": "R_content", "arm": "neg", "cid": cid, "prompt": f"{framed_neutral_prompt(row)}\n\n{WORLD_CLASS_OTHER[k]}"})
    with args.out.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} contrast prompts -> {args.out}")


if __name__ == "__main__":
    main()
