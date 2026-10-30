"""Generality arm (week 7, Chris): does the effort direction still act when the prompt carries a role cue instead
of the exhortation? Uses the paper's framed role-cue prompts (common.role_strong_prompt = "world-class" cue,
common.role_weak_prompt = "skilled" cue). For each role prompt P, two cells against the untouched P essay from the
same item and repeat:
  ablate_E_L{layers}_{role}_vs_{role} : P with E projected out at --ablate-layers (all positions)  vs  P untouched
  steer_E_L{L}_r{+r}_{role}_vs_{role}  : P with E added at layer --add-layer, dose --add-r (response tokens)  vs  P untouched
Optionally a bridge cell world-class vs skilled, both untouched (the paper's role contrast).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

from steering_extension.local.common import ROOT, make_job, role_strong_prompt, role_weak_prompt, task_items, write_manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vectors", type=Path, required=True)
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--task", default="essay")
    ap.add_argument("--items", type=int, default=30)
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--key", default="E")
    ap.add_argument("--ablate-layers", default="8,10,12,14,16")
    ap.add_argument("--add-layer", type=int, default=6)
    ap.add_argument("--add-r", type=float, default=0.1)
    ap.add_argument("--roles", default="world_class,skilled")
    ap.add_argument("--bridge", action="store_true", help="also pair world-class vs skilled, both untouched")
    args = ap.parse_args()
    tensors = load_file(str(args.vectors))
    vec_rel = str(args.vectors.resolve().relative_to(ROOT)) if args.vectors.resolve().is_relative_to(ROOT) else str(args.vectors.resolve())
    layers = [int(x) for x in args.ablate_layers.split(",")]
    ltag = "+".join(str(x) for x in layers)
    L = args.add_layer
    rms = float(tensors[f"norm/layer{L}"][0])
    vnorm = float(np.linalg.norm(tensors[f"{args.key}/layer{L}"].astype(np.float64)))
    add = {"vector": vec_rel, "key": args.key, "layer": L, "coef": args.add_r * rms / vnorm, "mode": "response", "r": args.add_r, "rms_norm": rms, "vector_norm": vnorm}
    abl = {"ablate": vec_rel, "key": args.key, "layers": layers}
    prompts = {"world_class": role_strong_prompt, "skilled": role_weak_prompt}
    jobs = []
    for rep in range(args.repeats):
        for row in task_items(args.task)[: args.items]:
            task = row["task"]
            for role in args.roles.split(","):
                p = prompts[role](row)
                cond_abl = f"ablate_{args.key}_L{ltag}_{role}"
                uid = f"{cond_abl}_vs_{role}:{task}:{row['item_index']}:r{rep}"
                jobs.append(make_job(pair_uid=uid, comparison="ablate_vs_role", task_row=row, condition_a=cond_abl, condition_b=role, prompt_a=p, prompt_b=p, repeat=rep,
                                     extra={"steering_a": abl, "steering_b": None, "cell": f"{cond_abl}_vs_{role}"}))
                cond_add = f"steer_{args.key}_L{L}_r{args.add_r:+.3f}_{role}"
                uid = f"{cond_add}_vs_{role}:{task}:{row['item_index']}:r{rep}"
                # alias the untouched role essay from the ablation pair so each role prompt is sampled once per item and repeat
                jobs.append(make_job(pair_uid=uid, comparison="steer_vs_role", task_row=row, condition_a=cond_add, condition_b=role, prompt_a=p, prompt_b=p, repeat=rep,
                                     extra={"steering_a": add, "steering_b": None, "alias_b": f"{cond_abl}_vs_{role}:{task}:{row['item_index']}:r{rep}::b", "cell": f"{cond_add}_vs_{role}"}))
            if args.bridge:
                uid = f"world_class_vs_skilled:{task}:{row['item_index']}:r{rep}"
                jobs.append(make_job(pair_uid=uid, comparison="role_bridge", task_row=row, condition_a="world_class", condition_b="skilled", prompt_a=prompts["world_class"](row), prompt_b=prompts["skilled"](row), repeat=rep,
                                     extra={"steering_a": None, "steering_b": None, "alias_a": f"ablate_{args.key}_L{ltag}_world_class_vs_world_class:{task}:{row['item_index']}:r{rep}::b",
                                            "alias_b": f"ablate_{args.key}_L{ltag}_skilled_vs_skilled:{task}:{row['item_index']}:r{rep}::b", "cell": "world_class_vs_skilled"}))
    write_manifest(jobs, args.run_name)


if __name__ == "__main__":
    main()
