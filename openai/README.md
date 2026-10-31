# InfraNodus plugin for ChatGPT and Codex

The OpenAI plugin directory uses its own package format, so the `infranodus`
plugin is built twice from the same skill:

| | Claude Code | ChatGPT / Codex |
|---|---|---|
| Manifest | `infranodus/.claude-plugin/plugin.json` | `openai/infranodus/plugin.json` |
| MCP server | in the manifest (`mcpServers`) | `openai/infranodus/mcp.json` (OAuth via DCR) |
| Skill | `infranodus/SKILL.md` + `references/` + `scripts/` | copied to `skills/infranodus/` at build time |
| Version | **source of truth** | copied from the Claude manifest at build time |

Only the files in `openai/infranodus/` are OpenAI-specific. Edit the skill
in `infranodus/` as usual; both packages pick the change up.

## Build

```bash
tests/build-openai.sh            # dist/infranodus-openai.zip, warns on placeholders
tests/build-openai.sh --strict   # fails on placeholders: use before submitting
```

The script checks the directory's length limits, test-case counts, icon
paths and symlinks. Each tagged release also attaches
`infranodus-openai.zip` (see `.github/workflows/release.yml`).

`mcp.json` does not pass the generic agent-plugins.org schema, because that
schema allows no extra keys on a server entry. The
`extensions["com.openai"].auth` block is the placement OpenAI's auth docs
prescribe (developers.openai.com/plugins/build/auth), so it stays.

## Before submitting

1. **Demo video.** Record a walkthrough of the test cases below and replace
   `review.demo_recording_url` in `openai/infranodus/plugin.json`.
2. **Demo account.** An InfraNodus account for reviewers with no MFA or email
   codes, enough credits for the test cases, and a saved graph named
   `review-sample-graph` (test case 5). Credentials go in the dashboard's
   Review details form, never in the package.
3. **Identity.** Verify the organization at platform.openai.com → Settings →
   Organization → General. `developerName` / `author.name` ("Nodus Labs") are
   replaced by the verified name anyway; change them if you publish under
   another name.
4. **Project.** Use a project with global data residency. EU-residency
   projects cannot submit plugins with an MCP server.
5. **MCP server.** Deploy `mcp-server-infranodus` branch
   `feat/openai-plugin-review`. The plugin connects to
   `https://mcp.infranodus.com/openai`, which serves the same tools as `/mcp`
   without the analytics the directory blocks: no `submit_workflow_feedback`,
   no mcpcat `get_more_tools` tool or `context` parameter, and
   `optimize_reasoning` takes a summary rather than the chat. Claude clients
   keep using `/` and `/mcp`, unchanged. After the dashboard shows the verification token, set
   `OPENAI_APPS_CHALLENGE=<token>` on the server and check
   `curl https://mcp.infranodus.com/.well-known/openai-apps-challenge`
   returns only the token.
6. **Privacy policy.** Check that https://infranodus.com/about/privacy-policy
   names the categories of personal data collected, the purposes, the
   categories of recipients, retention periods and user controls.
7. `tests/build-openai.sh --strict`, upload `dist/infranodus-openai.zip`
   under **With MCP**, connect `https://mcp.infranodus.com/openai` with OAuth
   (Dynamic Client Registration), run the tool scan, wait for the skill
   scan (up to 2 hours) and submit.

## Tool annotation justifications

The dashboard asks for a justification for each tool's `readOnlyHint`,
`destructiveHint` and `openWorldHint`. The values come from the server.

- **Read-only, open world** (`analyze_text`, `generate_knowledge_graph`,
  `generate_topical_clusters`, `generate_content_gaps`,
  `generate_contextual_hint`, `generate_research_questions`,
  `generate_research_ideas`, `generate_responses_from_graph`,
  `develop_text_tool`, `develop_latent_topics`, `develop_conceptual_bridges`,
  `optimize_text_structure`, `overlap_between_texts`,
  `difference_between_texts`, `merged_graph_from_texts`,
  `generate_seo_report`, `analyze_google_search_results`,
  `analyze_related_search_queries`, `search_queries_vs_search_results`,
  `analyze_youtube_results`): analyze the input without saving anything to
  the account (`doNotSave=true`). Open world because they can fetch a public
  URL or YouTube transcript the user provides, or query Google / YouTube
  search.
- **Read-only, closed world** (`analyze_existing_graph_by_name`,
  `retrieve_from_knowledge_base`, `list_graphs`, `search`, `fetch`,
  `memory_get_relations`, `get_project_learnings`, `optimize_reasoning`):
  read the user's own saved graphs or analyze the text passed in; no external
  fetches, no writes.
- **Writes, not destructive, open world** (`create_knowledge_graph`,
  `analyze_llm_results`): `create_knowledge_graph` saves a new graph (it can
  fetch a URL as its source); `analyze_llm_results` queries external AI models
  and can save the result as a graph. Neither overwrites or deletes.
- **Writes, not destructive, closed world** (`memory_add_relations`,
  `generate_ontology_graph`, `optimize_knowledge_base` when `saveAs` is given,
  `add_project_learnings`, `enable_project_learnings`): add statements or a
  new graph in the user's account; existing content is not removed.
- **Destructive, closed world** (`delete_graph`, `delete_statements`,
  `update_statements`): remove or overwrite statements in the user's own
  graphs, only when the user asks for it.

## Test cases

Five positive and three negative cases live in `plugin.json` under
`extensions["com.openai"].review.test_cases`. Cases 1–3 are self-contained
(the text is in the prompt); case 4 creates `review-demo-notes`; case 5 needs
`review-sample-graph` in the demo account.
