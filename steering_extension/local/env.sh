# Source this to export OPENROUTER_API_KEY / VAST_API_KEY from the gitignored key files.
# Usage: source steering_extension/local/env.sh
_root="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  for f in "$_root/steering_extension/spar_openrouter.txt" "$_root/.openrouter.txt"; do
    if [ -s "$f" ]; then export OPENROUTER_API_KEY="$(head -n1 "$f" | tr -d '[:space:]')"; echo "OPENROUTER_API_KEY: from ${f#$_root/}"; break; fi
  done
fi
if [ -z "${VAST_API_KEY:-}" ] && [ -s "$_root/steering_extension/spar_vastai.txt" ]; then
  export VAST_API_KEY="$(head -n1 "$_root/steering_extension/spar_vastai.txt" | tr -d '[:space:]')"
fi
unset _root
