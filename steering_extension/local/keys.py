"""Load API keys for the steering extension without printing them.

Canonical location (outside the repo tree): ``~/.config/utility_behavior_gap/secrets.env`` with
lines ``OPENROUTER_API_KEY=...`` and ``VAST_API_KEY=...`` (file mode 600, directory 700).
``XDG_CONFIG_HOME`` is honoured and ``UBG_SECRETS_FILE`` overrides the path.

Precedence per variable: process environment > secrets.env > gitignored in-repo files
(``steering_extension/spar_openrouter.txt``, ``steering_extension/spar_vastai.txt``) > ``.env``.
The PI's personal OpenRouter key (``OPENROUTER_API_KEY_PERSONAL=`` in secrets.env, else the
``sk-or-v1-`` token in ``.openrouter.txt``) is used only when ``OPENROUTER_KEY_SOURCE=personal``
is set; it is never a silent fallback.

``python -m steering_extension.local.keys --check`` audits the setup (per-key source and length,
secrets-file permissions, gitignore status of every in-repo key file, key material in tracked
files, pre-commit hook installation) and exits non-zero on any problem. Values are never printed.
"""
from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEY_VARS = ("OPENROUTER_API_KEY", "VAST_API_KEY")
OPENROUTER_RE = re.compile(r"sk-or-v1-[0-9a-f]{64}")
HEX64_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{64}(?![0-9a-fA-F])")

REPO_KEY_FILES = {
    "OPENROUTER_API_KEY": ROOT / "steering_extension" / "spar_openrouter.txt",
    "VAST_API_KEY": ROOT / "steering_extension" / "spar_vastai.txt",
}
PERSONAL_OPENROUTER_FILE = ROOT / ".openrouter.txt"
DOTENV = ROOT / ".env"
# every in-repo file that may hold a key; all must be gitignored and untracked
IN_REPO_SECRET_PATHS = [*REPO_KEY_FILES.values(), PERSONAL_OPENROUTER_FILE, DOTENV]
VERSIONED_HOOK = ROOT / "steering_extension" / "local" / "hooks" / "pre-commit"


def secrets_file() -> Path:
    override = os.environ.get("UBG_SECRETS_FILE", "").strip()
    if override:
        return Path(override).expanduser()
    base = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base_path = Path(base).expanduser() if base else Path.home() / ".config"
    return base_path / "utility_behavior_gap" / "secrets.env"


def _display(path: Path) -> str:
    """Path for messages: relative to the repo, else with ~ for the home directory."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        pass
    try:
        return "~/" + str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def _parse_env_file(path: Path) -> dict[str, str]:
    """KEY=VALUE lines (optional `export `, quotes stripped); comments and blanks ignored."""
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        if s.startswith("export "):
            s = s[len("export "):].lstrip()
        k, v = s.split("=", 1)
        out.setdefault(k.strip(), v.strip().strip("'\""))
    return out


def _first_token(path: Path) -> str:
    """First non-empty line of a one-key file, without whitespace or quotes."""
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        tok = "".join(line.split()).strip("'\"")
        if tok:
            return tok
    return ""


def resolve_key(var: str) -> tuple[str | None, str | None]:
    """Return ``(value, source_name)`` for ``var`` without touching ``os.environ``."""
    if var not in KEY_VARS:
        raise KeyError(var)
    value = os.environ.get(var, "").strip()
    if value:
        return value, "env"
    sec = secrets_file()
    secrets = _parse_env_file(sec)
    if var == "OPENROUTER_API_KEY" and personal_requested():
        value = secrets.get("OPENROUTER_API_KEY_PERSONAL", "")
        if value:
            return value, f"{_display(sec)} [OPENROUTER_API_KEY_PERSONAL]"
        if PERSONAL_OPENROUTER_FILE.is_file():
            m = OPENROUTER_RE.search(PERSONAL_OPENROUTER_FILE.read_text(encoding="utf-8", errors="replace"))
            if m:
                return m.group(0), ".openrouter.txt (personal)"
        return None, None  # explicit opt-in with nothing found: never fall back to the SPAR key
    value = secrets.get(var, "")
    if value:
        return value, _display(sec)
    value = _first_token(REPO_KEY_FILES[var])
    if value:
        if var == "OPENROUTER_API_KEY":
            m = OPENROUTER_RE.search(value)
            value = m.group(0) if m else value
        return value, _display(REPO_KEY_FILES[var])
    value = _parse_env_file(DOTENV).get(var, "")
    if value:
        return value, ".env"
    return None, None


def personal_requested() -> bool:
    return os.environ.get("OPENROUTER_KEY_SOURCE", "").strip().lower() == "personal"


def load_keys(verbose: bool = True) -> dict[str, str]:
    """Populate os.environ for any missing key; return {var: source-name}. Never prints values."""
    sources: dict[str, str] = {}
    for var in KEY_VARS:
        value, src = resolve_key(var)
        if value is None or src is None:
            if var == "OPENROUTER_API_KEY" and personal_requested():
                print("OPENROUTER_KEY_SOURCE=personal but no personal key was found", file=sys.stderr, flush=True)
            continue
        if src != "env":
            os.environ[var] = value
        sources[var] = src
    if verbose:
        for var, src in sources.items():
            print(f"{var}: from {src}", flush=True)
    return sources


# --------------------------------------------------------------------------- --check

def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def _hooks_dir() -> Path:
    r = _git("rev-parse", "--git-path", "hooks")
    p = Path(r.stdout.strip() or ".git/hooks")
    return p if p.is_absolute() else ROOT / p


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _line_of(data: bytes, pos: int) -> int:
    return data.count(b"\n", 0, pos) + 1


def check() -> int:
    problems: list[str] = []

    def ok(msg: str) -> None:
        print(f"  ok    {msg}")

    def bad(msg: str) -> None:
        problems.append(msg)
        print(f"  FAIL  {msg}")

    print("secrets file")
    sec = secrets_file()
    if sec.is_file():
        mode = stat.S_IMODE(sec.stat().st_mode)
        dmode = stat.S_IMODE(sec.parent.stat().st_mode)
        (ok if mode & 0o077 == 0 else bad)(f"{_display(sec)} mode {mode:03o} (want 600)")
        (ok if dmode & 0o077 == 0 else bad)(f"{_display(sec.parent)} mode {dmode:03o} (want 700)")
        present = sorted(k for k in _parse_env_file(sec) if k in KEY_VARS or k == "OPENROUTER_API_KEY_PERSONAL")
        ok(f"variables defined: {', '.join(present) or 'none'}")
    else:
        print(f"  note  {_display(sec)} not found (see steering_extension/README.md, Secrets)")
    if personal_requested():
        print("  note  OPENROUTER_KEY_SOURCE=personal is set: the personal OpenRouter key is selected")

    print("keys")
    loaded: dict[str, str] = {}
    for var in KEY_VARS:
        value, src = resolve_key(var)
        if not value:
            bad(f"{var}: not found")
            continue
        loaded[var] = value
        ok(f"{var}: found, source {src}, length {len(value)}")
        if var == "OPENROUTER_API_KEY" and not OPENROUTER_RE.fullmatch(value):
            bad(f"{var}: value does not look like an OpenRouter key (sk-or-v1- + 64 hex)")
        if var == "VAST_API_KEY" and not re.fullmatch(r"[0-9a-f]{64}", value):
            print(f"  note  {var}: value is not 64 lowercase hex characters; literal scan still applies")

    print("gitignore")
    if _git("rev-parse", "--is-inside-work-tree").returncode != 0:
        bad("not a git work tree; gitignore and tracked-file checks skipped")
    else:
        for p in IN_REPO_SECRET_PATHS:
            rel = _display(p)
            ignored = _git("check-ignore", "-q", "--no-index", "--", rel).returncode == 0
            tracked = _git("ls-files", "--error-unmatch", "--", rel).returncode == 0
            state = "present" if p.exists() else "absent"
            if tracked:
                bad(f"{rel}: TRACKED by git")
            elif ignored:
                ok(f"{rel}: ignored ({state})")
            else:
                bad(f"{rel}: not ignored ({state})")

        print("tracked files")
        hashes = {_sha(v.encode()): var for var, v in loaded.items()}
        files = [f for f in _git("ls-files", "-z").stdout.split("\0") if f]
        hits: list[str] = []
        for rel in files:
            fp = ROOT / rel
            if not fp.is_file():
                continue
            data = fp.read_bytes()
            for m in OPENROUTER_RE.finditer(data.decode("latin-1")):
                hits.append(f"{rel}:{_line_of(data, m.start())}: OpenRouter key pattern")
            if hashes:
                text = data.decode("latin-1")
                for m in HEX64_RE.finditer(text):
                    var = hashes.get(_sha(m.group(0).encode("latin-1")))
                    if var:
                        hits.append(f"{rel}:{_line_of(data, m.start())}: value of {var}")
        if hits:
            for h in hits:
                bad(h)
        else:
            ok(f"no OpenRouter key pattern and no loaded key value in {len(files)} tracked files")

        print("pre-commit hook")
        installed = _hooks_dir() / "pre-commit"
        if not VERSIONED_HOOK.is_file():
            bad(f"versioned hook missing: {_display(VERSIONED_HOOK)}")
        elif not installed.is_file():
            bad(f"{_display(installed)} not installed (run bash steering_extension/local/hooks/install_hooks.sh)")
        elif not os.access(installed, os.X_OK):
            bad(f"{_display(installed)} is not executable")
        elif _sha(installed.read_bytes()) != _sha(VERSIONED_HOOK.read_bytes()):
            bad(f"{_display(installed)} differs from {_display(VERSIONED_HOOK)} (re-run install_hooks.sh)")
        else:
            ok(f"{_display(installed)} installed and matches the versioned copy")

    if problems:
        print(f"{len(problems)} problem(s)")
        return 1
    print("all checks passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--check"]:
        return check()
    if args:
        print(__doc__.strip(), file=sys.stderr)
        print("\nusage: python -m steering_extension.local.keys [--check]", file=sys.stderr)
        return 2
    load_keys()
    return 0


if __name__ == "__main__":
    sys.exit(main())
