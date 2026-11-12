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
  InfraNodus connector (claude.ai Settings → Connectors; the plugin's
  README has the steps) and sign in there. Then continue.
- **Saving graphs (repo/vault graphs, bulk uploads)** — always through the
  InfraNodus MCP server connected to this session: you perform the upload
  yourself with its `create_knowledge_graph` tool, following the contract
  in [references/repo-graph.md](references/repo-graph.md). This skill
  ships no programs and runs none: every read of the project goes through
  your own file tools, every write to InfraNodus through the connected
  server, signed in as the user. That connection is the only way this
  skill reaches InfraNodus.
- **If no InfraNodus tools are connected**, tell the user in one line to
  connect the InfraNodus connector and stop there; offer to keep what you
  wrote (a digest file) local meanwhile.
- **Provenance** — each saved scope records `endpoint`, `transport`,
  `account`, and `verified` (the date the graph was successfully read back)
  in the manifest. When a graph query fails, compare the manifest's
  `endpoint`/`account` against the session's own server before assuming the
  graph is missing: the same `graphName` means different graphs on different
  servers and accounts.
