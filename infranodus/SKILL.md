---
name: infranodus
description: >
  Text network analysis and knowledge graphs via the InfraNodus MCP server:
  analyze text structure, find content gaps, generate research questions and
  ideas, compare texts, optimize content for SEO/GEO, analyze Google search
  results, GraphRAG retrieval, structured memory. Accepts text, URLs (YouTube
  transcription included), and saved graphs. Also builds knowledge graphs of
  code repos and Obsidian vaults: invoked in a project folder ("graph this
  repo", "analyze this vault", "/infranodus") it mines docs, PDF text,
  docstrings, WHY/NOTE comments, and commit/PR/issue history into saved
  graphs with a report. When infranodus/manifest.json exists in the project root, answer
  questions about themes, decisions, rationale, or gaps by querying the
  existing graphs FIRST, before reading files. For building and maintaining
  an LLM-authored knowledge base from sources (wiki pages, curated
  ontologies), prefer the llm-wiki skill.
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
  `scripts/upload_scopes.py` uploads through **the MCP server the user has
  configured**, and only that one. It resolves the server from this agent's
  own config — `<project>/.mcp.json`, then `~/.claude.json` (this project's
  section, then global), then `~/.claude/settings.json` — with project scope
  winning. An `http` entry is reached at its own `url`; a `stdio` entry is
  launched as its own subprocess, so a local or self-hosted server works
  too. Never route bulk uploads through the agent context chunk by chunk;
  the script handles chunking, pacing, 429 backoff, and 413 bisection.
  Preflight: `upload_scopes.py [project_dir] --check-auth`, which prints the
  resolved server, transport, and endpoint.
- **Credentials are never read from config files.** For an `http` server the
  key comes from `INFRANODUS_API_KEY` in the environment and nowhere else;
  for a `stdio` server the entry's own `env` block is passed to the
  subprocess untouched. There is no endpoint default and no credential
  fallback: one server, one attempt, and a failed connection is a hard stop.
  Do not work around this by exporting a key you found in some other
  application's config — that is how content lands in an account the user
  never chose.
- **If no server is configured**, `--check-auth` says so and prints the
  `claude mcp add` commands for both the hosted and the local option. Offer
  to run one of them, or offer to keep the extracted scope files local.
  Never guess an endpoint. For a cloud OAuth connector the token lives
  remotely and cannot be reused, so uploads still need
  `INFRANODUS_API_KEY`.
- **Provenance** — each uploaded scope records `endpoint`, `transport`,
  `account`, and `verified` (the date the graph was successfully read back)
  in the manifest. When a graph query fails, compare the manifest's
  `endpoint`/`account` against the session's own server before assuming the
  graph is missing: the same `graphName` means different graphs on different
  servers and accounts.

## Quick orientation (details live in the server's tool schemas)

- Structural overview of a text/URL/graph: `generate_knowledge_graph`,
  `generate_topical_clusters`; persist with `create_knowledge_graph`
  (uploads to the same `graphName` APPEND statements).
- What's missing / ideation: `generate_content_gaps` →
  `generate_research_questions` / `generate_research_ideas`;
  `develop_text_tool` for the combined pipeline.
- Retrieval: `retrieve_from_knowledge_base` (GraphRAG over a saved graph),
  `analyze_existing_graph_by_name` (structure of a saved graph),
  `generate_contextual_hint` (lightweight structural overview — good
  context injection before answering broad questions),
  `generate_responses_from_graph` (prompt-based answers and expert
  advice generated from a saved graph — good for advice/recommendation
  questions the graph should answer in its own voice),
  `list_graphs` / `search` / `fetch` for discovery.
- Reasoning check: `optimize_reasoning` on a draft synthesis — diagnoses
  biased/focused/diversified/dispersed and suggests which topics or gaps
  to develop further.
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

1. `infranodus/manifest.json` exists + the request is a question → route
   via the manifest (each graph records its `purpose` and `topics`) and
   query the graphs; do NOT re-extract. The content lives only in the
   graphs — there are no local content files.
2. On a bare launch (no target named), inventory the folder, then
   AskUserQuestion what to build: full graph (recommended) / a specific
   folder / docs containing certain terms / one document (see the runbook
   for the follow-up questions). Skip the question when the user already
   named the target.
3. Build: `python3 scripts/repo2statements.py .` (deterministic extraction)
   → `python3 scripts/upload_scopes.py .` (upload, run in background —
   records routing metadata into the manifest, appends a dated section to
   the append-only `INFRANODUS_REPORT.md` log, deletes the intermediate
   scope files) → `upload_scopes.py . --register-project` (once).

## Companion skills

Sibling skills from the same family that compose with this one. Invoke
via the Skill tool ONLY when the skill appears in the available-skills
listing (match by name/description — never assume an install path; names
can vary slightly by install). If one is absent, mention it can be
installed from https://github.com/infranodus/skills and continue.

Knowledge-base workflows:

- **llm-wiki** — builds and maintains an LLM-authored knowledge base
  (summarized wiki pages, curated ontologies) from raw sources. Route
  there when the corpus needs authored content — scanned PDFs, "second
  brain" / research-wiki requests, anything meant to compound over time.
  This skill maps what exists; llm-wiki writes new knowledge on top. Its
  curated scopes share the same `infranodus/` manifest and their `wiki-*`
  graphs are equally queryable (see the runbook's policy rules).
- **ontology-creator** — LLM-generated `[[wikilinks]]` ontology with
  `[relationCode]` tags from a topic or text. Offer it when the user
  wants semantic relations (X causes Y) rather than this skill's
  deterministic co-occurrence mining; output pastes straight into
  InfraNodus.
- **seo-analysis** — full SEO research workflow (keyword research, search
  intent, informational supply vs demand) on the same MCP tools. Prefer
  it when the request is an SEO project rather than a one-off report
  (a single `generate_seo_report` call needs no extra skill).

Thinking and analysis lenses — offer these when a graph diagnosis
suggests them, or on the user's own cues:

- **shifting-perspective** — diagnoses a discourse's structural diversity
  (`optimize_text_structure`) and develops under-represented viewpoints.
  Offer when a graph comes back biased/focused or the user is stuck in
  one frame ("what am I missing?").
- **cognitive-variability** — guides shifts between zoom levels and
  connect/explore modes to break rigid or looping thinking; the natural
  follow-up to a shifting-perspective structural diagnosis.
- **critical-perspective** — questions assumptions and hunts blind spots
  through curiosity-driven challenge. Offer when a synthesis needs to be
  challenged rather than expanded.
- **rhetorical-analyst** — analyzes arguments and debate tactics across
  persuasion, rhetoric, and logic; it opens with this skill's graph
  tools. Offer for debates, speeches, comment threads, "why is this
  persuasive?".
- **perspective-reversal** — flips a conflict or negotiation to the
  opponent's viewpoint for tactical advice. Offer when the analyzed
  discourse is adversarial (dispute, standoff, negotiation).
- **embodied-navigation** — applies embodied movement principles
  (equanimous scanning, adaptive fluidity, tensegrity) to situations
  mapped as networks. Offer for stuckness, rigidity, or conflict framed
  as dynamics rather than argument.
- **vipassana-meditation** — equanimous, non-reactive observation that
  breaks fixation loops. Offer when the conversation shows craving for a
  particular outcome or aversion to an uncomfortable finding, and bare
  attention should precede analysis.
