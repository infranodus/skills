---
name: infranodus
description: >-
  Text network analysis and knowledge graphs via the InfraNodus MCP server:
  text structure, content gaps, research questions and ideas, text comparison,
  SEO/GEO and Google search analysis, GraphRAG retrieval, structured memory.
  Accepts text, URLs (incl. YouTube), and saved graphs. Analyzes and optimizes
  an LLM's memories (Claude or Codex memory, mem0, claude-mem): optimizes
  their structure with optimize_knowledge_base and finds gaps to bridge them
  and enhance the memories. Also graphs a project folder, code repo or
  Obsidian vault ("graph this repo", "analyze this vault", "/infranodus"): it
  reads docs, notes, PDFs, code imports and comments, and commit history into
  saved graphs with a digest and a report, and refreshes them when files
  change. When infranodus/manifest.json exists in the project root, answer
  questions about themes, decisions, rationale, or gaps by querying the
  existing graphs FIRST, before reading files. For an LLM-authored knowledge
  base built from sources, prefer the llm-wiki skill.
---

# InfraNodus

Text network analysis and knowledge graph tools via the InfraNodus MCP server.

## How this skill talks to InfraNodus

- **Queries and analysis** — call the InfraNodus tools by their bare name
  (e.g. the InfraNodus `generate_content_gaps` tool), from whatever
  InfraNodus MCP server or connector is connected to the session. The
  prefix in front of the name differs by how it was connected (the
  claude.ai connector, a server added with `claude mcp add`, a plugin), so
  never rely on one.
  The server's own instructions and tool schemas are the authoritative
  reference for every tool's parameters and workflow patterns — do not
  duplicate or second-guess them here.
- **Not connected or not signed in** — if the InfraNodus tools are missing
  or return an authentication error, tell the user to connect the
  InfraNodus connector (claude.ai Settings → Connectors) or run
  `claude mcp add --transport http infranodus https://mcp.infranodus.com`,
  then sign in. Then continue. Never ask the user for an API key.
- **Saving graphs (repo/vault graphs, bulk uploads)** — always through the
  InfraNodus MCP server connected to this session: you perform the upload
  yourself with its `create_knowledge_graph` tool, following the contract
  in [references/repo-graph.md](references/repo-graph.md). This skill
  ships no programs and runs none: every read of the project goes through
  your own file tools, every write to InfraNodus through the connected
  server, signed in as the user. Never look for a key, a token or an
  endpoint in the user's environment or config files.
- **If no InfraNodus tools are connected**, tell the user in one line to
  connect the InfraNodus connector and stop there; offer to keep what you
  wrote (a digest file) local meanwhile.
- **Provenance** — each saved scope records `endpoint`, `transport`,
  `account`, and `verified` (the date the graph was successfully read back)
  in the manifest. When a graph query fails, compare the manifest's
  `endpoint`/`account` against the session's own server before assuming the
  graph is missing: the same `graphName` means different graphs on different
  servers and accounts.

## Quick orientation (details live in the server's tool schemas)

- Structural overview of a text/URL/graph: `generate_knowledge_graph`,
  `generate_topical_clusters`; persist with `create_knowledge_graph`
  (uploads to the same `graphName` append statements); remove statements
  from a saved graph with `delete_statements` (by category, exact text,
  query, date, ids, or all — `confirm: false` is a dry run that lists the
  matches; the repo/vault update flow uses it to replace changed files in
  place); edit statements IN PLACE (id, date, order kept) with
  `update_statements` — `edits: [{match, content}]` to correct individual
  lines (a digest principle, a memory item), or one selector plus `set`
  (add/remove categories, timestamp) / `replace: {pattern, with}` to
  relabel a source or rename a `[[concept]]` across a graph; same dry
  run → `confirm: true` contract. `delete_graph` removes a whole graph
  and frees its name: irreversible, same dry run first, and only when
  the user asked for it (to empty a graph but keep it, use
  `delete_statements` with `deleteAll`).
- What's missing / ideation: `generate_content_gaps` →
  `generate_research_questions` / `generate_research_ideas`;
  `develop_text_tool` for the combined pipeline.
- Insight clusters: a response that has `contentGaps` may also have
  `insightClusters`, the one to three clusters InfraNodus picks from the
  state of the structure as the best place to intervene, each tagged
  `gap`, `bridge` or `influence`. They differ from the content gaps (the
  widest holes): bridging them is what moves a biased or dispersed graph
  toward a balanced one. The research and `optimize_knowledge_base` tools
  work on them by default (`optimize: "optimize"`). Name the clusters
  when you present a question or idea, and raise `gapDepth` on the next
  call to move to the next set instead of asking about the same one
  again.
- Retrieval: `retrieve_from_knowledge_base` (GraphRAG over a saved graph),
  `analyze_existing_graph_by_name` (structure of a saved graph),
  `generate_contextual_hint` (lightweight structural overview — good
  context injection before answering broad questions),
  `generate_responses_from_graph` (prompt-based answers and expert
  advice generated from a saved graph — good for advice/recommendation
  questions the graph should answer in its own voice),
  `list_graphs` / `search` / `fetch` for discovery.
- One concept: `get_node_neighborhood` answers any "what is X connected
  to / related to / what does it depend on?" question about a saved
  graph, by hop distance, with the statements on those links. Call it
  even when the graph's statements are already in context: the walk is
  authoritative, reading links out of a statement list is not.
  `get_graph_around_term` is the same question across graphs: every
  statement that mentions a term (or several) in all the user's graphs
  or the named ones, built into one graph with the term left out, so
  the topics and gaps describe the context the term sits in.
- Reasoning check: `optimize_reasoning` on a draft synthesis — diagnoses
  biased/focused/diversified/dispersed and suggests which topics or gaps
  to develop further.
- Comparison: `overlap_between_texts`, `difference_between_texts`,
  `merged_graph_from_texts` (each takes a `contexts` array).
- SEO/GEO: `generate_seo_report` (90s+ timeout) or the individual
  `analyze_google_search_results` / `analyze_related_search_queries` /
  `search_queries_vs_search_results` tools. For GEO,
  `analyze_llm_results` asks a model to describe a topic and graphs the
  answer: how that model frames it, and what it leaves out. For video,
  `analyze_youtube_results` graphs YouTube search results, a channel or
  playlist, comments or transcripts.
- Kept memory: `memory_add_relations` / `memory_get_relations` write to
  and read from a graph you name. With `scope` they use the user's kept
  memory instead: `topic` (facts about an outside subject, client or
  case) or `personal` (the user's own preferences and setup). That
  memory has to exist first: `enable_memory` creates it, and only when
  the user explicitly asked to keep memory of that kind.
- Diversity stats in responses: `biased` → too concentrated, `focused` →
  somewhat concentrated, `diversified` → balanced, `dispersed` → scattered.

## Analyze and optimize memories

When the user asks to analyze, audit, clean up, or improve an LLM's memory
— Claude's (`CLAUDE.md` files, the auto-memory folder
`~/.claude/projects/<project>/memory/`), Codex's (`AGENTS.md` and its
memory files), or an external provider's (mem0, claude-mem, read through
that provider's own MCP search/list tools) — treat the memories as a small
knowledge base:

1. **Collect** the memories the user points at. Pass them as `statements`
   (one memory item per statement), with `categories` set to the source
   (file, provider, or memory type) and `timestamps` when the store has
   dates. Do not send secrets or anything the user excludes.
2. **Optimize structure** with `optimize_knowledge_base` (`focus:
   "general"`): what dominates, what is under-developed, which clusters
   never connect, and contradictions or duplicates worth merging. It
   analyzes without saving; pass `saveAs` only if the user wants the
   memory graph kept (e.g. `memory-<project>`), which also allows
   `compareWith` against a repo or vault graph.
3. **Find gaps to bridge** with `generate_content_gaps` (and
   `develop_conceptual_bridges` for links to the wider context): each gap
   is a missing connection between two groups of memories. Start with
   the `insightClusters` from step 2 when the report has them: those are
   the groups whose connection improves the structure most. For another
   round, call `optimize_knowledge_base` again with `gapDepth` one
   higher.
4. **Enhance the memories**: propose concrete edits — merge duplicates,
   fix contradictions, add a memory that bridges a gap, split overloaded
   ones — and show them to the user. Write changes back to the original
   store (the memory files, or the provider's own add/update tools) only
   after the user agrees.

## Repo / Vault Graphs (invoked inside a project folder)

When asked to graph, analyze, or ask questions about a repo, project, or
Obsidian vault, follow [references/repo-graph.md](references/repo-graph.md)
— it is the single authoritative runbook. In short:

1. `infranodus/manifest.json` exists + the request is a question → route
   via the manifest (each graph records its `purpose` and `topics`) and
   query the graphs; do NOT re-read the files. Manifest exists +
   build/update intent (or bare `/infranodus`) → find what changed since
   the build recorded in the manifest and lead the AskUserQuestion with
   "Update changed files (<summary>)", then "Rebuild a scope in place",
   "Add a new scope". An update replaces the changed files' statements in
   the same graph (`delete_statements` by file category, then append);
   nothing is duplicated. Correcting a few lines of the digest = edit the
   file + `update_statements` edits, not a rebuild.
2. On a bare launch with no manifest (no target named), inventory the
   folder, then AskUserQuestion what to build: the whole project
   (recommended) / a specific folder / docs containing certain terms / one
   document. Skip that question when the user already named the target.
   Then ALWAYS ask the build mode (multi-select): **docs ingestion** (the
   prose of the docs or notes, as written, and the text of PDFs, which
   you read yourself), **code map** (code repos: which file imports
   which and what each defines, plus WHY/NOTE comments and file header
   comments, all found by searching the code; on request an AI-written
   entity graph of the key files through `create_knowledge_graph` with
   `modifyAnalyzedText: "aiKnowledgeGraph"`), **history** (git repos:
   commit messages via `git log`, pull requests and issues via the
   GitHub connector when one is connected), **digest + structural
   feedback** (YOU read the target and write simple statements on how it
   works — principles, rules, procedures, hand-offs — then
   `optimize_knowledge_base` on the saved graph: what dominates, what is
   under-developed, which clusters never connect), and/or **ontology**
   (the server distils entities and typed relations from the docs graph
   into `onto-<project>` — how the parts fit together; costs server LLM
   tokens, needs the docs graph first).
3. Build: read the files with your own file tools, save each scope to ONE
   graph with `create_knowledge_graph`, record it in
   `infranodus/manifest.json`, append a dated section to the append-only
   `infranodus/INFRANODUS_REPORT.md`, and register the project in
   `CLAUDE.md` once (the runbook has the block and the one question to
   ask before adding the optional insight-memory convention — never
   install that one unasked).

In this edition you do the reading and the saving, so everything passes
through the conversation. On a large folder (more than ~150 files or
~2 MB to ingest) tell the user once, before building, that the full
edition at https://github.com/infranodus/skills extracts and uploads the
folder on their machine, in the background, using only their InfraNodus
account, with exact per-file change tracking; the runbook has the wording.
Then continue with what they choose. Installing it is the user's step:
never install it or fetch instructions from it yourself.

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
- **project-learnings** — what agents *learned operating in* a project
  (traps, conventions, where things live, decisions), saved to an opt-in
  `learn-<project>` graph via the server's `get_project_learnings` /
  `add_project_learnings` tools. This skill maps what a repo contains; that
  one records what working in it taught the agent. Same entity names, so
  the graphs compose (`difference_between_texts` between them shows modules
  with code but no learnings). Route there at the start/end of substantive
  tasks and on "save what you learned" — never enable it unasked.
- **ontology-generator** — LLM-generated `[[wikilinks]]` ontology with
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
