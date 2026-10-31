#!/usr/bin/env bash
# Build the OpenAI (ChatGPT / Codex plugin directory) package of the
# infranodus plugin from the same skill files the Claude plugin uses.
#
#   tests/build-openai.sh [--strict]
#
# Output: dist/openai/infranodus/ (unpacked) and dist/infranodus-openai.zip
# with plugin.json, mcp.json, assets/ and skills/infranodus/ at the ZIP root.
#
# Sources:
#   openai/infranodus/{plugin.json,mcp.json,assets/}  OpenAI-only files
#   infranodus/{SKILL.md,references/,scripts/}        the shared skill
#   infranodus/.claude-plugin/plugin.json             version (single source)
#
# Nothing under infranodus/ or .claude-plugin/ is written, so the Claude
# plugin and marketplace are unaffected. --strict fails on placeholders
# (TODO) that must be filled before a directory submission.
set -euo pipefail

STRICT=0
[ "${1:-}" = "--strict" ] && STRICT=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_OPENAI="$ROOT/openai/infranodus"
SRC_SKILL="$ROOT/infranodus"
OUT_DIR="$ROOT/dist/openai/infranodus"
ZIP="$ROOT/dist/infranodus-openai.zip"

command -v jq >/dev/null || { echo "error: jq is required" >&2; exit 1; }
command -v zip >/dev/null || { echo "error: zip is required" >&2; exit 1; }

VERSION="$(jq -r .version "$SRC_SKILL/.claude-plugin/plugin.json")"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+ ]] || { echo "error: bad version '$VERSION'" >&2; exit 1; }

rm -rf "$OUT_DIR" "$ZIP"
mkdir -p "$OUT_DIR/skills/infranodus"

# Manifest with the version taken from the Claude plugin manifest.
jq --arg v "$VERSION" '.version = $v' "$SRC_OPENAI/plugin.json" > "$OUT_DIR/plugin.json"
cp "$SRC_OPENAI/mcp.json" "$OUT_DIR/mcp.json"
cp -R "$SRC_OPENAI/assets" "$OUT_DIR/assets"

# The skill, minus caches, tests and OS junk. No symlinks (rejected by the
# directory), no .claude-plugin/ (Claude-only).
cp "$SRC_SKILL/SKILL.md" "$OUT_DIR/skills/infranodus/SKILL.md"

# The directory rejects a skill description that names another AI assistant,
# model or platform, while the Claude description names Claude, Codex, mem0
# and claude-mem on purpose (it routes those requests to the skill). The
# OpenAI copy gets openai/infranodus/skill-description.txt instead.
if [ -f "$SRC_OPENAI/skill-description.txt" ]; then
	python3 -I - "$OUT_DIR/skills/infranodus/SKILL.md" "$SRC_OPENAI/skill-description.txt" <<'PY'
import re, sys, textwrap
skill, desc_file = sys.argv[1], sys.argv[2]
desc = " ".join(open(desc_file, encoding="utf-8").read().split())
text = open(skill, encoding="utf-8").read()
m = re.match(r"---\n(.*?)\n---\n", text, re.S)
if not m:
    sys.exit("error: SKILL.md has no frontmatter")
lines = m.group(1).split("\n")
out, i = [], 0
while i < len(lines):
    if lines[i].startswith("description:"):
        out.append("description: >-")
        out += ["  " + l for l in textwrap.wrap(desc, 76)]
        i += 1
        while i < len(lines) and (lines[i].startswith(" ") or lines[i] == ""):
            i += 1
        continue
    out.append(lines[i])
    i += 1
open(skill, "w", encoding="utf-8").write("---\n" + "\n".join(out) + "\n---\n" + text[m.end():])
PY
fi
for d in references scripts; do
	[ -d "$SRC_SKILL/$d" ] || continue
	(cd "$SRC_SKILL" && find "$d" -type f \
		! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '.DS_Store' \
		! -path 'scripts/tests/*' -print0) |
		while IFS= read -r -d '' f; do
			mkdir -p "$OUT_DIR/skills/infranodus/$(dirname "$f")"
			cp "$SRC_SKILL/$f" "$OUT_DIR/skills/infranodus/$f"
		done
done

# Checks that mirror the directory's package validation.
fail=0
err() { echo "error: $*" >&2; fail=1; }
warn() { echo "warning: $*" >&2; }

M="$OUT_DIR/plugin.json"
jq -e . "$M" >/dev/null || err "plugin.json is not valid JSON"
jq -e . "$OUT_DIR/mcp.json" >/dev/null || err "mcp.json is not valid JSON"
[ -n "$(find "$OUT_DIR" -type l)" ] && err "symlinks in package"

len() { jq -r "$1 // \"\"" "$M" | tr -d '\n' | wc -m | tr -d ' '; }
chk() { local n; n=$(len "$1"); [ "$n" -le "$2" ] || err "$1 is $n chars (max $2)"; [ "$n" -gt 0 ] || err "$1 is empty"; }
I='.extensions["com.openai"].interface'
chk '.description' 1024
chk "$I.displayName" 30
chk "$I.shortDescription" 30
chk "$I.longDescription" 4000
chk "$I.developerName" 80
[ "$(jq -r "$I.defaultPrompt | length" "$M")" -le 3 ] || err "more than 3 starter prompts"
jq -r "$I.defaultPrompt[]" "$M" | while IFS= read -r p; do [ "${#p}" -le 128 ] || echo "error: starter prompt over 128 chars: $p" >&2; done
for k in logo composerIcon; do
	p="$(jq -r "$I.$k" "$M")"; [ -f "$OUT_DIR/$p" ] || err "$k points at missing file $p"
done
R='.extensions["com.openai"].review.test_cases'
[ "$(jq -r "$R.positive | length" "$M")" = 5 ] || err "need exactly 5 positive test cases"
[ "$(jq -r "$R.negative | length" "$M")" = 3 ] || err "need exactly 3 negative test cases"
desc_chars=$(awk 'NR==1{next} /^---$/{exit} {print}' "$OUT_DIR/skills/infranodus/SKILL.md" |
	sed -n '/^description:/,/^[a-z]*:/p' | sed '1s/^description:[ >-]*//;$d' | tr -s ' \n' ' ' | wc -m | tr -d ' ')
[ "$desc_chars" -le 1024 ] || err "SKILL.md description is $desc_chars chars (max 1024)"

# No other AI assistant, model or platform in the plugin name, listing text
# or skill description (directory rule).
SKILL_DESC=$(python3 -I -c 'import sys,yaml; t=open(sys.argv[1],encoding="utf-8").read().split("---")[1]; print(yaml.safe_load(t)["description"])' "$OUT_DIR/skills/infranodus/SKILL.md" 2>/dev/null) || err "SKILL.md frontmatter is not valid YAML"
LISTING=$(jq -r '[.name, .description, (.extensions["com.openai"].interface | .displayName, .shortDescription, .longDescription, (.capabilities // [] | join(" ")), (.defaultPrompt // [] | join(" "))), (.extensions["com.openai"].publication.release_notes // "")] | join("\n")' "$M")
NAMES='claude|anthropic|chatgpt|codex|openai|gpt-?[0-9]|gemini|bard|copilot|cursor|windsurf|perplexity|grok|llama|mistral|deepseek|mem0|claude-mem'
hits=$(printf '%s\n%s\n' "$LISTING" "$SKILL_DESC" | { grep -o -i -w -E "$NAMES" || true; } | sort -u | tr '\n' ' ')
[ -z "$hits" ] || err "listing or skill description names other AI products: $hits"

if grep -q 'TODO' "$M"; then
	if [ "$STRICT" = 1 ]; then err "placeholders left in plugin.json (TODO)"; else warn "placeholders left in plugin.json (TODO): fill before submitting"; fi
fi
[ "$fail" = 0 ] || exit 1

(cd "$OUT_DIR" && zip -qrX "$ZIP" .)
echo "Built $ZIP (version $VERSION, $(unzip -Z1 "$ZIP" | wc -l | tr -d ' ') entries)"
