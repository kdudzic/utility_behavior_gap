# Source this to export OPENROUTER_API_KEY / VAST_API_KEY without printing them (prints source names only).
# Mirrors steering_extension/local/keys.py. Usage: source steering_extension/local/env.sh
#
# Precedence per variable: process env > ~/.config/utility_behavior_gap/secrets.env (XDG_CONFIG_HOME
# honoured, UBG_SECRETS_FILE overrides) > gitignored in-repo files (steering_extension/spar_*.txt) > .env.
# OPENROUTER_KEY_SOURCE=personal selects the PI's personal key (OPENROUTER_API_KEY_PERSONAL= in
# secrets.env, else the sk-or-v1- token in .openrouter.txt) and never falls back to the SPAR key.
# Safe under `set -euo pipefail` and in bash or zsh.
_ubg_root="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
_ubg_secrets="${UBG_SECRETS_FILE:-${XDG_CONFIG_HOME:-$HOME/.config}/utility_behavior_gap/secrets.env}"
_ubg_secrets_name="$_ubg_secrets"; case "$_ubg_secrets" in "$HOME"/*) _ubg_secrets_name="~${_ubg_secrets#"$HOME"}" ;; esac

# _ubg_envval FILE VAR: value of VAR from a KEY=VALUE file (optional `export `, quotes stripped), else empty.
_ubg_envval() {
  [ -r "$1" ] || return 0
  awk -v k="$2" -v q="'" '
    { line = $0; sub(/^[ \t]*/, "", line); sub(/^export[ \t]+/, "", line) }
    index(line, k "=") == 1 {
      v = substr(line, length(k) + 2); sub(/^[ \t]+/, "", v); sub(/[ \t\r]+$/, "", v)
      c = substr(v, 1, 1); if ((c == "\"" || c == q) && substr(v, length(v), 1) == c) v = substr(v, 2, length(v) - 2)
      print v; exit
    }' "$1"
}
# _ubg_token FILE: first line of a one-key file without whitespace or quotes, else empty.
_ubg_token() { if [ -s "$1" ]; then head -n1 "$1" | tr -d "[:space:]\"'"; fi; }

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  _ubg_v=""; _ubg_s=""
  if [ "${OPENROUTER_KEY_SOURCE:-}" = "personal" ]; then
    _ubg_v="$(_ubg_envval "$_ubg_secrets" OPENROUTER_API_KEY_PERSONAL)"; _ubg_s="$_ubg_secrets_name [OPENROUTER_API_KEY_PERSONAL]"
    if [ -z "$_ubg_v" ] && [ -r "$_ubg_root/.openrouter.txt" ]; then
      _ubg_v="$(grep -m1 -oE 'sk-or-v1-[0-9a-f]{64}' "$_ubg_root/.openrouter.txt" || true)"; _ubg_s=".openrouter.txt (personal)"
    fi
    if [ -z "$_ubg_v" ]; then echo "OPENROUTER_KEY_SOURCE=personal but no personal key was found" >&2; fi
  else
    _ubg_v="$(_ubg_envval "$_ubg_secrets" OPENROUTER_API_KEY)"; _ubg_s="$_ubg_secrets_name"
    if [ -z "$_ubg_v" ]; then
      _ubg_v="$(_ubg_token "$_ubg_root/steering_extension/spar_openrouter.txt")"; _ubg_s="steering_extension/spar_openrouter.txt"
      if [ -n "$_ubg_v" ]; then _ubg_v="$(printf '%s' "$_ubg_v" | grep -m1 -oE 'sk-or-v1-[0-9a-f]{64}' || printf '%s' "$_ubg_v")"; fi
    fi
    if [ -z "$_ubg_v" ]; then _ubg_v="$(_ubg_envval "$_ubg_root/.env" OPENROUTER_API_KEY)"; _ubg_s=".env"; fi
  fi
  if [ -n "$_ubg_v" ]; then export OPENROUTER_API_KEY="$_ubg_v"; echo "OPENROUTER_API_KEY: from $_ubg_s"; fi
fi

if [ -z "${VAST_API_KEY:-}" ]; then
  _ubg_v="$(_ubg_envval "$_ubg_secrets" VAST_API_KEY)"; _ubg_s="$_ubg_secrets_name"
  if [ -z "$_ubg_v" ]; then _ubg_v="$(_ubg_token "$_ubg_root/steering_extension/spar_vastai.txt")"; _ubg_s="steering_extension/spar_vastai.txt"; fi
  if [ -z "$_ubg_v" ]; then _ubg_v="$(_ubg_envval "$_ubg_root/.env" VAST_API_KEY)"; _ubg_s=".env"; fi
  if [ -n "$_ubg_v" ]; then export VAST_API_KEY="$_ubg_v"; echo "VAST_API_KEY: from $_ubg_s"; fi
fi

unset _ubg_v _ubg_s _ubg_root _ubg_secrets _ubg_secrets_name
unset -f _ubg_envval _ubg_token
