"""Maintainer-only export of the explicitly selected paper inputs; no API calls.

Readers use reproduce.py. This records source checksums and compresses the
missing inputs without copying raw API caches or exploratory experiments.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_FILES = [
    "framed_user_strong_panel_pairs.csv",
    "canonical_highn_utility_gap_trend__gap-actor-z_trials.csv",
    "final_text_analysis_pair_deltas.csv",
    "framed_user_prompt_role_pair_deltas.csv",
    "moral_low_vs_framed_empty_current_pair_deltas_for_selection.csv",
]


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.research_root.resolve()
    dest = ROOT / "data" / "processed"
    dest.mkdir(parents=True, exist_ok=True)
    records = []

    def export(path: Path, name: str, frame: pd.DataFrame | None = None) -> None:
        target = dest / name
        with tempfile.NamedTemporaryFile(dir=dest, suffix=".gz", delete=False) as temp:
            staging = Path(temp.name)
        if frame is None and path.suffix == ".gz":
            shutil.copy2(path, staging)
        elif frame is None:
            with path.open("rb") as inp, staging.open("wb") as out:
                with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0) as zipped:
                    shutil.copyfileobj(inp, zipped)
        else:
            with staging.open("wb") as out:
                with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0) as zipped:
                    zipped.write(frame.to_csv(index=False).encode("utf-8"))
        os.replace(staging, target)
        records.append({
            "path": str(target.relative_to(ROOT)), "sha256": digest(target),
            "source": str(path.relative_to(source)), "source_sha256": digest(path),
            "transformation": ("unchanged gzip" if path.suffix == ".gz" else "gzip only") if frame is None else "selected columns; rows and order unchanged",
            "rows": None if frame is None else len(frame),
        })

    for name in ANALYSIS_FILES:
        export(source / "outputs" / "analysis" / name, name + ".gz")
    catalog = source / "outputs/analysis/final_text_analysis_by_output.csv"
    flags = {"output_id", "missing_output", "generation_success_false", "finish_reason_missing",
             "non_stop_finish", "explicit_length_truncation", "empty_output"}
    export(catalog, "output_validity.csv.gz", pd.read_csv(catalog, usecols=lambda c: c in flags))
    labels = source / "outputs/analysis/canonical_highn_moral_refusal_classifications.jsonl"
    export(labels, labels.name + ".gz")
    followup = source / "outputs/api/runs/essay__qwen35_reasoning_stance_followup__qwen3.5-9b-or__seed-20260915__hash-2994eb3b2711/analysis/qwen35_reasoning_stance_pair_outcomes.csv"
    frame = pd.read_csv(followup)
    # The labels are joined afresh by the reproduction step, not treated as outcomes.
    remove = {f"{side}_{key}" for side in ("high", "low")
              for key in ("believes", "disbelieves", "suspicious", "dismisses", "label_source")}
    remove |= {"both_traces_classified", "either_disbelieves", "either_suspicious_or_disbelieves"}
    export(followup, "qwen35_followup_pair_inputs.csv.gz", frame.drop(columns=list(remove), errors="ignore"))
    export(source / "outputs/analysis/incentive_belief_qwen9b_followup_traces.jsonl",
           "qwen35_followup_local_labels.jsonl.gz")
    export(followup.parent.parent / "qwen35_old_plus_followup_reasoning_traces.jsonl.gz",
           "qwen35_old_plus_followup_reasoning_traces.jsonl.gz")
    (dest / "provenance.json").write_text(json.dumps(records, indent=2) + "\n")
    print(f"Exported {len(records)} inputs, {sum((ROOT / r['path']).stat().st_size for r in records)/1024**2:.1f} MiB")


if __name__ == "__main__":
    main()
