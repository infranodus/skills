# TODO: Integrating `infranodus-cli` and `skill-llm-wiki`

*Drafted 2026-08-01. Goal: make the two skills compose cleanly — the analytical skill (`infranodus-cli`) and the generative one (`skill-llm-wiki`) — without duplicating each other's internals in prose that drifts. Proposal only; nothing below is implemented yet.*

---

## Background: what each skill produces

| | `infranodus-cli` | `skill-llm-wiki` |
|---|---|---|
| **Role** | Maps what already exists: deterministic scan of a repo/vault into saved InfraNodus graphs, report, CLAUDE.md query block. Authors no new content. | Writes a new knowledge layer: LLM-authored wiki pages, curated ontologies, schema, todos. Compounds over time. |
| **In an Obsidian vault** | X-ray of the vault as-is (content + link topology → `infranodus/` scopes, graphs, report). | Treats the vault as raw sources and writes a new wiki on top. |
| **In a folder of PDFs** | Near-useless — the scanner reads md/code/git, not PDFs. | Built for it — PDF→md conversion, per-source summaries, gap-driven research plan. |
| **`infranodus/` artifacts** | `generated: true` scopes — regenerated wholesale by scripts, never hand-edited. | `curated: true` ontologies — append-only, line-by-line editorial changes only. |

They already share one integration point: the `infranodus/` folder, `manifest.json`, and the curated/generated policy flags that keep them out of each other's files. That is a **data contract**, and data contracts survive refactors; prose descriptions of another skill's internals don't.

## The problem

`skill-llm-wiki` currently hard-codes `infranodus-cli` internals — the script name `repo2statements.py`, its flags, the `parentAndConcepts` contract, and the install path `~/.claude/skills/infranodus/`. That path doesn't match the actual install directory (`infranodus-cli`), so the "offer the vault scan" step already silently fails. Duplicated prose has drifted once and will keep drifting. Meanwhile `infranodus-cli` has no awareness of llm-wiki at all: launched on a PDF corpus it runs an empty scan instead of routing, and its query mode doesn't explicitly claim the `wiki-*` curated graphs.

## Proposal

### 1. Extract the shared contract into one reference doc

A short `infranodus-folder-contract.md` (living in this repo; shipped into both skills' `references/` by `install.sh`, or linked as a shared doc) defining the five things the skills must agree on:

- `infranodus/` layout (flat, at project root)
- `manifest.json` schema (`scopes: {file, policy, graphName, url, updated}`)
- the curated vs generated policy and its frontmatter flags
- `wikilinksMode` declarations and what each mode means for upload
- graph naming (`repo-<project>-<scope>` vs `wiki-<project>-<scope>`)

Both SKILL.md files then say "follow the folder contract in references/…" instead of each re-explaining it. Today those rules exist twice in slightly different words — that's the drift engine.

### 2. `skill-llm-wiki`: replace script knowledge with skill invocation

Everywhere llm-wiki names `repo2statements.py`, its path, or its flags (Phase 6 tooling, Phase 9.4 step 4), replace with capability-level language:

> If the `infranodus` skill is listed among available skills, invoke it (Skill tool) to scan a repo or map the vault's link structure — it writes `generated: true` scopes into the same `infranodus/` folder and manifest; refresh generated scopes by re-invoking it, never by editing the files.

Detection by **skill listing**, not hard-coded filesystem path. The cli skill can then rename, restructure, or rewrite its scanner freely without breaking llm-wiki.

### 3. `infranodus-cli`: two small awareness rules, not a wiki tutorial

- **Routing hint** — in the repo/vault workflow's "ask what to build" step, when the folder is mostly PDFs or non-minable documents (the case where the scanner produces nothing), say so and suggest llm-wiki ("this corpus needs LLM-authored summarization; the llm-wiki skill builds that") instead of running an empty scan.
- **Coexistence rule** — in query mode, treat *all* manifest scopes as queryable, including `wiki-*` curated graphs llm-wiki created, and never write into files whose manifest entry says `curated`. The manifest `policy` field is the runtime signal; the cli skill never needs to know llm-wiki by name for this.

### 4. Put the routing decision in the skill descriptions

Skill selection is driven by descriptions, so that's the highest-leverage place for the two-sentence version of everything above. One clause each:

- `infranodus-cli` description: *"for building and maintaining an LLM-written knowledge base from sources, prefer the llm-wiki skill."*
- `skill-llm-wiki` description: *"for a one-shot structural map of an existing repo/vault without authoring new content, prefer the infranodus skill."*

### Why this shape (and not fuller mutual embedding)

The asymmetry is deliberate: llm-wiki legitimately **orchestrates** the cli skill (as it does ontology-creator and actionize), while the cli skill only needs to **route away** and **not clobber** — it should never depend on llm-wiki's phase machinery. Everything else flows through the manifest.

## Prerequisite housekeeping

For any of the above to resolve correctly:

1. **Settle the skill name** — directory `infranodus-cli`, frontmatter `name: infranodus`, `/infranodus` in its own body, `/infranodus-cli` in the global CLAUDE.md trigger. Both description-level routing and Skill-tool invocation need one canonical name.
2. **Fix llm-wiki's stale references** — the `~/.claude/skills/infranodus/` path, and the `allowed-tools` list (contains `MCPorter`, which isn't a tool; omits `Edit`, `WebFetch`, `WebSearch`, `Skill`, all of which the body's workflows require).
3. **Sync the cli skill's tool catalog with the live MCP server** — the catalog lists `generate_difference_graph_from_text` / `generate_overlap_from_texts`; the server exposes `difference_between_texts` / `overlap_between_texts`.

## Work items

| # | Item | Where |
|---|---|---|
| 1 | Write `infranodus-folder-contract.md`; point both skills at it; have `install.sh` ship it into both | repo + both skills |
| 2 | Replace script-level references with Skill-tool invocation (Phase 6, Phase 9.4) | skill-llm-wiki |
| 3 | Add PDF/non-minable routing hint + curated-graph coexistence rule | infranodus-cli |
| 4 | Add the cross-routing clause to both descriptions | both SKILL.md frontmatter |
| 5 | Housekeeping: canonical name, stale path, `allowed-tools`, tool-catalog sync | both |
