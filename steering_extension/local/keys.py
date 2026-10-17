"""Load API keys for the extension without printing them.

Precedence: process environment, then `steering_extension/spar_openrouter.txt` (SPAR team key),
then `.openrouter.txt` (PI's personal key), then `.env`. Same pattern for VAST_API_KEY with
`steering_extension/spar_vastai.txt`. All key files are gitignored.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEY_FILES = {
    "OPENROUTER_API_KEY": [ROOT / "steering_extension" / "spar_openrouter.txt", ROOT / ".openrouter.txt"],
    "VAST_API_KEY": [ROOT / "steering_extension" / "spar_vastai.txt"],
}


def load_keys(verbose: bool = True) -> dict[str, str]:
    """Populate os.environ for any missing key; return {var: source-name}."""
    sources: dict[str, str] = {}
    for var, files in KEY_FILES.items():
        if os.environ.get(var, "").strip():
            sources[var] = "env"
            continue
        for f in files:
            if f.exists() and f.read_text().strip():
                os.environ[var] = f.read_text().strip().splitlines()[0].strip()
                sources[var] = str(f.relative_to(ROOT))
                break
        else:
            env = ROOT / ".env"
            if env.exists():
                for line in env.read_text().splitlines():
                    if line.startswith(f"{var}="):
                        os.environ[var] = line.split("=", 1)[1].strip().strip("'\"")
                        sources[var] = ".env"
    if verbose:
        for var, src in sources.items():
            print(f"{var}: from {src}", flush=True)
    return sources


if __name__ == "__main__":
    load_keys()
