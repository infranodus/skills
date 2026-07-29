#!/usr/bin/env bash
# install.sh — install the InfraNodus skills into an agent's skills directory.
#
# Copies (or symlinks) the skills from this repo into ~/.claude/skills/ so
# they load in Claude Code (and any agent reading the same layout). The
# installed directory name determines the slash command, so infranodus-cli
# is installed as "infranodus" -> /infranodus.
#
# Usage:
#   ./install.sh                 # copy into ~/.claude/skills/
#   ./install.sh --project       # copy into ./.claude/skills/ (current project)
#   ./install.sh --symlink       # symlink instead of copy (dev mode: edits in
#                                # this repo apply instantly, no re-install)
#   ./install.sh --core-only     # only infranodus (skip llm-wiki, ontology-generator)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_BASE="$HOME/.claude/skills"
MODE="copy"
CORE_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --project)   TARGET_BASE="$(pwd)/.claude/skills" ;;
    --symlink)   MODE="symlink" ;;
    --core-only) CORE_ONLY=1 ;;
    -h|--help)   sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg (see --help)"; exit 1 ;;
  esac
done

# repo folder -> installed name (= slash command / registry name)
SKILLS=("infranodus-cli:infranodus")
if [ "$CORE_ONLY" -eq 0 ]; then
  SKILLS+=("skill-ontology-creator:ontology-generator" "skill-llm-wiki:llm-wiki")
fi

mkdir -p "$TARGET_BASE"
echo "Installing into: $TARGET_BASE ($MODE)"
echo

for pair in "${SKILLS[@]}"; do
  src="$REPO_DIR/${pair%%:*}"
  dst="$TARGET_BASE/${pair##*:}"
  if [ ! -f "$src/SKILL.md" ]; then
    echo "  SKIP ${pair%%:*} (no SKILL.md found)"
    continue
  fi
  rm -rf "$dst"
  if [ "$MODE" = "symlink" ]; then
    ln -sfn "$src" "$dst"
  else
    cp -R "$src" "$dst"
  fi
  echo "  ${pair%%:*} -> $dst"
done

# --- Register the trigger in CLAUDE.md -------------------------------------
# Two separate registrations exist, with distinct markers so they never
# clobber each other:
#   infranodus-skill:*  (here) - the always-loaded pointer that makes
#                        /infranodus discoverable, in .claude/CLAUDE.md
#   infranodus:*        (upload_scopes.py --register-project) - the
#                        per-project rules block in <project>/CLAUDE.md,
#                        written only once a project actually has graphs
if [ "$TARGET_BASE" = "$HOME/.claude/skills" ]; then
  CLAUDE_MD="$HOME/.claude/CLAUDE.md"
  SKILL_PATH="~/.claude/skills/infranodus/SKILL.md"
else
  CLAUDE_MD="$(pwd)/.claude/CLAUDE.md"
  SKILL_PATH=".claude/skills/infranodus/SKILL.md"
fi

echo
if command -v python3 >/dev/null 2>&1; then
  python3 - "$CLAUDE_MD" "$SKILL_PATH" <<'PY'
import pathlib, sys

path, skill = pathlib.Path(sys.argv[1]), sys.argv[2]
BEGIN, END = "<!-- infranodus-skill:begin -->", "<!-- infranodus-skill:end -->"
block = f"""{BEGIN}
# infranodus
- **infranodus** (`{skill}`) - any text, repo, or vault to a knowledge graph; topics, content gaps, GraphRAG retrieval. Trigger: `/infranodus`
When the user types `/infranodus`, use the installed infranodus skill before doing anything else.
When a project root has `infranodus/manifest.json`, answer questions about its themes, concepts, rationale, or gaps by querying those graphs first (see that project's CLAUDE.md for the rules).
{END}
"""

if not path.exists():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(block, encoding="utf-8")
    action = "created"
else:
    content = path.read_text(encoding="utf-8")
    if BEGIN in content and END in content:
        start, end = content.index(BEGIN), content.index(END) + len(END)
        updated = content[:start] + block.rstrip("\n") + content[end:]
        action = "unchanged" if updated == content else "updated"
        if action == "updated":
            path.write_text(updated, encoding="utf-8")
    else:
        path.write_text(content.rstrip("\n") + "\n\n" + block, encoding="utf-8")
        action = "registered"
print(f"CLAUDE.md {action}: {path}")
PY
else
  echo "  [--] python3 not found — skipped CLAUDE.md registration."
  echo "       Add a pointer to $SKILL_PATH manually if you want /infranodus"
  echo "       surfaced automatically."
fi

echo
echo "Transport preflight (runtime fallback order: native MCP > mcporter > install):"

if grep -rqs '"infranodus"' "$HOME/.claude.json" "$HOME/.claude/settings.json" \
     "$(pwd)/.mcp.json" 2>/dev/null; then
  echo "  [ok] an 'infranodus' MCP server appears in your agent config —"
  echo "       native tools will be used directly; nothing else needed."
elif command -v mcporter >/dev/null 2>&1; then
  echo "  [ok] mcporter found: $(command -v mcporter)"
  if mcporter list 2>/dev/null | grep -q infranodus; then
    echo "       'infranodus' server is configured."
  else
    echo "       'infranodus' server NOT configured yet — see Setup & Auth in"
    echo "       the skill (mcporter config add infranodus ...)."
  fi
else
  echo "  [--] no native MCP config detected and mcporter not installed."
  echo "       The skill will offer to set this up on first use, or run now:"
  echo "         npm install -g mcporter"
  echo "         # then, with your key from infranodus.com -> settings -> API:"
  echo "         mcporter config add infranodus --url https://mcp.infranodus.com/ \\"
  echo "           --transport http --header \"accept=application/json, text/event-stream\" \\"
  echo "           --header \"Authorization=Bearer \$INFRANODUS_API_KEY\" --scope home"
fi

if [ -z "${INFRANODUS_API_KEY:-}" ]; then
  echo "  [--] INFRANODUS_API_KEY is not set (needed for mcporter transport only)."
fi

echo
echo "Done. In Claude Code, /infranodus is now available (restart the session"
echo "if it was already open). Extraction works offline; upload/queries use"
echo "whichever transport the preflight found."
