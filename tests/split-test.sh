#!/usr/bin/env bash
# Isolated cross-repo test for the infranodus/skills + infranodus/skills-lab split.
# Every claude call runs under a throwaway CLAUDE_CONFIG_DIR, so ~/.claude is never touched.
# Usage: tests/split-test.sh [path-to-this-repo] [branch] [pre-split-ref]   (needs claude, git, jq, npx, curl)
set -u

MAIN_REPO=$(cd "${1:-$(dirname "$0")/..}" && pwd)   # absolute: the script cds into its work dir
BRANCH=${2:-restructure/main-and-lab}
OLD_REF=${3:-v1.7.3}   # last release before the split, for the upgrade check
LAB_GH=infranodus/skills-lab
WORK=$(mktemp -d "${TMPDIR:-/tmp}/split-test.XXXXXX")
cd "$WORK" || exit 1

MAIN_IDS="infranodus llm-wiki ontology-generator project-learnings shifting-perspective cognitive-variability writing-assistant seo-analysis"
LAB_IDS="actionize critical-perspective embodied-navigation perspective-reversal rhetorical-analyst shopping-assistant vipassana-llm youtube-viral-optimizer"
MCP_IDS="infranodus llm-wiki project-learnings shifting-perspective seo-analysis"

PASS=0; FAIL=0; FAILED=()
ok()   { PASS=$((PASS+1)); echo "  PASS  $*"; }
bad()  { FAIL=$((FAIL+1)); FAILED+=("$*"); echo "  FAIL  $*"; }
check() { local desc=$1; shift; if "$@" >/dev/null 2>&1; then ok "$desc"; else bad "$desc"; fi; }
eq()   { [ "$2" = "$3" ] && ok "$1 ($2)" || bad "$1 (got '$2', want '$3')"; }

c()        { CLAUDE_CONFIG_DIR="$CFG" claude "$@"; }
details()  { c plugin details "$1" 2>&1; }
n_skills() { details "$1" | sed -n 's/^ *Skills (\([0-9]*\)).*/\1/p'; }
n_mcp()    { details "$1" | sed -n 's/^ *MCP servers (\([0-9]*\)).*/\1/p'; }
version()  { c plugin list --json | jq -r --arg id "$1" '.[] | select(.id==$id) | .version'; }
path_of()  { c plugin list --json | jq -r --arg id "$1" '.[] | select(.id==$id) | .installPath'; }

git clone -q --branch "$BRANCH" "$MAIN_REPO" "$WORK/main-branch"
git clone -q --branch "$OLD_REF" "$MAIN_REPO" "$WORK/main-master" 2>/dev/null

echo "== A. Fresh install from $BRANCH (Lab ids via git-subdir over GitHub)"
CFG=$WORK/cfg-fresh; mkdir -p "$CFG"
check "marketplace add (branch clone)" c plugin marketplace add "$WORK/main-branch"
for id in $MAIN_IDS infranodus-all $LAB_IDS; do
  check "install $id@infranodus-skills" c plugin install "$id@infranodus-skills"
done
# Each main plugin's expected version is the one in its own manifest on the branch.
want_version() {
  local src; src=$(jq -r --arg id "$1" '.plugins[] | select(.name==$id) | .source' "$WORK/main-branch/.claude-plugin/marketplace.json")
  jq -r .version "$WORK/main-branch/$src/.claude-plugin/plugin.json"
}
eq "infranodus-all skills" "$(n_skills infranodus-all@infranodus-skills)" 8
eq "infranodus-all MCP servers" "$(n_mcp infranodus-all@infranodus-skills)" 1
eq "infranodus-all version" "$(version infranodus-all@infranodus-skills)" "$(want_version infranodus-all)"
for id in $MAIN_IDS; do eq "$id version" "$(version "$id@infranodus-skills")" "$(want_version "$id")"; done
for id in $MCP_IDS; do eq "$id MCP servers" "$(n_mcp "$id@infranodus-skills")" 1; done
for id in $LAB_IDS; do
  eq "$id (Lab, by id) version" "$(version "$id@infranodus-skills")" 1.8.0
  p=$(path_of "$id@infranodus-skills")
  check "$id installed SKILL.md present" test -f "$p/SKILL.md"
  check "$id manifest points at skills-lab" grep -q "infranodus/skills-lab" "$p/.claude-plugin/plugin.json"
done

echo "== B. Lab marketplace from GitHub"
CFG=$WORK/cfg-lab; mkdir -p "$CFG"
check "marketplace add $LAB_GH" c plugin marketplace add "$LAB_GH"
check "install skills-lab-all@infranodus-skills-lab" c plugin install skills-lab-all@infranodus-skills-lab
eq "skills-lab-all skills" "$(n_skills skills-lab-all@infranodus-skills-lab)" 8
eq "skills-lab-all MCP servers" "$(n_mcp skills-lab-all@infranodus-skills-lab)" 1
eq "skills-lab-all version" "$(version skills-lab-all@infranodus-skills-lab)" 1.8.0
check "install actionize@infranodus-skills-lab" c plugin install actionize@infranodus-skills-lab

echo "== C. MCP server registrations with infranodus + seo-analysis + infranodus-all (info)"
CFG=$WORK/cfg-fresh
(cd "$WORK" && c mcp list 2>&1) | grep -i "infranodus" | sed 's/^/        /'
N=$( (cd "$WORK" && c mcp list 2>&1) | grep -ci "mcp.infranodus.com")
echo "        -> $N entries point at mcp.infranodus.com (1 = deduplicated, >1 = one per plugin)"

echo "== D. Upgrade: user on $OLD_REF -> $BRANCH"
CFG=$WORK/cfg-upgrade; mkdir -p "$CFG"
check "marketplace add ($OLD_REF clone)" c plugin marketplace add "$WORK/main-master"
check "install infranodus-all ($OLD_REF)" c plugin install infranodus-all@infranodus-skills
check "install actionize ($OLD_REF, relative source)" c plugin install actionize@infranodus-skills
eq "before: infranodus-all skills" "$(n_skills infranodus-all@infranodus-skills)" 16
eq "before: actionize version" "$(version actionize@infranodus-skills)" 1.7.3
git -C "$WORK/main-master" checkout -q "$BRANCH"
check "marketplace update infranodus-skills" c plugin marketplace update infranodus-skills
check "plugin update infranodus-all" c plugin update infranodus-all@infranodus-skills
check "plugin update actionize" c plugin update actionize@infranodus-skills
eq "after: infranodus-all skills" "$(n_skills infranodus-all@infranodus-skills)" 8
eq "after: infranodus-all version" "$(version infranodus-all@infranodus-skills)" "$(want_version infranodus-all)"
eq "after: actionize version (now from Lab)" "$(version actionize@infranodus-skills)" 1.8.0
check "after: actionize manifest points at skills-lab" \
  grep -q "infranodus/skills-lab" "$(path_of actionize@infranodus-skills)/.claude-plugin/plugin.json"

echo "== E. npx skills + release zips"
check "npx skills lists Lab repo" sh -c "npx -y skills add $LAB_GH --list 2>&1 | grep -q actionize"
check "npx skills lists branch clone (seo-analysis)" sh -c "npx -y skills add '$WORK/main-branch' --list 2>&1 | grep -q seo-analysis"
check "npx skills: branch clone has no Lab skills" sh -c "! npx -y skills add '$WORK/main-branch' --list 2>&1 | grep -q actionize"
for z in $LAB_IDS; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -L "https://github.com/$LAB_GH/releases/latest/download/$z.zip")
  eq "Lab zip $z.zip" "$code" 200
done

echo
echo "== $PASS passed, $FAIL failed   (work dir: $WORK)"
for f in ${FAILED[@]+"${FAILED[@]}"}; do echo "   - $f"; done
[ "$FAIL" -eq 0 ]
