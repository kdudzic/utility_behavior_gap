#!/usr/bin/env bash
# Keep this project's Claude Code session directory in sync with a private git repo, so the
# same conversation can be resumed on several machines. Called by hooks in .claude/settings.json:
#   context_sync.sh start   (SessionStart)  fetch; warn if another machine pushed newer context
#   context_sync.sh save    (Stop, SessionEnd) commit + push in the background
# No-op unless ~/.claude/projects/<slug-of-repo-path>/ is a git repo whose origin contains
# CONTEXT_REMOTE_MATCH, so clones of the public repo by other people are unaffected.
# Never prints key values. Never force-pushes. Log: ~/.cache/claude-context-sync.log
set -uo pipefail

MATCH="${CONTEXT_REMOTE_MATCH:-utility-behavior-gap-claude-context}"
REPO="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
DIR="$HOME/.claude/projects/$(printf '%s' "$REPO" | sed 's/[^A-Za-z0-9]/-/g')"
LOG="$HOME/.cache/claude-context-sync.log"
mkdir -p "$(dirname "$LOG")"

active() {
  [ -d "$DIR/.git" ] && git -C "$DIR" remote get-url origin 2>/dev/null | grep -q "$MATCH"
}

start() {
  if ! active; then
    [ -d "$DIR/.git" ] || exit 0
    echo "context sync: $DIR is a git repo but origin does not match $MATCH; sync disabled."; exit 0
  fi
  if ! timeout 20 git -C "$DIR" fetch -q origin 2>>"$LOG"; then
    echo "context sync: could not reach the context repo (offline?). Continuing without sync check."; exit 0
  fi
  local ahead behind
  read -r ahead behind < <(git -C "$DIR" rev-list --left-right --count HEAD...origin/main 2>/dev/null || echo "0 0")
  if [ "${behind:-0}" -gt 0 ]; then
    cat <<EOF
CONTEXT SYNC WARNING: the context repo on GitHub has $behind newer commit(s) from another machine.
This session was loaded from an older copy. Tell the user, before doing anything else:
quit Claude Code, run \`git -C "$DIR" pull\`, then relaunch with \`claude --resume\`.
Do not continue working in this session until they have done so.
EOF
  elif [ "${ahead:-0}" -gt 0 ]; then
    echo "context sync: $ahead local commit(s) not yet pushed; they will be pushed after the next turn."
  else
    echo "context sync: session context is up to date with the private context repo."
  fi
}

save_now() {
  cd "$DIR" || exit 0
  exec 9>"$DIR/.git/context-sync.lock"
  flock -n 9 || exit 0   # another save is running
  git add -A
  git diff --cached --quiet && { git push -q origin main 2>/dev/null; exit 0; }
  # refuse to commit key material: OpenRouter pattern, and literal loaded key values
  local secrets="${XDG_CONFIG_HOME:-$HOME/.config}/utility_behavior_gap/secrets.env"
  if git diff --cached -U0 | grep -qE 'sk-or-v1-[0-9a-f]{64}' \
     || { [ -r "$secrets" ] && git diff --cached -U0 | grep -qF -f <(sed -n 's/^[A-Z_]*API_KEY[A-Z_]*=//p' "$secrets" | tr -d "\"' " | grep -v '^$'); }; then
    git reset -q
    echo "$(date -Is) BLOCKED: key material in session files; nothing committed. Inspect $DIR manually." >>"$LOG"
    exit 0
  fi
  local who; who="$(git config user.name || echo claude-context-sync)"
  git -c user.name="$who" -c user.email="$(git config user.email || echo noreply@localhost)" \
    commit -q -m "sync $(hostname -s) $(date -u +%Y-%m-%dT%H:%MZ)"
  if ! timeout 60 git push -q origin main 2>>"$LOG"; then
    echo "$(date -Is) PUSH REJECTED or failed: another machine may have pushed. Not forcing. Resolve by hand in $DIR." >>"$LOG"
  fi
}

case "${1:-}" in
  start) start ;;
  save)  active || exit 0; ( save_now ) >>"$LOG" 2>&1 </dev/null & disown; exit 0 ;;
  save-foreground) active || exit 0; save_now ;;
  *) echo "usage: $0 start|save|save-foreground"; exit 1 ;;
esac
