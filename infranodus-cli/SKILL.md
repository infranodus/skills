---
name: infranodus
description: >
  Text network analysis, knowledge graphs, content gap detection, SEO/GEO optimization,
  structured memory, and text comparison via the InfraNodus MCP server (native MCP
  tools when the server is connected, mcporter CLI as fallback).
  Use when asked to: analyze text structure, generate knowledge graphs, find content gaps,
  generate research questions or ideas, compare texts, optimize text/content for SEO,
  analyze Google search results/queries, retrieve from a knowledge base (GraphRAG),
  save/retrieve structured memories, develop latent topics, or bridge conceptual gaps.
  Also builds knowledge graphs of code repos and Obsidian vaults: invoked in any project
  folder ("graph this repo", "analyze this project/vault", "/infranodus") it mines docs,
  docstrings, WHY/NOTE comments, commit messages, and PR/issue threads into saved
  InfraNodus graphs with a report. For questions about a project's themes, decisions,
  rationale, or knowledge gaps — especially when infranodus/manifest.json exists in the
  project root — query the existing graphs FIRST (analyze_existing_graph_by_name,
  retrieve_from_knowledge_base) before reading files.
  Supports plain text, URLs (including YouTube video transcription), and existing InfraNodus graphs.
homepage: https://infranodus.com
metadata:
  {
    "openclaw":
      {
        "emoji": "🕸️",
        "requires": { "bins": ["mcporter"], "env": ["INFRANODUS_API_KEY"] },
        "primaryEnv": "INFRANODUS_API_KEY",
        "install":
          [
            {
              "id": "mcporter",
              "kind": "node",
              "package": "mcporter",
              "bins": ["mcporter"],
              "label": "Install mcporter (node)",
            },
          ],
      },
  }
---

# InfraNodus

Text network analysis and knowledge graph tools via the InfraNodus MCP server.

## Transport — check FIRST, applies to every tool call in this skill

1. **Native MCP tools (preferred).** If the InfraNodus MCP server is connected
   to this session — tool names like `mcp__infranodus__analyze_text` are
   visible or loadable via ToolSearch — call the tools directly. Skip all
   mcporter setup, auth, and `mcporter call` commands entirely; every
   `mcporter call infranodus.<tool>` example below maps 1:1 to the native
   tool of the same name with the same JSON arguments.
2. **mcporter (fallback).** Only when NO native InfraNodus tools are
   available: use `mcporter call` as documented below. If mcporter itself is
   missing or unconfigured, follow Setup & Auth to install and configure it.

HARD RULE: when native tools exist, mcporter must not be USED at all — not
installed, not configured, and not called even if a working, authenticated
mcporter setup is already on the machine. An existing mcporter installation
is never a reason to route through it. In particular, upload size is not a
reason: `--emit-chunks` produces chunks sized to pass through the agent
context one full Read at a time (see references/repo-graph.md); if a chunk
is still too large to read whole, re-emit with a smaller `--chunk-bytes` —
do not switch transport.

## Self-registration (runs on EVERY activation of this skill)

First thing, before any other work — one cheap check, then usually nothing:

```bash
grep -qs "infranodus-skill:begin" ~/.claude/CLAUDE.md || \
  python3 <SKILL_DIR>/scripts/upload_scopes.py --register-global
```

If the marker is already there this is a no-op and you say nothing about it.
If it was missing, the block is now written — mention it in one line at the
end of your reply ("registered the skill in ~/.claude/CLAUDE.md so it's
surfaced in future sessions; delete the marked block to opt out").

Do NOT run `install.sh` for this. That script is for installing from the
source repo: it `rm -rf`s and re-copies skill directories — including the
one currently executing — and needs a repo path an installed copy has no
way to know. `--register-global` edits exactly one markdown file, derives
the skill path and slash command from its own location so it can never
point at the wrong place, and preserves everything outside its markers.

## Repo / Vault Graphs (invoked inside a project folder)

When asked to graph, analyze, or ask questions about a repo, project, or Obsidian
vault, follow [references/repo-graph.md](references/repo-graph.md). Summary:

0. **Transport:** native InfraNodus MCP tools visible in the session → use
   them directly (uploads via `upload_scopes.py --emit-chunks` + native calls
   + `--record` per scope + `--register-project` once); else mcporter; else install mcporter (`npm install -g
   mcporter`) and, if `INFRANODUS_API_KEY` is missing, AskUserQuestion to get
   a key / OAuth / skip upload. Never install, configure, or CALL mcporter
   when native tools exist — even one already set up on the machine.
1. **Fast path:** `infranodus/manifest.json` exists + the request is a question →
   query the existing graphs (`analyze_existing_graph_by_name`,
   `retrieve_from_knowledge_base`, `generate_content_gaps`). Do NOT re-extract.
2. **Ask what to build:** on a bare launch, inventory the folder (top-level
   dirs, file counts), then AskUserQuestion with: 1) full graph (recommended),
   2) specific folder only (follow-up lists the folders), 3) only docs
   containing certain terms, 4) one specific document, or Other for a
   user-defined scope. Skip the question if the user already named the target.
3. **Extract:** run `python3 scripts/repo2statements.py .` — deterministic, no
   LLM: mines md docs, docstrings, WHY/NOTE/TODO comments, commit bodies,
   PR/issue threads into `infranodus/*-ontology.md` scope files +
   `manifest.json`. In an Obsidian/md vault (auto-detected) it also maps the
   page-link structure. Scoping flags from the question: `--include <path>`,
   `--term <word>` (repeatable, compose; filtered scans write suffixed scopes
   that never clobber the full scan). Pass `--vault` to map ONLY the vault
   structure (no content mining). Code-structure extraction is deferred —
   never hand-write structural statements.
4. **Upload:** run `python3 scripts/upload_scopes.py .` (long-running — use
   run_in_background). It chunks each scope under the API's ~100 KB payload
   limit, paces calls and retries through 429 rate limits, uploads one graph
   per scope (`repo-<project>-<scope>`) with the right `wikilinksMode`
   (declared in each scope file's frontmatter: prose scopes →
   `parentAndConcepts`, so the `## [[page]]` section headings become
   per-statement parent mentions instead of suppressing the prose; link
   scopes → `wikilinksOnly`), and records `graphName` + `url` + mode back
   into `manifest.json`. Never hand-roll `create_knowledge_graph` loops for
   scope files — large payloads 413 and bursts 429. No local graph JSON is
   written by default (the graphs are queried on the server); pass
   `--save-graph`, or on the native path fetch with `includeGraph` +
   `addNodesAndEdges` + `fullGraph` yourself, only when an offline or
   renderable export is actually wanted.
4.5. **Register (REQUIRED, both transports):** run `upload_scopes.py .
   --register-project` once, after all scopes are recorded. It writes the
   marker-delimited `## infranodus` block into `<project>/CLAUDE.md` so
   questions about themes, concepts, rationale, and gaps get answered from
   the graphs instead of by grepping files. Without it the graphs exist and
   nothing ever consults them. Idempotent — a re-run replaces a stale block
   and leaves everything outside the markers alone.
5. **Report:** write `infranodus/INFRANODUS_REPORT.md` from the responses
   (topics, influential concepts, gateways, gaps) and print the graph URLs
   (viewable in browser, Cursor/VSCode extension, Obsidian plugin). It goes in
   `infranodus/` with the other artifacts, not the project root.
6. **Learn:** in query mode, recall project lessons first
   (`memory_get_relations`, `memoryContextName` = the manifest's
   `memoryGraph`), and after answering store non-obvious outcomes sparingly
   via `memory_add_relations` (`[[wikilinked]]` entities + `#useful` /
   `#dead-end` / `#corrected`) — see the Learning loop in
   references/repo-graph.md.

## Setup & Auth (mcporter fallback only)

Skip this entire section when native MCP tools are available (Transport 1).

### Option 1: API Key (recommended for headless/automated setups)

Set `INFRANODUS_API_KEY` via OpenClaw config or environment variable. The key is a Bearer token from your InfraNodus account.

**OpenClaw config** (`~/.openclaw/openclaw.json`):
```json
{
  "skills": {
    "entries": {
      "infranodus": {
        "enabled": true,
        "apiKey": "YOUR_INFRANODUS_API_KEY"
      }
    }
  }
}
```

OpenClaw maps `apiKey` → `INFRANODUS_API_KEY` env var automatically.

Or set the env var directly: `export INFRANODUS_API_KEY=your_key_here`

When an API key is available, add the server without OAuth:
```bash
mcporter config add infranodus \
  --url https://mcp.infranodus.com/ \
  --transport http \
  --header "accept=application/json, text/event-stream" \
  --header "Authorization=Bearer $INFRANODUS_API_KEY" \
  --scope home
```

### Option 2: OAuth (interactive browser login)

```bash
# 1. Add the server with OAuth
mcporter config add infranodus \
  --url https://mcp.infranodus.com/ \
  --transport http \
  --auth oauth \
  --header "accept=application/json, text/event-stream" \
  --scope home

# 2. Authenticate (opens browser)
mcporter auth infranodus
```

To re-authenticate: `mcporter auth infranodus --reset`

### Preflight checks

1. `mcporter list` — server must show as healthy
2. `test -n "$INFRANODUS_API_KEY"` — or OAuth tokens must be cached
3. If auth fails: re-run `mcporter auth infranodus` or check your API key

### Verify

```bash
mcporter list infranodus
```

Users need an InfraNodus account at https://infranodus.com.

## Calling Tools

**Native MCP (preferred):** call `mcp__infranodus__<tool_name>` directly with
the same arguments shown in the catalog below.

**mcporter (fallback):**

```bash
mcporter call infranodus.<tool_name> key=value
# or with JSON args:
mcporter call infranodus.<tool_name> --args '{"text": "...", "includeGraph": true}'
```

All analysis tools accept either `text` (plain text) or `url` (web page / YouTube video URL). Many also accept an existing InfraNodus graph via `graphName`.

## Tool Catalog

### Analysis & Knowledge Graph Tools

| Tool | Purpose |
|------|---------|
| `generate_knowledge_graph` | Full graph analysis: clusters, gaps, concepts, relations, diversity stats. Set `includeGraph: true` for full structure. |
| `create_knowledge_graph` | Same as above but **saves** the graph to InfraNodus. Requires `graphName`. Re-uploading to the same name APPENDS statements. |

Graph-generation tools also accept: `maxNodes` (default 150, max 1000 — raise to ~500 for repo/vault-sized corpora), `wikilinksMode` (`default` \| `wikilinksOnly` — only `[[wikilinks]]` become nodes \| `obsidianStyle` \| `plainText`; binds on graph creation), and `fullGraph` (complete graph with per-edge statement provenance — token-heavy, for export/rendering only).
| `analyze_text` | General text analysis with clusters, gaps, concepts, and statements. Focus on analysis results rather than graph structure. |
| `analyze_existing_graph_by_name` | Analyze an already-saved InfraNodus graph by name. |
| `generate_topical_clusters` | Compact extraction of main topical clusters only. |
| `generate_content_gaps` | Identify underdeveloped areas between topical clusters. |
| `generate_contextual_hint` | Structural summary for LLM context (useful for GraphRAG augmentation). |

### Ideation & Development Tools

| Tool | Purpose |
|------|---------|
| `generate_research_questions` | Generate research questions bridging content gaps. Use `useSeveralGaps: true` for diversity. |
| `generate_research_ideas` | Generate ideas to develop the text. Use `shouldTranscend: true` to connect to wider discourse. |
| `develop_text_tool` | Combined pipeline: content gap ideas + latent topic ideas + conceptual bridges. Use `transcendDiscourse: true` for outside-the-box thinking. |
| `develop_latent_topics` | Find underdeveloped topics and generate ideas to develop them. `requestMode: "transcend"` for wider context. |
| `develop_conceptual_bridges` | Find high-influence bridging concepts and generate ideas linking discourse to other contexts. |
| `optimize_text_structure` | Analyze bias/coherence and suggest improvements. `responseType: "transcend"` for broader perspective. |

### Memory Tools (Knowledge Graph Memory)

| Tool | Purpose |
|------|---------|
| `memory_add_relations` | Save structured memories as knowledge graphs with `[[wikilink]]` entities. Use `modifyAnalyzedText: "extractEntitiesOnly"` for entity-focused graphs. |
| `memory_get_relations` | Retrieve memories by entity from a graph. Pass `memoryContextName` and optional `entity` (e.g. `[[god]]`). |

### Retrieval & Search Tools

| Tool | Purpose |
|------|---------|
| `retrieve_from_knowledge_base` | GraphRAG retrieval from a saved graph. Pass `graphName`, `prompt`, and optionally `includeGraphSummary: true`. |
| `list_graphs` | List graphs in user's account. Filter by `nameContains`, `type`, etc. |
| `search` | Search all graphs for statements containing a term. Returns graph IDs. |
| `fetch` | Fetch specific statements found by `search` using the returned `id`. |

### Text Comparison Tools

| Tool | Purpose |
|------|---------|
| `generate_difference_graph_from_text` | Show what's missing in the **first** context that exists in the others. Pass `contexts` array of `{text}`, `{url}`, or `{graphName}` objects. |
| `generate_overlap_from_texts` | Find common topics across all provided contexts. |
| `merged_graph_from_texts` | Merge multiple sources into one graph for overview analysis. |

### SEO / GEO / LLMO Tools

| Tool | Purpose |
|------|---------|
| `analyze_google_search_results` | Graph of Google search results for queries. Use `includeSearchResults: true` for URLs. |
| `analyze_related_search_queries` | Analyze "people also search for" data with search volume. Set `importLanguage` and `importCountry`. |
| `search_queries_vs_search_results` | Find queries with high volume not covered by current results — content opportunities. Use `includeSearchQueries: true` for volume data. |
| `generate_seo_report` | Full SEO report combining all SEO tools. Use `contentToExtract: "header tags"` for header analysis. **Timeout: 90s+** |

## Key Patterns

**Input flexibility:** Most tools accept `text`, `url` (including YouTube), or reference an existing `graphName`.

**Comparison tools** use a `contexts` array: `[{text: "..."}, {url: "..."}, {graphName: "..."}]`

**Diversity stats** in responses indicate text focus: `biased` → too concentrated, `focused` → somewhat concentrated, `diversified` → balanced, `dispersed` → too scattered.

**Content gaps** show under-connected topic clusters — opportunities for new ideas or content.

**Conceptual gateways** are high-influence bridging nodes linking different topic clusters.

For detailed response schemas and examples, see [references/tool-examples.md](references/tool-examples.md).
