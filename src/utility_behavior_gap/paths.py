"""Repository paths shared by the reproduction entry points."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUTS = ROOT / "data" / "inputs"
OUTPUTS = Path(os.environ.get("UTILITY_BEHAVIOR_GAP_OUTPUTS", ROOT / "outputs"))
ANALYSIS_SPECS = ROOT / "analysis_specs"
OUTPUT_INPUTS = OUTPUTS / "inputs"
OUTPUT_API = OUTPUTS / "api"
OUTPUT_RAW = OUTPUTS / "raw"
PROCESSED = OUTPUTS / "processed"
ANALYSIS = OUTPUTS / "analysis"
FIGURES = OUTPUTS / "figures"
