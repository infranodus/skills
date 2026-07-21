# TODO: infranodus-app changes needed for repo-as-graph support

*Companion to [todo-graph-repo.md](todo-graph-repo.md). Drafted 2026-07-21 against the current `infranodus-app` code. Lists what must be programmed in the app to make the skill/MCP plan fully work — and, just as important, what already works and needs no code.*

## Already works — no app changes needed

Verified in code; the skill plan can rely on these today:

- **POST `/api/v1/graphAndStatements`** (`app.js:1276`, handler `routes/entries.js:568` `getGraphAndStatements`) accepts `name` (graphName), `text`, and — already — **`statements` arrays with per-statement `categories` and `timestamps`** (`entries.js:~615-640`). Relation-as-category typing and git-commit-time-as-timestamp need **no app work**; they only need the MCP server to expose a `statements` input (see other doc, section C).
- **Full graph return**: `includeGraph`, `compactGraph`, `includeStatements`, `extendedGraphSummary` query params all handled in `getGraphAndStatements` — local `repo-graph.json` storage is already feasible.
- **Saving under a name**: `doNotSave=false` + `name` creates a persistent named context — the Cursor-extension / browser URL handoff works today.
- **Wikilink tokenization**: `[[..]]` survives as exact nodes (backend tokenizer); file paths and symbols are safe.
- **Entity-graph shortcut**: for a **new** context, `modifyAnalyzedText: 'extractEntitiesOnly'` already sets `doubleSquarebracketsProcessing = 'PROCESS_AS_HASHTAGS_IGNORE_THE_REST'` (`lib/context.js:~997-1000`) — but see R1: it is coupled to TextRazor entity detection.

## Required changes (minimal set)

### R1. Decouple wikilink processing mode from entity detection

**Problem:** the only API path that sets `PROCESS_AS_HASHTAGS_IGNORE_THE_REST` (pure structural graph: only `[[wikilinks]]` become nodes, relation words ignored) is `modifyAnalyzedText: 'extractEntitiesOnly'` — which also flips `detectEntities = true` (`entries.js:~587-590`), sending the text through TextRazor. For repo statements the entities are *already* marked; TextRazor adds cost, latency, and noise.

**Change:** in `lib/context.js` `getContextForEntry()` (~L975-1000, the new-context branch), accept an explicit `textProcessingSettings` object (or at minimum `doubleSquarebracketsProcessing`) from `req.body` and merge it into `contextsObject.textProcessingSettings`, without touching the entity-detection flags. The settings-update handler at `lib/context.js:415` already reads exactly these body fields — reuse its field list (`doubleSquarebracketsProcessing`, `mentionsProcessing`, `lemmatizeHashtags`, `categoriesAsMentions`, `contextLanguage`, `contextStopwords`).

**Acceptance:** `POST /api/v1/graphAndStatements` with `{name, text, doubleSquarebracketsProcessing: "PROCESS_AS_HASHTAGS_IGNORE_THE_REST"}` produces a wikilinks-only graph with no TextRazor call.

### R2. Confirm/expose `maxnodes` on the POST endpoint

Default `maxNodes` is 150 (top by weighted degree) — a mid-size repo truncates. `req.query.maxnodes` is read on some handlers (`entries.js:288,405`); verify `getGraphAndStatements` honors it end-to-end (app → infrasonic query string, `lib/graph.js:28`), document the accepted range, and decide a sane repo default (e.g. 500). If plan-gated, return an explicit warning in the response when truncation happened rather than silently dropping nodes.

### R3. Retrieval-only fetch of a saved graph by name

The skill's fast path and local re-sync need "give me the current graph JSON for `repo-<name>` without submitting text." Verify whether `POST /api/v1/graphAndStatements` with `name` and empty `text` returns the existing context's graph (rather than erroring), or whether `/api/v1/graphsAndStatements` (`graphs.getSeveralGraphs`, `app.js:1288`) covers it. If neither does cleanly, add a documented retrieval path (name → full graph with stats, `includeGraph=true`). No new computation — the backend already rebuilds graphs on request.

## Optional enhancements (not needed for the minimum plan)

- **O1. `CODE`/`REPO` ContextType**: the backend `ContextType` enum already has PDF/CSV/MD/WIKILINKS/ONTOLOGY; adding a repo type lets the app badge repo graphs in `/:username` lists and `/find`, and pick better defaults (wikilinks-only processing, higher maxNodes) automatically.
- **O2. Node → source deep links**: repo statements can carry `file:line` (e.g. as statement text or category). If the graph view / VSCode extension surfaced a "open in editor" action on node click (`vscode://file/<path>:<line>`), the extension becomes a real code-navigation surface, not just a viewer. Requires plumbing one metadata field through `graphologyToJSON.js` node attributes.
- **O3. "Import repo" entry in the Imports menu**: a thin UI wrapper (like `TextFilesImport.jsx`'s md path, `views/react/components/Imports/`) that accepts a `repo-ontology.md` statements file and applies the wikilinks-only preset. Pure convenience; API path covers it.
- **O4. Directed-edge display mode**: structural relations are directional (`A imports B`); the graphology graph is undirected, direction lives only in the statement. A display-level arrow mode would need backend + renderer work — explicitly out of scope for the minimal plan; the statement text preserves direction for the LLM meanwhile.

## Cross-reference: division of labor

| Piece | Lives in | Status |
|---|---|---|
| Repo scan → statements | skill script (`repo2statements`) | to build (other doc, A1) |
| Statements + categories/timestamps API | infranodus-app | **already works** |
| Wikilinks-only mode without TextRazor | infranodus-app | **R1 — build** |
| maxnodes for large repos | infranodus-app | **R2 — verify/document** |
| Fetch saved graph by name | infranodus-app | **R3 — verify/add** |
| Expose statements/processing params over MCP | mcp-server-infranodus | other doc, C1 (extend: also add `statements`, `maxNodes` passthrough) |
| Local storage, traversal, triggers, Obsidian | skills only | other doc, A3-A6, B |
