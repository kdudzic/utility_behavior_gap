#!/usr/bin/env bash
# Install the versioned git hooks of this directory into the clone's hook directory (honours core.hooksPath).
# Usage: bash steering_extension/local/hooks/install_hooks.sh
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(git -C "$here" rev-parse --show-toplevel)"
hooks_dir="$(git -C "$root" rev-parse --git-path hooks)"
case "$hooks_dir" in /*) ;; *) hooks_dir="$root/$hooks_dir" ;; esac
mkdir -p "$hooks_dir"
for hook in pre-commit; do
  install -m 755 "$here/$hook" "$hooks_dir/$hook"
  echo "installed $hooks_dir/$hook"
done
