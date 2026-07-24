# TODO: Repo-as-Graph support for InfraNodus skills

*Drafted 2026-07-21. Goal: make InfraNodus (skills + MCP server) as useful as graphify for giving LLMs a structural representation of a code repo, with graphs viewable in Cursor (VSCode extension) and Obsidian, and stored locally.*

Pipeline this enables, end to end (no LLM in construction):

```
deterministic repo scan  →  [[wikilink]] statements  →  create_knowledge_graph (MCP)
        │                                                      │
        └── infranodus/repo-ontology.md (Obsidian-ready)       ├── structural summary JSON (for the LLM)
                                                               ├── graph URL (for Cursor extension / browser)
                                                               └── full graph JSON → stored locally (goal 1)
```

---

## Goals

1. **Store generated graphs locally** (skill-level, no server changes needed) → A3
2. **Traverse the generated graph when providing a response** → A6
3. Represent a repo's structure as an InfraNodus graph an LLM can query → A1, A2
4. Make Claude reach for InfraNodus on codebase questions (trigger engineering) → A4, A5
5. View the repo graph in Cursor (VSCode extension) and Obsidian (infranodus-graph-view plugin) → E

---

## A. Changes to `infranodus-cli` skill

### A1. New reference: `references/repo-extraction.md`

> **STATUS UPDATE (2026-07-22): the code-structure tiers below are DEFERRED — they will be added later.** v1 of repo analysis instead mines the repo's natural-language layer: in-repo `.md` files, docstrings, and `WHY:`/`NOTE:` comments pulled from source; around-repo commit-message bodies, PR descriptions, and issue threads via `git log` / `gh` CLI. See `infranodus-app/docs/llms/infranodus-command.md` §4a for the v1 spec. The tiers below remain the spec for the later structure phase; the shared-wikilink rule (verbatim file paths) is the join point between the two.

Deterministic repo → statements conversion. **No LLM.** Ship a script in `scripts/repo2statements.py` (or `.js`); the skill instructs Claude only to *run* it.

Three fidelity tiers (script implements 1+2; tier 3 optional):

| Tier | Produces | Mechanism |
|---|---|---|
| 1. File tree | `[[src/auth]] contains [[src/auth/service.py]]` | filesystem walk (~20 lines) |
| 2. Imports | `[[src/auth/service.py]] imports [[src/db/client.py]]` | per-language regex on import/require/use/#include lines (~100 lines) |
| 3. Symbols + calls | `[[login]] calls [[validate_token]]` | if `graphify` CLI on PATH: `graphify extract . --code-only --no-cluster`, then convert `graphify-out/graph.json` edges → statements (tree-sitter AST, still deterministic) |

Format rules:
- One relation per line (newline = statement boundary for the API).
- Entities in `[[..]]` so file paths/symbols survive tokenization exactly.
- Relation word between the wikilinks (`contains`, `imports`, `calls`) — readable, and typed via the wikilinks-only processing mode (see A2) it does not pollute the node space.
- Optional relation typing: append `#contains` / `#imports` hashtags, or (richer, via direct REST) pass relation as per-statement `category` and git commit time as `timestamp`.

### A2. Upload step in SKILL.md

Feed statements to `create_knowledge_graph` with `graphName: repo-<name>`. Notes:
- The MCP tool POSTs to `/api/v1/graphAndStatements` with `addStats=true` — the response already contains the full structural analysis (see D).
- Default `maxNodes` is 150 (top by weighted degree): for large repos either raise `maxnodes` or create one graph per top-level directory and use multi-context/compare views.
- For a **pure structural graph** (only files/symbols as nodes), the request should set `doubleSquarebracketsProcessing: PROCESS_AS_HASHTAGS_IGNORE_THE_REST` ("wikilinks link to other wikilinks only") — currently NOT exposed by the MCP tool → see C1.

### A3. Local graph storage (goal 1) — unified with skill-llm-wiki's existing convention

**Do NOT introduce a new hidden `.infranodus/` folder.** skill-llm-wiki already defines a graph-artifact convention: a flat, visible `infranodus/` folder at project root holding `<scope>-ontology.md` wikilink files (curated, append-only), with analysis summaries in `output/`. Extend that convention instead of competing with it:

```
infranodus/
  manifest.json              # NEW: maps every local graph file → InfraNodus graphName,
                             #   view URL, source ("repo-scan" | "ontology-creator"),
                             #   policy ("generated" | "curated"), last-synced timestamp.
                             #   THE fast-path marker for both skills.
  repo-ontology.md           # NEW: deterministic repo scan output (wikilink statements) —
                             #   follows the existing <scope>-ontology.md naming
  concepts-ontology.md       # existing llm-wiki curated ontologies, unchanged
  repo-graph.json            # NEW: full graph fetched via create_knowledge_graph
                             #   (includeGraph + addNodesAndEdges): graphology nodes/edges
                             #   with community, betweenness, x/y/z layout
output/
  repo-knowledge-graph-analysis.md   # structural summary, existing llm-wiki naming
```

**Regeneration policy via YAML frontmatter** — this resolves the clash with llm-wiki's "NEVER regenerate ontologies" rule:

```yaml
---
generated: true          # machine-derived from source of truth (the code):
generator: repo2statements   # → overwrite freely on re-scan; do NOT hand-curate
---
```

Files without `generated: true` (or with `curated: true`) keep the append-only rule. Repo scans are derived artifacts like build output — stale edges after a refactor MUST be dropped, so they are always fully regenerated; curated ontologies accumulate human-reviewed knowledge, so they never are. Both skills must check the frontmatter before deciding how to update a file in `infranodus/`.

Git guidance: commit `manifest.json` + all `*-ontology.md`; consider gitignoring `*-graph.json` if large.

### A4. Frontmatter description — the trigger (most important single edit)

Extend the `description:` with codebase triggers, copying graphify's pattern:

> "…Use also for questions about a codebase, repo structure, architecture, or file relationships — especially when `infranodus/manifest.json` exists in the project root: treat the question as a graph retrieval first (`analyze_existing_graph_by_name`, `retrieve_from_knowledge_base`, `generate_content_gaps`) before reading files."

### A5. Fast path in SKILL.md body

First instruction: check for `infranodus/manifest.json`. If present and the request is a question (not a rebuild), skip extraction entirely — query the graph named in the manifest. Rebuild only on explicit request or when the scan output differs (re-run script, diff against stored `repo-ontology.md`).

### A6. Graph traversal when answering (goal 2 of the request list)

Add a `references/graph-traversal.md` teaching Claude to **traverse the stored graph while composing a response**, instead of (or before) reading source files — graphify's `query`/`path`/`explain` equivalent. Two modes:

**Local traversal** (free, offline — uses `infranodus/repo-graph.json` from A3):
1. Match question terms to node labels (exact + lemma/fuzzy match).
2. BFS outward from matched nodes over edges, collecting neighbors, their `community`, and betweenness; depth 2 by default, cap collected context by a token budget (~2000).
3. For "how are X and Y related" → shortest path between the two matched nodes; report the chain of relation words along the path.
4. For "what is X" → node + its community members + top-betweenness neighbors (the explain pattern).
5. For "what depends on X / what breaks if X changes" → reverse traversal over `imports`/`calls`-tagged statements.
6. Cite evidence: every edge maps back to a statement line in `repo-ontology.md` — quote the statement, not just the edge.

**Server-side retrieval** (when nuance or scale exceeds the local file):
- `retrieve_from_knowledge_base` / `generate_responses_from_graph` on `repo-<name>` for GraphRAG answers grounded in the statements.
- `analyze_existing_graph_by_name` for structure-level questions (clusters, gaps, influence).
- `generate_content_gaps` when the question is "what's missing / what should we work on".

Rule of thumb to encode in the skill: **structure questions → local traversal first** (deterministic, instant); **meaning/synthesis questions → server retrieval**. Always answer from the graph before falling back to reading files; fall back only when the graph lacks the node.

---

## B. Changes to `skill-llm-wiki` skill

The wiki architecture already fits — `infranodus/` ontologies + `output/` analyses (SKILL.md ~L177-242, Step 9.4). Changes are alignment + upgrades, not new structure:

- **B1. Adopt `manifest.json` + frontmatter policy (from A3).** Step 9.4's "append-only, never regenerate" rule becomes conditional: check frontmatter; `generated: true` files are overwritten by their generator, everything else stays append-only. One paragraph edit in the Knowledge Graphs section + Step 9.4.
- **B2. Upgrade from `generate_` to `create_knowledge_graph` for persistent graphs.** Today the skill only calls `generate_knowledge_graph` (ephemeral): no named server-side graph, so no GraphRAG retrieval, no shareable/Cursor-openable URL, no raw graph JSON. Change Step 9.4 and the ontology workflow (item 5, ~L231) to `create_knowledge_graph` with `graphName` from the manifest (e.g. `wiki-<project>-<scope>`), and save the returned graph JSON as `infranodus/<scope>-graph.json` + URL into the manifest. This gives the wiki the same goals 1+2 benefits as the repo: local storage, traversal, `retrieve_from_knowledge_base` over wiki content.
- **B3. Phase 6 (TOOLING) / Phase 9 (PROCESS):** add the repo scan as an ingest option — when raw sources include a code repo, run `repo2statements` (from infranodus-cli's scripts) and write `infranodus/repo-ontology.md` (with `generated: true` frontmatter). Wikilinks in it resolve as pages, so Obsidian graph view and the infranodus-graph-view plugin render the repo structure natively.
- **B4. Phase 10 (PLAN):** point gap analysis at the repo graph too — `generate_content_gaps` on the repo graph surfaces under-connected modules (candidate refactors / missing docs), feeding the todo list the phase already produces.
- **B5. Schema (Phase 4):** mention `infranodus/manifest.json` and the generated/curated distinction in the CLAUDE.md/AGENTS.md the skill writes, so future sessions query existing graphs instead of re-scanning, and never hand-edit generated files.

---

## C. Changes to `mcp-server-infranodus` (minimal)

1. **C1. Expose wikilink processing mode:** add optional `doubleSquarebracketsProcessing` enum (`PROCESS_AS_MENTIONS | PROCESS_AS_HASHTAGS | PROCESS_AS_HASHTAGS_IGNORE_THE_REST`) to `CreateGraphSchema` (`src/schemas/index.ts`) and pass through to `requestBody` in `createKnowledgeGraph.ts`. One parameter; unlocks pure structural graphs via MCP.
2. **C2. Trigger keywords:** add "codebase / repository structure / architecture analysis" to the `create_knowledge_graph` tool description and `instructions.ts`, so MCP-only clients (no skill installed) also route repo questions here.

---

## D. What comes back from one `create_knowledge_graph` call (already works, no changes)

- `statistics`: node/edge counts, modularity, `diversity_stats` (focused/dispersed state of the repo)
- `mainTopicalClusters` (module groupings), `mainConcepts`, `topInfluentialNodes` (betweenness ≈ god nodes), `conceptualGateways` (bridge files/symbols), `contentGaps` (modules that should connect but don't), `topRelations`, `knowledgeGraphByCluster` (DOT format per cluster)
- With `includeGraph`/`addNodesAndEdges`: full graphology nodes/edges + layout — this is what A3 stores locally
- Saved graph name + URL → open in Cursor via the VSCode extension or browser

## E. Viewing (no changes needed)

- **Cursor:** skill prints the graph URL from the response; extension opens the named graph.
- **Obsidian:** `statements.md` (or `wiki/repo-map.md`) in the vault + infranodus-graph-view plugin in "[[Wiki Links]] and Concepts" mode renders the repo graph locally.

---

## Suggested order of work

1. A4 + A5 (trigger + fast path — pure skill-text edits, biggest behavior change)
2. A1 script + A2 upload flow + A3 local storage
3. C1 + C2 (two small MCP server edits)
4. B (llm-wiki integration)
