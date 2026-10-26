# Roadmap: main repo + InfraNodus Skills Lab

Status as of 2026-10-26, branch `restructure/main-and-lab`. This branch makes
structural and documentation changes only; no `SKILL.md` instructions were
changed. Line numbers were checked against `8e59daf` (v1.7.3) and will drift;
search for the quoted text if they do.

## 1. Decisions

- **No rename.** `infranodus/skills` keeps its name. The marketplace name stays
  `infranodus-skills`, so install ids such as `infranodus@infranodus-skills`
  keep working. No GitHub settings change.
- **Front door:** the core `infranodus` skill. Headline: *Knowledge graph +
  gap finder for your notes, vault or agent memory: shows what's missing and
  what to write next.* The measured, deterministic graph is the proof, not the
  pitch.
- **Stays here (8):** `infranodus`, `llm-wiki`, `ontology-generator`
  (`skill-ontology-creator`), `project-learnings`, `shifting-perspective`,
  `cognitive-variability`, `writing-assistant`, `seo-analysis`.
- **Moved to InfraNodus Skills Lab (8):** `actionize`, `critical-perspective`,
  `embodied-navigation`, `perspective-reversal`, `rhetorical-analyst`,
  `shopping-assistant` (`skill-shopping`), `vipassana-llm`
  (`skill-vipassana-meditation`), `youtube-viral-optimizer`
  (`skill-viral-videos`).
- **Lab repo: `infranodus/skills-lab`** (decided), marketplace
  `infranodus-skills-lab`, bundle `skills-lab-all`. Local folder
  `~/Software/skills/InfraNodus-Skills-Lab`.
- **Audience:** AI researchers, Obsidian users, general researchers, content
  publishers, mostly not terminal users, so the README puts the no-terminal
  path (InfraNodus connector + release-zip skill upload) first.

## 2. What this branch changed

| Change | Where |
|---|---|
| Moved-skill entries keep their ids but use a `git-subdir` source (`url: infranodus/skills-lab`, `path: skill-…`). The `github` source type has no subdirectory field, so `git-subdir` is the right type for a multi-skill repo | `.claude-plugin/marketplace.json` |
| `infranodus-all` lists only the 8 remaining skills | marketplace entry + root `.claude-plugin/plugin.json` |
| Old folders of moved skills contain only a stub `README.md` (no `SKILL.md`, no `.claude-plugin/`) | `skill-actionize/` … `skill-vipassana-meditation/` |
| Outcome-led descriptions + keywords (manifest text only) | marketplace + 5 `plugin.json` files |
| InfraNodus MCP server declared in the llm-wiki plugin | `skill-llm-wiki/.claude-plugin/plugin.json` |
| README: headline, no-terminal install first, workflow with gaps at the centre, "What gets uploaded and where", "Moved to InfraNodus Skills Lab", glossary | `README.md` |
| Track this file only (rest of `docs/` stays local) | `.gitignore` |

No change was needed in `install.sh` (it only installs `infranodus`,
`ontology-generator`, `llm-wiki`, `project-learnings`) or
`.github/workflows/release.yml` (it globs `skill-*/` + `infranodus/` and skips
folders without `SKILL.md`, so the stubs produce no zip).

**Not carried over from `restructure/knowledge-front-door`:** the
`infranodus-knowledge` bundle (with 8 focused skills, `infranodus-all` is the
bundle; a second, overlapping bundle adds a double-install trap), the
optional-hooks scaffold that lived inside it (kept as a TODO below), and the
rename plan.

**Lab repo (local only):** `~/Software/skills/InfraNodus-Skills-Lab`, branch `main`.
Plain copy via `git archive` (content identical to `master` @ `8e59daf`,
v1.7.3; history not preserved, it remains in this repo). It has its own
`.claude-plugin/marketplace.json` (`infranodus-skills-lab`) with the same 8
plugin ids plus a `skills-lab-all` bundle, the copied `release.yml`,
`LICENSE`, `NOTICE`, and a README. Manifest URLs point at
`https://github.com/infranodus/skills-lab`.

## 3. Go-live order

Do not merge this branch before step 1. Until the Lab repo exists, the 8
moved ids cannot be installed from `infranodus-skills`.

1. Create the Lab repo on GitHub, bump its plugin versions (see step 3),
   push `main` and tag `v1.8.0` so
   its release workflow builds zips, including the legacy `skill-*.zip`
   aliases.
2. Cross-repo test (section 4), then merge this branch and tag a release here.
3. Bump plugin versions above 1.7.3 in **both** repos at release time.
   Upgrade simulation (local git server, throwaway config): without a bump,
   `claude plugin update` reports "already at the latest version (1.7.3)" and
   keeps the cached 16-skill copy, and by-id installs of Lab skills never
   switch to the Lab repo. With 1.8.0 in both repos, `infranodus-all` drops
   to the remaining skills and by-id Lab installs are fetched from the Lab
   repo (restart needed).
4. Website: update infranodus.com `/skills` and `/about/knowledge-base`
   (headline, no-terminal install, workflow, Lab link).

### Known breakages to announce

- `infranodus-all` no longer contains the 8 Lab skills, and their command
  prefix changes from `/infranodus-all:<skill>` to `/<skill>:<skill>` when
  they are installed by id.
- `npx skills add infranodus/skills --skill <lab-skill>` stops finding them;
  use `npx skills add infranodus/skills-lab --skill <lab-skill>`.
- `npx skills` users who installed all 16 keep the Lab copies, unmaintained:
  re-running `npx skills add infranodus/skills -g` does not remove them. To
  clean up: `npx skills remove actionize critical-perspective
  embodied-navigation perspective-reversal rhetorical-analyst
  shopping-assistant vipassana-llm youtube-viral-optimizer -g`, then
  `npx skills add infranodus/skills-lab -g` if still wanted.
- `install.sh` never installed Lab skills; nothing changes for its users.
- Release zips for Lab skills (`actionize.zip`, `skill-shopping.zip`, …)
  stop appearing in new releases here, so
  `releases/latest/download/<lab-skill>.zip` links on this repo break after
  the next release. Old releases keep them. Point links at the Lab repo's
  releases.
- If someone adds both marketplaces and installs a Lab skill from each, it
  loads twice. README says to pick one.

## 4. Tests

Done locally on this branch (see the commit that added this file for the
run):

- `claude plugin validate` on both repos and every touched plugin folder;
  `jq .` on every JSON.
- Throwaway `CLAUDE_CONFIG_DIR`: local marketplace add of this repo, install
  of every remaining id + `infranodus-all`; moved ids attempted.
- Temporary (uncommitted) copy of the marketplace with the Lab entries'
  `git-subdir` `url` pointed at `file://…/InfraNodus-Skills-Lab` to simulate the
  cross-repo install.
- `install.sh --project` in a temp dir; `npx skills add . --list` on both
  repos.

Still to verify after the Lab repo is pushed:

```
export CLAUDE_CONFIG_DIR=$(mktemp -d)
claude plugin marketplace add infranodus/skills
claude plugin install actionize@infranodus-skills        # git-subdir over GitHub
claude plugin install infranodus-all@infranodus-skills   # 8 skills
claude plugin marketplace add infranodus/skills-lab
claude plugin install skills-lab-all@infranodus-skills-lab
npx skills add infranodus/skills-lab --list
curl -sIL https://github.com/infranodus/skills-lab/releases/latest/download/actionize.zip
```

Also: an existing user who installed a moved id from the old relative-path
source must get the Lab copy on `claude plugin marketplace update
infranodus-skills` + `claude plugin update <id>`.

## 5. TODOs (not done here)

### Router skill

- A research-cycle router skill that takes the user through research →
  analyze gaps → collect/curate → refine → publish and hands off to the right
  skill. Out of scope for this branch.

### Skill text that mentions moved skills (SKILL.md edits, deferred)

All of these already say "only if the skill is available", so nothing
breaks; they just point at the old repo or at skills that now live in Lab.

- `infranodus/SKILL.md` L189: "installed from https://github.com/infranodus/skills";
  L228-245 list critical-perspective, rhetorical-analyst,
  perspective-reversal, embodied-navigation, vipassana-meditation.
- `infranodus/references/repo-graph.md` L576 (actionize).
- `skill-llm-wiki/SKILL.md` L490-516 (actionize hand-off).
- `skill-shifting-perspective/SKILL.md` L184,
  `skill-cognitive-variability/SKILL.md` L252, L300 (critical perspective).

### Behavior

1. **Keep a local copy by default.** The core flow deletes scope files after
   upload: `infranodus/SKILL.md` L129-130 ("there are no local content
   files") and L166-168; `infranodus/references/repo-graph.md` L261-265;
   `infranodus/scripts/upload_scopes.py` L1492, L1510, L1610 (opt-out
   `--keep-scopes`, L76 / L1376). Flip the default.
2. **One credential policy.** `skill-llm-wiki/scripts/upload_wiki_ontology.py`
   L71-131 reads keys from `.mcp.json`, `~/.claude.json`,
   `~/.claude/settings.json`, `~/.cursor/mcp.json`, `~/.codex/config.json`;
   the core skill says it never reads credentials from config files
   (`infranodus/SKILL.md` L63-73; `upload_scopes.py` ~L119, L1300-1340).
   Same claim in `skill-llm-wiki/references/knowledge-graphs.md` L79 and the
   `install.sh` preflight text L137-138. Align on env-only + host allowlist.
3. **Measured scan default in llm-wiki** (`skill-llm-wiki/SKILL.md` L321 only
   offers it), and fix the stale "delete the graph in InfraNodus first"
   rebuild text on the same line, in `references/knowledge-graphs.md` L79 and
   in `upload_wiki_ontology.py` L25-27, L371-374, L436-448 (the core skill now
   rebuilds in place: `upload_scopes.py --force`).
4. **Layout auto-detection** in the core skill (today only `is_vault`,
   `infranodus/scripts/repo2statements.py` L434-445): Obsidian, Karpathy
   `raw/`+`wiki/`, graphify export, plain docs; report exclusions.
5. **Graph export/import:** NetworkX node-link `graph.json` + GraphML out,
   graphify `graph.json` in.
6. **gap-lint rule** next to the llm-wiki lint workflow
   (`skill-llm-wiki/SKILL.md` L238-247).
7. **Opt-in, local-only hooks** (never auto-registered, no network, no
   credentials).
8. **Stub pages opt-in** for gap concepts without a page (llm-wiki asks about
   auto-creating entity pages at L277; lint lists missing pages at L244).

### Planned first run

`/infranodus gaps` on the current folder: show the detected layout and what
was excluded, confirm what will be uploaded (file count, size), output 5-7
clusters with key files, 3 gaps written as prompts, 3 central concepts, write
`gaps.md` + `graph.json` locally, end with one next step.

**Metrics:** share of first runs that produce `gaps.md`; share of users who
run again within 7 days. No telemetry exists; decide on server-side counting
from graph creation or an explicit opt-in.

**Dogfood:** 3-5 public vaults/wikis of different shapes, two raters score
the top 10 gaps per corpus on specific / true / actionable (0-2 each).
