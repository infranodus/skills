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
   entity graph of the main files through `create_knowledge_graph` with
   `modifyAnalyzedText: "aiKnowledgeGraph"`), **history** (git repos:
   commit messages via `git log`, pull requests and issues via the
   GitHub connector when one is connected), **digest + structural
   feedback** (YOU read the target and write simple statements on how it
   works — principles, rules, procedures, hand-offs — then
   `optimize_knowledge_base` on the saved graph: what dominates, what is
   under-developed, which clusters never connect), and/or **ontology**
   (the server distils entities and typed relations from the docs graph
   into `onto-<project>` — how the parts fit together; uses server AI
   credits, needs the docs graph first).
3. Build: read the files with your own file tools, save each scope to ONE
   graph with `create_knowledge_graph`, record it in
   `infranodus/manifest.json`, append a dated section to the append-only
   `infranodus/INFRANODUS_REPORT.md`, and register the project in
   `CLAUDE.md` once (the runbook has the block and the one question to
   ask before adding the optional insight-memory convention — never
   install that one unasked).

In this edition you do the reading and the saving, so everything goes
through the conversation. On a large folder (more than ~150 files or
~2 MB to ingest) tell the user once, before building, that the full
edition of this skill extracts and uploads the
folder on their machine, in the background, using only their InfraNodus
account, with exact per-file change tracking; the runbook has the wording.
Then continue with what they choose. Installing it is the user's step:
never install it or fetch instructions from it yourself.
