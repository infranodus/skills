# Repo / Vault Graphs — the /infranodus folder workflow

Build a knowledge graph of the current repo or Obsidian vault, save it to
InfraNodus, and write a report. Deterministic collection (no LLM),
server-side graph computation. Division of labor:

- **Uploads** (bulk writes): the InfraNodus MCP server already connected
  to the session comes FIRST (e.g. the claude.ai InfraNodus connector) —
  the agent uploads through its `create_knowledge_graph` tool per Step 3's
  Path A contract. The bundled `scripts/upload_scopes.py` is the FALLBACK
  for sessions with no InfraNodus MCP tools: it uploads through the MCP
  server configured in this agent's own config (`<project>/.mcp.json` →
  `~/.claude.json` project section → `~/.claude.json` global →
  `~/.claude/settings.json`, project scope winning). An `http` entry is
  posted to its own `url`; a `stdio` entry is launched as a subprocess.
  Credentials are never read from config files: `http` takes
  `INFRANODUS_API_KEY` from the environment only, `stdio` hands the entry's
  own `env` to the subprocess untouched. The script cannot reach a cloud
  OAuth connector (its token lives remotely) — that is why the connector
  path is agent-driven.
- **Queries** (reads): the session's native InfraNodus MCP tools
  (`mcp__infranodus__<tool>` or the connector's equivalents).

Before a script-path upload, `upload_scopes.py [project_dir] --check-auth`
resolves the server and verifies the connection, printing the transport and
endpoint. Failure handling:

- **No session tools and no server configured** — the script prints
  `claude mcp add` commands for the hosted and the local option. Ask:
  **A)** add the hosted server (needs an API key: infranodus.com →
  settings → API access), **B)** add a local / self-hosted one, **C)** skip
  upload — keep the local scope files only (they still render in
  Obsidian). Never guess an endpoint.
- **Configured server's connection failed** — if the session has
  InfraNodus MCP tools, switch to Path A and continue; otherwise report
  the endpoint and the error verbatim and stop. Do NOT hunt for another
  key or endpoint; a 401 means the wrong key for *that* server, not
  permission to use another.

After a build, each scope carries `endpoint`, `transport`, `account`, and
`verified` in the manifest. When a later query fails, check those first —
a `graphName` only resolves against the server and account that hold it.

## Step 0 — Fast path (ALWAYS check first)

If `infranodus/manifest.json` exists in the project root AND the user is
asking a question (not requesting a build/update): **do not re-extract**.
Answer from the existing graphs (graph names from the manifest — never
guess them):

- structure / clusters / influence / gaps → `analyze_existing_graph_by_name`
- specific question, GraphRAG over the statements →
  `retrieve_from_knowledge_base` with the question as `prompt`
- "what is missing / what should we work on" → `generate_content_gaps`,
  then optionally `generate_research_questions`

Rebuild only when the user says so ("rebuild", "refresh", "--update") or
when the repo clearly changed since `manifest.json`'s `updated` dates.

## Step 1 — Understand the corpus, then ASK what to build

On a bare launch (user asked to graph/analyze the project without naming a
target), do a quick inventory first — top-level folders, md/code file
counts, biggest docs, and non-minable documents — e.g.:

```bash
ls -d */ | head -20
find . -name "*.md" -not -path "./node_modules/*" | wc -l
find . \( -name "*.pdf" -o -name "*.docx" -o -name "*.epub" \) \
  -not -path "./node_modules/*" | wc -l
```

**Routing check:** the scanner mines md/code/git, and PDFs *when a
text-layer converter is installed* (pdftotext from poppler, mutool, or
markitdown — checked with `command -v pdftotext mutool markitdown`).
It cannot read docx/epub, and it never OCRs. Route accordingly:

- PDFs present + a converter installed → the scan covers them
  (deterministic extraction of what the PDFs literally say, into their
  own scope) — mention that in the question below.
- PDFs present, no converter → say so and offer both paths: install
  poppler (`brew install poppler`) for the structural scan, or the
  llm-wiki skill for an LLM-authored knowledge base.
- Corpus dominated by scanned PDFs (extraction comes back empty),
  docx/epub, or other non-minable documents → don't run a scan that
  will come back empty; point at the llm-wiki skill ("this corpus needs
  LLM-authored summarization — the llm-wiki skill builds and maintains
  that kind of knowledge base") and, if it is listed among the available
  skills, offer to invoke it.

The two products differ, and both can be useful on the same corpus: this
scan = a reproducible structural map of what the documents literally say
(clusters, gaps, cross-document differences); llm-wiki = a curated,
compounding knowledge base about them.

Then use **AskUserQuestion** (single question, not multiSelect) following
this structure: one sentence re-grounding (what folder, what you detected —
"this is an Obsidian vault with 480 notes in 7 folders"), then the options:

1. **Full graph (Recommended)** — everything the bare scan covers: all
   docs/notes + link structure (vault) or docs + code rationale + git/PR
   history (repo). → `repo2statements.py .`
2. **A specific folder only** — follow-up AskUserQuestion listing the
   top-level folders from the inventory as options (+ Other for a path).
   → `repo2statements.py . --include <folder>`
3. **Only documents containing certain terms** — follow-up question for the
   terms (seed options with 2-3 themes evident from folder/file names;
   Other for custom; multiple terms = any-of match).
   → `repo2statements.py . --term "<term1>" --term "<term2>"`
4. **A specific document only** — follow-up listing 3 notable candidates
   (largest / most-linked md files) + Other for a path.
   → `repo2statements.py . --include <path/to/doc.md>`
5. Handled by AskUserQuestion's built-in **Other**: a user-defined scope in
   free text — map it to the closest flag combination (`--include` and/or
   `--term`; both compose, `--vault` for structure-only).

Skip the *scope* question when the user already named the target ("graph
the docs folder", "analyze notes mentioning trading") — map straight to the
flags.

**Then ALWAYS ask the build mode** (a second AskUserQuestion, `multiSelect:
true`, asked even when the target was named — it decides cost and what the
graphs can answer). Options, all combinable:

1. **Full ingestion (Recommended for small/medium repos)** — everything the
   scan covers: docs, code rationale, git/PR history (or notes + links in a
   vault). Many uploads, no LLM. → `repo2statements.py . <scope flags>`
   Answers: *what does the project say about X*.
2. **Digest** — a condensed structural map: directory tree, file → imports
   and dependencies, exported symbols, first docstring line per file,
   package manifests. A few uploads, no LLM; the sensible default for a big
   repo. → `repo2statements.py . <scope flags> --digest`
   Answers: *how is the project organised, what depends on what*.
3. **Principles digest + structural feedback** — a conceptual digest: the
   rules (must / never / should sentences), frameworks (headings) and main
   ideas (first sentence per section) found in docs, notes, and agent
   instruction files (CLAUDE.md, .cursorrules, SKILL.md …), with their
   [[wikilinks]]. Cheap, no LLM for the extraction; then
   `optimize_knowledge_base` on the uploaded graph gives the structural
   feedback (Step 6). → `repo2statements.py . <scope flags> --principles`
   Answers: *what does this project say one must do, is that set of rules
   coherent, what is under-developed or never connected*.
4. **Ontology** — an AI-condensed ontology graph (`onto-<project>`: entities
   and typed relations) generated by `generate_ontology_graph` from an
   uploaded graph: from the **digest** when one exists (codebase mode:
   modules, functions, data stores, services, concepts), otherwise from the
   **docs** scope of a full ingestion (general mode). Costs LLM tokens and
   is lossy by design. Requires 1 or 2. → Step 3's ontology substep.
   Answers: *how do the parts fit together*.

Full, Digest and Principles are separate script runs (scopes are
independent files that share the manifest). Note the choices in your reply
before building. Filtered scans get their own suffixed scope files and graphs
(`repo-docs-<slug>-ontology.md`), so they never clobber the full scan — a
later full run can coexist with them in the same manifest.

## Step 2 — Extract

```bash
python3 <SKILL_DIR>/scripts/repo2statements.py .            # full scan
python3 <SKILL_DIR>/scripts/repo2statements.py . --vault    # vault STRUCTURE only
```

Stdlib-only, deterministic, no LLM. A bare launch mines the
natural-language layer (code-structure extraction is deferred — do not
attempt it by reading source files yourself):

- `repo-docs-ontology.md` — md/rst/txt paragraphs, grouped under
  `## [[<filepath>]]` section headings
- `repo-pdfs-ontology.md` — the text layer of `*.pdf` files (only when
  pdftotext/mutool/markitdown is installed; deterministic cleanup: no
  headers/footers/page numbers, prose paragraphs only), same headings.
  Scanned PDFs without a text layer are reported and skipped — no OCR.
  Extracted text stays in memory; no converted files land in the project.
- `repo-code-rationale-ontology.md` — docstrings + `WHY:`/`NOTE:`/`TODO:`/
  `HACK:`/`FIXME:` comments, tagged `#docstring` / `#why` / …, same headings
- `repo-history-ontology.md` — commit bodies (`#commit`), PR descriptions
  (`#pr`), issue threads (`#issue`) via `git` and `gh`

In an Obsidian/md vault (auto-detected: `.obsidian/` or md-dominated) it
ALSO maps the page-link structure (`vault-links-ontology.md`) and names doc
sections after page stems (`## [[Page A]]`) so content and link scopes share
node names. `--vault` maps ONLY the structure, no content mining.

Each scope file declares its upload mode in frontmatter (`wikilinksMode:
parentAndConcepts` for prose — the `## [[page]]` heading travels as a
per-statement parent without suppressing the prose; `wikilinksOnly` for
link scopes — only `[[page]]` wikilinks become nodes).
Likely-secret files (`.env*`, keys, anything named credential/secret/apikey)
are never mined. The script also creates/updates `infranodus/manifest.json`.

**Scope files are build intermediates, not artifacts.** The uploader
deletes each one after its statements are safely in the graph (they stay
if the upload fails or is skipped, and `--keep-scopes` retains them — e.g.
to render in Obsidian). The persistent local record is the manifest + the
insight log; the content lives in the graphs.

## Step 3 — Upload (one graph per scope)

### Path A — session MCP server (PREFERRED when InfraNodus tools are connected)

The agent drives the upload through the session's `create_knowledge_graph`.
The contract mirrors the script exactly:

1. **Chunk deterministically** with the script's own chunker (strip the
   frontmatter first, keep the heading-aware boundaries):

   ```bash
   python3 - <<'EOF'
   import importlib.util, re, os
   spec = importlib.util.spec_from_file_location(
       "up", "<SKILL_DIR>/scripts/upload_scopes.py")
   up = importlib.util.module_from_spec(spec); spec.loader.exec_module(up)
   for fname in sorted(os.listdir("infranodus")):
       if not fname.endswith("-ontology.md"): continue
       body = re.sub(r"^---.*?---\s*", "",
                     open(f"infranodus/{fname}").read(), flags=re.S)
       scope, gname = up.scope_graph_name("<prefix>", fname)
       for i, c in enumerate(up.chunk_text(body, 25_000), 1):
           open(f"<scratchpad>/chunks/{gname}.{i:02d}.txt", "w").write(c)
   EOF
   ```

   ~25 KB per chunk keeps each piece inside tool I/O windows (the API
   itself rejects ~100 KB+ with 413).

2. **Upload every chunk of a scope to ONE `graphName`**
   (`repo-<project>-<scope>` / `vault-<project>-<scope>` — same naming as
   the script) with `{graphName, text: <chunk>, maxNodes: 500,
   wikilinksMode: <the scope's frontmatter mode>}`. Uploads APPEND
   server-side: never re-send a chunk that already succeeded. Pace calls;
   on 429 wait ~5 min and retry the same chunk; on 413 split the chunk in
   half and send the halves.

3. **Ontology substep (only if the user chose it).** After the source scope
   is uploaded and verified, one call:
   `generate_ontology_graph({ sourceGraphName: "<repo-<project>-digest>"
   (or `-docs`), graphName: "onto-<project>", ontologyMode: "codebase"
   (digest) | "general" (docs), saveGraph: true, includeGraph: false })`.
   The server reads the source graph, chunks it, and appends one ontology
   per chunk to the same graph — expect it to take a minute or more; pass a
   progress token if the client supports it. Record it in the manifest as
   scope `onto` (no `file`; `sourceScope`, `sourceGraph`, `purpose`: the
   `onto` entry of the script's `SCOPE_PURPOSES`).

4. **Do the script's per-scope bookkeeping yourself** (Path A skips the
   script, not the record-keeping): the manifest entry and report section
   described below, with `transport: "session-mcp"`, the connector's name
   as `endpoint` (e.g. `claude.ai InfraNodus connector -> infranodus.com`),
   the `account` segment parsed from the returned graph URL, and today's
   date as `verified`. Then delete the scope file (or keep on
   user request).

Path B does the same with `upload_scopes.py . --ontology` (or
`--ontology-from docs`).

### Path B — the bundled script (fallback: no InfraNodus tools in session)

```bash
python3 <SKILL_DIR>/scripts/upload_scopes.py .            # long-running: use run_in_background
python3 <SKILL_DIR>/scripts/upload_scopes.py . --prefix repo-myproject
python3 <SKILL_DIR>/scripts/upload_scopes.py . --force    # re-upload (APPENDS — see below)
```

Do NOT hand-roll ad-hoc upload loops outside these two paths — Path A
exists precisely so the chunking, pacing, appending, and bookkeeping
rules still hold when the agent uploads directly. The script chunks on
heading-aware line boundaries, paces calls 20 s apart, backs off 5 min on
429s, bisects on 413s, uploads all chunks of a scope under ONE
`graphName` (`repo-<project>-<scope>` / `vault-<project>-<scope>`),
sets `maxNodes: 500` and the scope's declared `wikilinksMode` (these bind
when the graph is FIRST created), and then, per scope:

- records the **routing metadata** into the manifest: `graphName`, `url`,
  `purpose` (what the graph is for), `topics` and `gaps` (harvested from
  the upload response), plus two best-effort enrichment calls per graph —
  `hint` (`generate_contextual_hint`: structural overview — concepts,
  gateways, relations, diversity) and `diversity` + `develop`
  (`optimize_text_structure`: bias/focus diagnosis + condensed suggestions
  for further development). This is what enables the Step 0 fast path and
  question routing next session;
- appends a dated build section to `infranodus/INFRANODUS_REPORT.md` with
  the same metadata in full (complete hint and untruncated development
  suggestions, in collapsible blocks);
- deletes the scope file (see Step 2; `--keep-scopes` retains it).

**Append rule:** uploads to an existing `graphName` APPEND statements
server-side. A clean rebuild of an already-uploaded scope = delete the
graph in InfraNodus first, then `--force`. `--force` without deleting
duplicates every statement.

`--save-graph` additionally exports `infranodus/<scope>-graph.json` per
scope — opt-in only, for offline/renderable copies; the server is the
source of truth and every query goes there.

A large corpus can take many minutes (rate limits allow only a few calls
per window on some plans) — launch in the background and check its output
rather than waiting inline.

## Step 4 — Register the project (REQUIRED, once)

```bash
python3 <SKILL_DIR>/scripts/upload_scopes.py . --register-project
```

Writes the always-on `## infranodus` block into `<project>/CLAUDE.md`
(marker-delimited, idempotent: a re-run replaces a stale block; content
outside the markers is untouched) so future sessions query these graphs for
questions about themes, concepts, rationale, and gaps instead of grepping
files. **This is the step that makes the graphs get used** — without it
they exist and nothing ever consults them.

- **Build path only.** Never run it while answering a question via the
  Step 0 fast path — editing CLAUDE.md is not what a question asked for.
- **Say that you did it.** One line in the report: "added the
  `## infranodus` block to `CLAUDE.md` so questions route to these graphs —
  delete the marked block to opt out."
- If the project also uses a code-graph tool (graphify and similar), the
  block defers to it for files/symbols/call paths and claims only meaning
  and discourse structure. Keep that boundary.
- In an llm-wiki project the CLAUDE.md is the user's co-authored wiki
  schema: the marker block appends alongside it — never replace or
  reorganize anything outside the markers.

## Step 5 — The insight log (append-only)

`infranodus/INFRANODUS_REPORT.md` is a LOG, not a snapshot. The uploader
already appended this build's dated section (per graph: purpose, topics,
gaps, URL). Do not rewrite it into a report — at most append one short
dated paragraph of your own reading of the results (e.g. "docs and history
scopes barely overlap — decisions are discussed in PRs but never
documented") if it adds something the raw sections don't say.

Finish the build by printing the graph URL(s) — they open in the browser,
the InfraNodus VSCode/Cursor extension, and the Obsidian plugin.

## Step 6 — Structural feedback (optimize the code base / vault / rules)

When the user chose the Principles mode, or asks to *optimize*, *review*,
or find *what is missing / under-developed* in the project, run
`optimize_knowledge_base` on the most relevant uploaded graph:

| the user's project is… | `graphName` | `focus` | `compareWith` |
|---|---|---|---|
| a code base | `repo-<p>-principles` (or `-docs`) | `codebase` | `repo-<p>-digest` — rules/docs without code, code without rules |
| a document vault | `vault-<p>-docs` (or `-principles`) | `vault` | `vault-<p>-links` |
| procedural knowledge (rules, frameworks, playbooks) | `repo-<p>-principles` | `procedural` | the docs or digest graph |

Report to the user, in this order: the state and its reading (`meaning`,
`action`), the dominant cluster, the under-developed areas, the missing
bridges (with the focus-specific meaning: integrations / bridge notes /
hand-offs), the comparison findings when `compareWith` was given, and the
AI suggestions last. Offer to save the resulting plan with the actionize
skill if it is installed, and to record the key findings with
`add_project_learnings` if learnings are enabled for the project. Do not
re-run the extraction to "fix" the graph — the feedback is about the
project, not the graph.

## Query mode (after a graph exists)

ALL manifest scopes are queryable regardless of their `policy` — including
curated `wiki-*` graphs that llm-wiki created. Policy governs who WRITES
the files (never edit a file whose manifest entry says `curated`); reading
the graphs is open to everyone.

Route via the manifest: match the question against each graph's `purpose`
and `topics`, then:

- Architecture questions ("what depends on X", "which module exposes Y",
  "how is this organised") → the `digest` scope: `retrieve_from_knowledge_base`
  with the module/file as `prompt`, or `analyze_existing_graph_by_name`
  for the dependency clusters.
- "Is this coherent / what is missing / what should we develop" → Step 6
  (`optimize_knowledge_base`) on `principles`, `docs`, or `digest`.
- "How does it fit together" / typed-relation questions → the `onto` scope
  if it exists; it is condensed and may omit things, so confirm specifics
  against `digest` or `docs`.
- Structure questions ("main themes", "how organized") →
  `analyze_existing_graph_by_name`
- Broad/overview questions ("what is this project about", "give me the
  lay of the land") → `generate_contextual_hint` first — a lightweight
  structural summary (concepts, topics, gaps, gateways, diversity) to
  ground the answer — then `retrieve_from_knowledge_base` for specifics
- Content questions ("how does X work", "what was decided about Y") →
  `retrieve_from_knowledge_base` with the question as `prompt`
- Advice/recommendation questions ("what should we do about X", "how
  would this project approach Y") → `generate_responses_from_graph` with
  the question as `prompt` — generates an answer grounded in the graph's
  own concepts and relations rather than retrieving raw statements
- Direction questions ("what's missing", "what next") →
  `generate_content_gaps`, then optionally `generate_research_questions`
- When synthesizing across several graphs or drafting recommendations,
  pass the draft reasoning to `optimize_reasoning`: it diagnoses whether
  the reasoning is biased (fixated on one cluster), focused, diversified,
  or dispersed, and suggests which under-represented topics or gaps to
  develop further. One check per substantial synthesis — not per answer.

Consult the insight log's past entries before answering; after answering,
APPEND a dated one-line insight ONLY when something non-obvious and
reusable was learned — a confirmed gap, a user correction, a dead end
("[[X]] not covered by any scope"). Routine successful answers are not
logged. Never rewrite or delete existing entries.

## Conventions

- **Shared wikilink namespace:** file paths appear verbatim as
  `[[src/auth/service.py]]` in every scope — identical strings are the join
  keys that let merged and difference views stitch scopes together. Never
  paraphrase a path.
- **Separate graphs per scope** by default; merged view on demand via
  `merged_graph_from_texts` with `{graphName}` contexts; cross-scope
  comparison via `difference_between_texts` the same way (e.g. docs vs
  history = "discussed but never documented"). No local files needed.
- **Obsidian:** upload with `--keep-scopes` to retain the scope files —
  plain md with wikilinks; copied into a vault, the InfraNodus Obsidian
  plugin renders them in "[[Wiki Links]] and Concepts" mode.
- In an llm-wiki project (wiki CLAUDE.md schema present), this workflow
  complements the curated ontologies: same `infranodus/` folder, same
  manifest; only `generated: true` files are ever overwritten.
