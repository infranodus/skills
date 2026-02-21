---
name: infranodus
description: >
  Text network analysis, knowledge graphs, content gap detection, SEO/GEO optimization,
  structured memory, and text comparison via the InfraNodus MCP server (mcporter).
  Use when asked to: analyze text structure, generate knowledge graphs, find content gaps,
  generate research questions or ideas, compare texts, optimize text/content for SEO,
  analyze Google search results/queries, retrieve from a knowledge base (GraphRAG),
  save/retrieve structured memories, develop latent topics, or bridge conceptual gaps.
  Supports plain text, URLs (including YouTube video transcription), and existing InfraNodus graphs.
---

# InfraNodus

Text network analysis and knowledge graph tools via the InfraNodus MCP server.

## Setup & Auth

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
| `create_knowledge_graph` | Same as above but **saves** the graph to InfraNodus. Requires `graphName`. |
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
