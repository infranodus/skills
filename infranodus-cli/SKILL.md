---
name: infranodus
description: >
  Text network analysis, knowledge graphs, content gap detection, SEO/GEO optimization,
  structured memory, and text comparison via the InfraNodus MCP server.
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
        "requires": { "env": ["INFRANODUS_API_KEY"] },
        "primaryEnv": "INFRANODUS_API_KEY",
      },
  }
---

# InfraNodus

Text network analysis and knowledge graph tools via the InfraNodus MCP server.

## How this skill talks to InfraNodus

- **Queries and analysis** — use the native MCP tools in the session
  (`mcp__infranodus__<tool>`, or the InfraNodus connector's equivalents).
  The server's own instructions and tool schemas are the authoritative
  reference for every tool's parameters and workflow patterns — do not
  duplicate or second-guess them here.
- **Bulk uploads (repo/vault graphs)** — the bundled
  `scripts/upload_scopes.py` talks to the MCP server itself over HTTP.
  It finds its credential automatically: `INFRANODUS_API_KEY` env var, or
  the key from an already-configured local `infranodus` MCP server entry
  (`.mcp.json`, `~/.claude.json`) — so a locally-installed MCP server means
  no extra setup. Never route bulk uploads through the agent context chunk
  by chunk; the script handles chunking, pacing, 429 backoff, and 413
  bisection. Preflight: `upload_scopes.py --check-auth`.
- If the MCP server is not connected and the user wants text analysis,
  tell them to connect it (https://mcp.infranodus.com/ with an InfraNodus
  API key, or the claude.ai connector). If `--check-auth` finds no
  credential for an upload (a cloud OAuth connector holds its token
  remotely and cannot be reused), ask for a key once (infranodus.com →
  settings → API access) or offer to keep the extracted files local.

## Quick orientation (details live in the server's tool schemas)

- Structural overview of a text/URL/graph: `generate_knowledge_graph`,
  `generate_topical_clusters`; persist with `create_knowledge_graph`
  (uploads to the same `graphName` APPEND statements).
- What's missing / ideation: `generate_content_gaps` →
  `generate_research_questions` / `generate_research_ideas`;
  `develop_text_tool` for the combined pipeline.
- Retrieval: `retrieve_from_knowledge_base` (GraphRAG over a saved graph),
  `analyze_existing_graph_by_name` (structure of a saved graph),
  `list_graphs` / `search` / `fetch` for discovery.
- Comparison: `overlap_between_texts`, `difference_between_texts`,
  `merged_graph_from_texts` (each takes a `contexts` array).
- SEO/GEO: `generate_seo_report` (90s+ timeout) or the individual
  `analyze_google_search_results` / `analyze_related_search_queries` /
  `search_queries_vs_search_results` tools.
- Diversity stats in responses: `biased` → too concentrated, `focused` →
  somewhat concentrated, `diversified` → balanced, `dispersed` → scattered.

## Repo / Vault Graphs (invoked inside a project folder)

When asked to graph, analyze, or ask questions about a repo, project, or
Obsidian vault, follow [references/repo-graph.md](references/repo-graph.md)
— it is the single authoritative runbook. In short:

1. `infranodus/manifest.json` exists + the request is a question → query
   the existing graphs; do NOT re-extract.
2. Build: `python3 scripts/repo2statements.py .` (deterministic extraction)
   → `python3 scripts/upload_scopes.py .` (upload, run in background)
   → `upload_scopes.py . --register-project` (once) → write the report.
