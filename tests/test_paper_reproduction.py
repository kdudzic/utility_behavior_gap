"""Fast checks for the public offline entry point; full fits are a separate command."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("paper_reproduction", ROOT / "paper_reproduction/reproduce.py")
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


def test_frozen_inputs_present_and_checksummed():
    workflow.audit()


def test_scientific_choices_explicit():
    assert workflow.CONTRASTS["highlow"][2] == "actor task domain"
    assert workflow.CONTRASTS["direct"][2] == "actor task"
    assert "framed_user_prompt_role" in str(workflow.CONTRASTS["role"][0])
    assert workflow.FEATURES["direct_instruction"][-1] == .20
    assert workflow.FEATURES["framed_user_prompt_role"][-1] == .25


def test_comparison_rejects_numerical_changes_and_missing_rows():
    frame = pd.DataFrame({"key": ["a", "b"], "value": [.4, .6]})
    workflow.compare(frame, frame.copy(), ["key"], ["value"])
    changed = frame.copy()
    changed.loc[0, "value"] = .5
    with pytest.raises(AssertionError):
        workflow.compare(changed, frame, ["key"], ["value"])
    with pytest.raises(AssertionError):
        workflow.compare(frame.iloc[:1], frame, ["key"], ["value"])


def test_bootstrap_and_exact_intervals_are_distinct():
    from utility_behavior_gap.scripts.consolidate_aggregate_cis import bootstrap_equal_cell
    from utility_behavior_gap.scripts.plot_canonical_highn_highlow import exact_familywise_ci
    mean, low, high, n = bootstrap_equal_cell([np.array([1., 1., 0.]), np.array([0., 1.])], 20260615, 100)
    assert mean == pytest.approx((2/3 + 1/2)/2)
    assert n == 2 and low <= mean <= high
    lo1, hi1 = exact_familywise_ci(60, 100, 1)
    lo28, hi28 = exact_familywise_ci(60, 100, 28)
    assert lo28 < lo1 < hi1 < hi28
