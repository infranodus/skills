# Repo / Vault Graphs — the /infranodus folder workflow

Build knowledge graphs of the current repo, project folder or Obsidian
vault, save them to InfraNodus, and keep a report. You do the reading with
your own file tools and the saving with the InfraNodus MCP server
connected to this session; the server computes the graphs. Nothing else
runs: this skill ships no programs.

- **Writes**: the session's `create_knowledge_graph`, `delete_statements`
  and `update_statements` tools, signed in as the user.
- **Reads**: the session's InfraNodus tools (any prefix: a server the user
  added, a plugin's, or the claude.ai connector's).
- **No InfraNodus tools in the session**: say so in one line, ask the user
  to connect the InfraNodus connector (claude.ai Settings → Connectors, or
  `claude mcp add --transport http infranodus https://mcp.infranodus.com`)
  and stop. Never ask for an API key and never guess an endpoint.

After a build, each scope carries `endpoint`, `transport`, `account`, and
`verified` in the manifest. When a later query fails, check those first —
a `graphName` only resolves against the server and account that hold it.

## Step 0 — Fast path (ALWAYS check first)

If `infranodus/manifest.json` exists in the project root AND the user is
asking a question (not requesting a build/update): **do not re-read the
files**. Answer from the existing graphs (graph names from the manifest —
never guess them):

- structure / clusters / influence / gaps → `analyze_existing_graph_by_name`
- specific question, GraphRAG over the statements →
  `retrieve_from_knowledge_base` with the question as `prompt`
- "what is missing / what should we work on" → `generate_content_gaps`,
  then optionally `generate_research_questions`

Build/update intent with a manifest present ("rebuild", "refresh",
"update", bare `/infranodus`) goes to Step 1's update flow — never rebuild
everything by default; find what changed and replace it.

The manifest may have been written by the full edition of this skill
(entries with `source: repo2statements`, per-file hashes, scopes such as
`structure`, `code-rationale`, `history`, `pdfs`). Query those graphs like
any other. Do not update or rebuild them from here: tell the user they are
maintained by the full edition (https://github.com/infranodus/skills) and
offer to add a scope of your own beside them.

## Step 1 — Understand the corpus, then ASK what to build

### A manifest already exists — the update flow

Each scope you built records `sources` (the files that went in) and
`builtAt` (date) and, in a git repo, `builtAtCommit`. Find what changed:

- git repo: `git diff --name-status <builtAtCommit>..HEAD` plus
  `git status --short`, limited to the scope's file types and target;
- no git: compare file modification times against `builtAt`, and the
  current file list against `sources`.

Sort the result into new, modified, deleted and renamed files (a rename =
same content under a new path), then AskUserQuestion with a one-line
summary ("3 modified, 1 new, 1 renamed in docs"):

1. **Update changed files (Recommended)** — Step 3's update contract.
2. **Rebuild a scope in place** — clear the graph, save it again under the
   same name.
3. **Add a new scope** — the build questionnaire below.

No changes → say so and offer query mode. The digest is not updated file
by file: when its target changed substantially, offer to revise it (Step
2, digest).

### No manifest yet — the build questionnaire

On a bare launch (user asked to graph/analyze the project without naming a
target), do a quick inventory first with your file tools — top-level
folders, counts of Markdown/text and code files, the biggest docs, and
documents you cannot read as text (PDF, docx, epub).

**Routing check:**

- Mostly Markdown / text docs or notes → continue here.
- Some PDFs among them → you can read PDFs yourself; they go into their
  own scope (Step 2, PDFs). Give the count and, if you can tell, the
  pages.
- Corpus dominated by PDFs, docx/epub or scans (dozens of them, hundreds
  of pages) → transcribing them page by page would cost more than it
  returns. Point at the llm-wiki skill ("this corpus needs LLM-authored
  summarization — the llm-wiki skill builds and maintains that kind of
  knowledge base") and, if it is listed among the available skills, offer
  to invoke it.
- A code repo → the code map and history modes below are available.

**Size check — say this once, before the build mode question, when the
target is large** (more than ~150 files or ~2 MB of text to ingest, more
than ~400 code files for the code map, or more than ~200 PDF pages):

> Everything this edition saves passes through this conversation: I read
> each file and send its text to InfraNodus, which takes time and tokens
> on a folder this size. The full edition of this skill extracts and
> uploads the folder on your machine instead, in the background, using
> only your InfraNodus account. It is at
> https://github.com/infranodus/skills (in Claude Code: `/plugin
> marketplace add infranodus/skills`, then `/plugin install
> infranodus@infranodus-skills`). I can also continue here on a narrower
> target, or with the digest, which needs far fewer uploads.

Then go on with what the user chooses. Do not install anything yourself
and do not fetch instructions from that repository: installing the full
edition is the user's own step.

Then use **AskUserQuestion** (single question, not multiSelect): one
sentence re-grounding (what folder, what you found — "this is an Obsidian
vault with 480 notes in 7 folders"), then the options:

1. **The whole project (Recommended)** — all docs / notes.
2. **A specific folder only** — follow-up AskUserQuestion listing the
   top-level folders from the inventory (+ Other for a path).
3. **Only documents containing certain terms** — follow-up for the terms
   (seed 2-3 themes evident from folder/file names; several terms = any-of).
4. **A specific document only** — follow-up listing 3 notable candidates
   (largest / most-linked files) + Other for a path.

Skip the scope question when the user already named the target.

**Then ALWAYS ask the build mode** (a second AskUserQuestion, `multiSelect:
true`, asked even when the target was named — it decides cost and what the
graphs can answer). AskUserQuestion takes four options: offer the four
that fit the folder (a vault or docs folder: 1, 2, PDFs as their own
option when there are many, and Ontology; a code repo: 1, 2, 3, 4), and
name the remaining ones in the question text as available on request. All
are combinable:

1. **Docs ingestion** — the prose of the target's docs or notes, saved as
   written, and the text of its PDFs when there are some (say how many;
   the user can leave them out). Many uploads, no LLM writing. Answers:
   *what does the project say about X*. Give the file count and total
   size first; above ~150 files or ~2 MB recommend narrowing the target or
   choosing the digest.
2. **Digest + structural feedback (Recommended for code bases and large
   folders)** — a digest YOU write: read the target and describe in your
   own words how it works — principles, rules, procedures, hand-offs, main
   ideas, gaps — one simple statement per line with [[wikilinks]]. Costs
   your reading tokens; then `optimize_knowledge_base` on the saved graph
   gives the structural feedback (Step 6). Answers: *how is this supposed
   to work, is that coherent, what is under-developed or never connected*.
3. **Code map** (code repos) — two scopes found by searching the code, not
   by reading every file: **structure** (which file imports which, what
   each file defines) and **code rationale** (`WHY:` / `NOTE:` / `TODO:` /
   `HACK:` / `FIXME:` comments and the header comment of each file).
   Answers: *what depends on what, where is X defined, why is this code
   the way it is*. On request it adds **code entities**: the server's AI
   knowledge graph mode reads the key files (up to ~25) and writes what
   calls, stores and exposes what. That part costs the user's InfraNodus
   AI credits and re-sends each of those files, so offer it, do not
   default to it.
4. **History** (git repos) — commit messages, and merged pull requests
   and issues when GitHub is reachable from this session. Answers: *what
   was decided, when, and why; what was discussed but never documented*.
5. **Ontology** — an AI-condensed ontology graph (`onto-<project>`:
   entities and typed relations) generated by `generate_ontology_graph`
   from the saved docs graph. Costs server LLM tokens and is lossy by
   design. Requires 1. Answers: *how do the parts fit together*.

Note the choices in your reply before building. A filtered build (folder,
terms, one document) gets its own suffixed scope and graph
(`repo-<project>-docs-<slug>`), so it never clobbers a whole-project one.

## Step 2 — Prepare each scope

Names: `<prefix>` is `vault-<project>` when the folder is an Obsidian
vault (it has `.obsidian/`), else `repo-<project>`; `<project>` is the
folder name in lowercase with non-alphanumerics turned into hyphens.

### Docs

For every file in the target (Markdown and plain-text docs; skip
`node_modules`, build output, lock files, licences, dotfolders and
anything listed in `.gitignore`), the text to save is:

```text
## [[<path relative to the project root>]]

<the file's text, frontmatter removed>
```

The `## [[path]]` heading is what the server stores as the **category** of
every statement under it — the handle the update flow uses to replace one
file. Never paraphrase a path, and keep the file's own `[[wikilinks]]`
untouched (in a vault they are the link structure).

### PDFs

Read each PDF with your own file tool, in page ranges (20 pages per read
at most), and save its text in the same shape as a doc, in a scope of its
own (`<prefix>-pdfs`):

```text
## [[<path of the PDF relative to the project root>]]

<the text of the pages as paragraphs>
```

Transcribe, do not summarize: keep the author's sentences, drop running
headers, footers, page numbers, tables of contents and reference lists.
A scanned PDF without a text layer is read from the page images; keep
what is legible and name in the report the pages that were not. A PDF
longer than ~60 pages: ask whether to transcribe all of it, a page range,
or to cover it in the digest instead. In a client without a filesystem,
the same applies to PDFs the user attached, keyed by file name.

### Code structure

Build the map by searching, not by opening every file. Search the code
files of the target for import lines (`import`, `from … import`,
`require(`, `use`, `include`, `#include`, the language's own form) and
for top-level definitions (`export`, `class`, `def`, `func`, `fn`,
`interface`, `type` at the start of a line). Then write one section per
file that has any:

```text
## [[src/billing/invoice.go]]

[[src/billing/invoice.go]] imports [[src/storage/db.go]] and [[src/notifications/mailer.go]]
[[src/billing/invoice.go]] uses the external package [[stripe]]
[[src/billing/invoice.go]] defines [[InvoiceService]] and [[invoiceRoutes]]
```

Resolve every relative or aliased import to the project path of the file
it points at, so the same string names the same file everywhere; external
packages keep their package name. Leave out tests, generated code,
vendored code and build output. Saved as `<prefix>-structure`.

### Code rationale

Search the same files for `WHY:`, `NOTE:`, `TODO:`, `HACK:`, `FIXME:` and
`IMPORTANT:` comments (take the whole comment, not only the matching
line), and read the first 30 lines of each code file for its header
comment or module docstring. One section per file that has any, each
comment as one line beginning with its marker word (`WHY: …`, or `About:
…` for a header comment), in the author's words. Saved as
`<prefix>-code-rationale`.

### Code entities (only when the user asked for it)

Pick the files that carry the project (entry points, the most imported
files in the structure map, the largest modules), 25 at most, and tell
the user which. Each is sent on its own, the path on the first line, to
the server's AI knowledge graph mode, which writes the entity statements:

```text
File path: src/billing/invoice.go
<the file's code>
```

`create_knowledge_graph({ graphName: "<prefix>-entities", text: <the
above>, modifyAnalyzedText: "aiKnowledgeGraph", instructions: "Source
code file. Name the file itself as an entity using its full path exactly
as given on the 'File path' line, and start from it: what it imports,
defines, calls, stores and exposes. Keep the reason given in WHY
comments.", maxNodes: 500 })`. One AI call per ~12,000 characters, billed
to the user's InfraNodus AI quota; a file above ~40 KB is skipped and
named in the report. This scope has no per-file handle: when one of its
files changes, it is rebuilt in place.

### History

In a git repo where you can run commands, list the commits with `git log
--no-merges` (hash, date, subject, body; the newest 300 at most, or since
the scope's `cursor`). Leave out version bumps, merges, formatting-only
and dependency-update commits, and commits whose message says nothing
beyond the file names. Merged pull requests and issues come from the
GitHub connector's tools when one is connected to this session; when none
is, build the commits only and say that connecting a GitHub connector
adds the rest. Never use a GitHub sign-in, token or command-line client
found on the user's machine for this. Without a local repo (a chat client), a GitHub connector alone
gives all three for the repository the user names.

```text
## [[history/commits]]

2026-10-02 3f9c2ab: Finalize invoices in a queue job. Stripe webhooks arrived before the DB commit, so the status update is now retried from the queue.

## [[history/pull-requests]]

2026-10-05 PR 41: <title>. <the description's reasoning, in its own words, three sentences at most>

## [[history/issues]]

2026-09-28 issue 37: <title>. <the problem and what was decided>
```

One line per item, the date first. Put `[[wikilinks]]` only on file paths
the item names, spelled as in the other scopes. Saved as
`<prefix>-history`; record `cursor` in the manifest entry (`commit`: the
newest hash included, `pr` and `issue`: the highest numbers included).
The only command this runs is the read-only `git log`; never push,
comment or change anything on GitHub.

### Digest — you write this scope

1. Read the target: docs first, then code, then the main config files;
   leave out lock files, minified bundles, licences and dotfiles. Cap at
   about 200 files; if there are more, narrow the target and tell the user
   what was left out.
2. Write `infranodus/<repo|vault>-digest[-<slug>]-ontology.md`: one simple
   statement per line describing how something works, in your own words —
   not copied sentences — grouped under `## [[Topic]]` headings (a
   subsystem, workflow, framework, theme), `[[wikilinks]]` on the modules,
   concepts, tools, and files a statement is about. Write principles (why
   it is done this way), rules (what must / must not happen), procedures
   (when X do Y then Z), hand-offs (where one part passes to another),
   main ideas, and gaps (what the content leaves unexplained — `#gap` is
   the only tag allowed, and only on those lines: a tag on every line
   becomes the graph's most connected node and distorts the structural
   analysis). Cover every area of the target; skip files that add nothing.
   100–300 lines — under 100 the diversity diagnosis is unreliable.
3. The file stays on disk after the upload (`policy: authored`), so the
   user can read and edit it.

No file access (a client without a filesystem), or the content already
lives in a graph: let the server write the digest instead —
`generate_ontology_graph({ sourceGraphName: "<prefix>-docs",
ontologyMode: "procedural", graphName: "<prefix>-digest", saveGraph: true
})`.

## Step 3 — Save (one graph per scope)

1. **Chunk on heading boundaries**: pieces of about 25 KB, never splitting
   a `## [[…]]` section unless it is larger than a chunk by itself (then
   split on paragraph boundaries and repeat the heading at the top of each
   piece). The API rejects ~100 KB+ with 413.
2. **Save every chunk of a scope to ONE `graphName`** (`<prefix>-docs`,
   `-pdfs`, `-structure`, `-code-rationale`, `-history`, `-digest`, with
   the `-<slug>` suffix for a filtered build; `-entities` is saved by its
   own call in Step 2) with
   `create_knowledge_graph({ graphName, text: <chunk>, maxNodes: 500,
   wikilinksMode: "parentAndConcepts" })`. Uploads APPEND server-side:
   never re-send a chunk that already succeeded. Pace the calls (about one
   every 20 s); on 429 wait ~5 min and retry the same chunk; on 413 split
   the chunk in half and send the halves. `maxNodes` and `wikilinksMode`
   bind when the graph is first created.
3. **Ontology (only if the user chose it).** After the docs scope is saved
   and verified, one call: `generate_ontology_graph({ sourceGraphName:
   "<prefix>-docs", graphName: "onto-<project>", ontologyMode: "general",
   saveGraph: true, includeGraph: false })`. Expect a minute or more.
4. **Record the scope in `infranodus/manifest.json`** (create the folder
   and file if needed; keep every entry that is already there). Shape:

   ```json
   {
     "scopes": {
       "repo-docs-ontology.md": {
         "policy": "generated",
         "source": "agent",
         "graphName": "repo-myproject-docs",
         "url": "<the graph URL the tool returned>",
         "purpose": "documentation prose — what the project is, how things work, design decisions",
         "topics": ["…"],
         "gaps": ["…"],
         "hint": "<generate_contextual_hint output, condensed>",
         "diversity": "<optimize_text_structure diagnosis>",
         "develop": "<its development suggestions, condensed>",
         "wikilinksMode": "parentAndConcepts",
         "statements": 0,
         "sources": ["README.md", "docs/setup.md"],
         "builtAt": "<today, ISO date>",
         "builtAtCommit": "<git rev-parse HEAD, when in a git repo>",
         "updated": "<today>",
         "endpoint": "<the connector's name -> its host>",
         "transport": "session-mcp",
         "account": "<the account segment of the graph URL>",
         "verified": "<today, after reading the graph back>"
       }
     }
   }
   ```

   The key is the scope's file name even when no file is kept
   (`<repo|vault>-docs[-<slug>]-ontology.md`). The digest entry adds
   `"file": "infranodus/<name>"` and `"policy": "authored"`, with purpose
   "LLM-written digest of how the project works — principles, rules,
   procedures, hand-offs, main ideas and gaps; feed to
   optimize_knowledge_base for structural feedback". The ontology entry is
   keyed `onto`, has no `file`, and adds `sourceScope` and `sourceGraph`.
   The other scopes follow the docs entry with their own key and purpose:
   `-pdfs-` "what the PDFs literally say", `-structure-` "which file
   imports which and what each defines — found by search, so a dynamic
   import can be missing", `-code-rationale-` "why the code is the way it
   is: WHY/NOTE/TODO comments and file header comments", `-entities-`
   "AI-written entity graph of the key code files: what calls, stores and
   exposes what — condensed, confirm specifics in the code", `-history-`
   "commit messages, pull requests and issues: what was decided, when and
   why" (plus its `cursor`).
   `topics` and `gaps` come from the upload responses; `hint` from one
   `generate_contextual_hint` call and `diversity` + `develop` from one
   `optimize_text_structure` call per graph (best effort). This metadata is
   what enables the Step 0 fast path next session.
5. **Append a dated section to `infranodus/INFRANODUS_REPORT.md`** (create
   it with the header below if missing): `## Build <date>`, then per graph
   `### <graphName> — <url>`, its purpose, topics, gaps, and the full hint
   and development suggestions.

   ```markdown
   # InfraNodus log — <project>

   Append-only. Builds append a dated section below; query sessions append
   dated insights when something non-obvious is learned. Never rewrite or
   delete existing entries — the history IS the value.
   ```

**Updating a graph in place** (the update flow), per changed file, in this
order — always on the scope's own `graphName`:

1. Renamed: `update_statements({ graphName, categories: [<old path>],
   set: { removeCategories: [<old path>], addCategories: [<new path>] },
   confirm: true })` — relabels in place, nothing re-read.
2. Modified or deleted: `delete_statements({ graphName, categories:
   [<paths>], confirm: false })` is a dry run — show the user the matched
   count and a few lines, ask to confirm, then repeat with `confirm:
   true`. An error reply is fatal for that scope: append nothing and
   report it.
3. Modified or new: save the files' text as in step 2, to the SAME
   `graphName`.
4. Bookkeeping: `statements` = old − deleted + added, refresh `sources`,
   `builtAt`, `builtAtCommit`, `updated`, re-run the two enrichment
   calls, and append a `## Delta build <date>` section to the report
   (renamed, replaced and new files, counts).

Per scope: docs, PDFs, structure and code rationale are replaced file by
file as above (a changed code file means searching that file again for
both code scopes). History only appends: list what is newer than the
`cursor`, save it, move the cursor. Code entities are rebuilt in place
when one of their files changed; ask first, since it costs AI credits.

**Rebuilding a scope in place**: `delete_statements({ graphName,
deleteAll: true, confirm: false })` → show the count → `confirm: true` →
save the scope again under the same name. Never save on top of a graph
that was not cleared, and never clear a graph this skill did not create
(curated `wiki-*` graphs, `learn-*` graphs, entries of the full edition).

**Correcting the digest**: a few lines → edit the line in the local file
AND `update_statements({ graphName, edits: [{ match: "<old line exactly
as saved>", content: "<new line>" }], confirm: false })`, show the
before/after, repeat with `confirm: true`. A structural rewrite → edit the
file, then rebuild that scope in place.

## Step 4 — Register the project (REQUIRED, once)

Add this block to `<project>/CLAUDE.md` (create the file if missing). It
is delimited by markers: if the markers are already there, replace what is
between them; never touch anything outside them.

```markdown
<!-- infranodus:begin -->
## infranodus

This project's content is indexed as InfraNodus knowledge graphs.
`infranodus/manifest.json` is the routing table: per graph it records
`graphName`, `purpose` (what the graph is for), `topics`, `gaps`,
`hint` (structural overview), `diversity`
(biased/focused/diversified/dispersed), and `develop` (how the graph could
be developed further), plus its provenance — `endpoint`, `transport`,
`account`, `verified`.

Rules:
- For questions about themes, concepts, rationale, or what is missing or
  under-developed, query the graphs BEFORE reading or grepping files.
  Route via the manifest: match the question against each graph's
  `purpose` and `topics`, then call `analyze_existing_graph_by_name`
  (structure), `retrieve_from_knowledge_base` (content),
  `generate_contextual_hint` (broad questions),
  `generate_responses_from_graph` (advice), `generate_content_gaps`
  (direction).
- Read graph names from `infranodus/manifest.json` — do not guess them.
- If a graph query fails with "select an existing graph context", compare
  the manifest's `endpoint` and `account` with the server this session is
  connected to (`list_graphs`) and report a mismatch instead of retrying.
- `infranodus/INFRANODUS_REPORT.md` is an APPEND-ONLY log. After
  answering, append a dated one-line insight ONLY when something
  non-obvious and reusable was learned — never rewrite existing entries.
- The graphs cover meaning and discourse. Code structure is in them only
  when the manifest has a `structure` or `entities` scope, and those were
  built by search or by an AI model: confirm specifics in the code.
- After adding or substantially editing content, run `/infranodus` to
  refresh the affected scope: the changed files' statements are replaced
  in place — no graph is deleted or duplicated.
<!-- infranodus:end -->
```

**Ask before adding the insight-memory convention — one AskUserQuestion at
this step.** Skip the question when `CLAUDE.md` already contains
`<!-- infranodus-memory:begin -->`. Otherwise:

- Question: "Register the project's graphs in CLAUDE.md. Also install the
  end-of-session insight memory convention? At the end of substantive
  sessions the agent would distill YOUR realizations into timestamped
  relations and save them to the `<slug>-insights` graph in your InfraNodus
  account — always shown to you first, saved only on your OK."
- **"Routing + insight memory (Recommended)"** → add both blocks.
- **"Routing rules only"** → add the block above only.

The second block (`<slug>-insights`: the folder slug, the whole name at
most 28 characters):

```markdown
<!-- infranodus-memory:begin -->
## end-of-session insight memory

At the end of a substantive session (analysis, digest build, synthesis —
not quick edits or trivial questions), distill the USER's insights from the
conversation — the new connections and realizations they arrived at, not
agent mechanics and not project content — into short relational statements
and save them to InfraNodus memory:

- Tool: `memory_add_relations`, graph `<slug>-insights`.
- One insight per statement, at most two sentences, with at least two
  `[[wikilinked]]` entities, and an ISO 8601 timestamp per statement.
- Show the statements to the user and get their OK before saving.
- Zero insights is a normal outcome — do not pad.
- To recall earlier insights on a concept, use `memory_get_relations`
  with the entity name (memory graph `<slug>-insights`).
<!-- infranodus-memory:end -->
```

Never install the memory block unasked: it commits every future session to
proposing writes to the user's InfraNodus account.

- **Build path only.** Never edit CLAUDE.md while answering a question via
  the Step 0 fast path.
- **Say that you did it.** One line in the report: "added the
  `## infranodus` block to `CLAUDE.md` so questions route to these graphs —
  delete the marked block to opt out."
- In an llm-wiki project the CLAUDE.md is the user's co-authored wiki
  schema: the marker block appends alongside it.

## Step 5 — The insight log (append-only)

`infranodus/INFRANODUS_REPORT.md` is a LOG, not a snapshot. Do not rewrite
it into a report — at most append one short dated paragraph of your own
reading of the results if it adds something the build section doesn't say.

Finish the build by printing the graph URL(s) — they open in the browser,
the InfraNodus VSCode/Cursor extension, and the Obsidian plugin.

## Step 6 — Structural feedback (optimize the code base / vault / rules)

When the user chose the digest mode, or asks to *optimize*, *review*, or
find *what is missing / under-developed* in the project, run
`optimize_knowledge_base` on the most relevant saved graph:

| the user's project is… | `graphName` | `focus` | `compareWith` |
|---|---|---|---|
| a code base | `repo-<p>-digest` (or `-docs`) | `codebase` | `repo-<p>-structure` when it exists (rules and docs without code, code without rules), else the other of the two |
| a document vault | `vault-<p>-docs` (or `-digest`) | `vault` | the other of the two, when both exist |
| procedural knowledge (rules, frameworks, playbooks) | `repo-<p>-digest` | `procedural` | the docs graph |

Report to the user, in this order: the state and its reading (`meaning`,
`action`), the dominant cluster, the under-developed areas, the missing
bridges, the comparison findings when `compareWith` was given, and the AI
suggestions last. Offer to record the key findings with
`add_project_learnings` if learnings are enabled for the project. Do not
rebuild the graph to "fix" it — the feedback is about the project, not the
graph.

## Query mode (after a graph exists)

ALL manifest scopes are queryable regardless of their `policy` or who
built them — including curated `wiki-*` graphs that llm-wiki created and
the scopes of the full edition. Policy governs who WRITES; reading the
graphs is open to everyone.

Route via the manifest: match the question against each graph's `purpose`
and `topics`, then:

- "Is this coherent / what is missing / what should we develop" → Step 6
  on `digest` or `docs`.
- "What are the rules / how is X supposed to be done / why is it done this
  way" → `retrieve_from_knowledge_base` on `digest` if it exists, else
  `docs`.
- "How does it fit together" / typed-relation questions → the `onto` scope
  if it exists; it is condensed and may omit things, so confirm specifics
  against `docs`.
- "What depends on X / what imports X / where is X defined" →
  `get_node_neighborhood` on the `structure` scope with the file path or
  name as the node; "what calls or stores X" → the same on `entities`.
- "Why is this code the way it is" → `retrieve_from_knowledge_base` on
  `code-rationale`, then `history`.
- "What was decided about X, and when" → `retrieve_from_knowledge_base`
  on `history`; "discussed but never documented" →
  `difference_between_texts` with the `docs` and `history` graphs.
- Structure questions ("main themes", "how organized") →
  `analyze_existing_graph_by_name`
- Broad/overview questions → `generate_contextual_hint` first, then
  `retrieve_from_knowledge_base` for specifics
- Content questions ("how does X work", "what was decided about Y") →
  `retrieve_from_knowledge_base` with the question as `prompt`
- Advice/recommendation questions → `generate_responses_from_graph` with
  the question as `prompt`
- Direction questions ("what's missing", "what next") →
  `generate_content_gaps`, then optionally `generate_research_questions`
- When synthesizing across several graphs or drafting recommendations,
  pass the draft reasoning to `optimize_reasoning`. One check per
  substantial synthesis — not per answer.

Consult the insight log's past entries before answering; after answering,
APPEND a dated one-line insight ONLY when something non-obvious and
reusable was learned. Never rewrite or delete existing entries.

## Conventions

- **Shared wikilink namespace:** file paths appear verbatim as
  `[[docs/setup.md]]` in every scope — identical strings are the join keys
  that let merged and difference views stitch scopes together.
- **Separate graphs per scope** by default; merged view on demand via
  `merged_graph_from_texts` with `{graphName}` contexts; cross-scope
  comparison via `difference_between_texts` the same way.
- In an llm-wiki project (wiki CLAUDE.md schema present), this workflow
  complements the curated ontologies: same `infranodus/` folder, same
  manifest; never edit a file whose manifest entry says `curated`.
