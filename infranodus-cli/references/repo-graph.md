# Repo / Vault Graphs — the /infranodus folder workflow

Build a knowledge graph of the current repo or Obsidian vault, save it to
InfraNodus, store everything locally, and write a report. Deterministic
collection (no LLM), server-side graph computation.

## Transport — pick ONCE, before anything else

All InfraNodus calls in this workflow go through whichever transport is
available, in this order:

1. **Native MCP tools** — if InfraNodus tools are already visible in this
   session (tool names like `mcp__infranodus__create_knowledge_graph` or an
   InfraNodus connector), **use them directly** for every query AND for
   uploads. Do not install, configure, or call mcporter — a working mcporter
   already on the machine changes nothing; while native tools exist it is
   dead to this workflow. For uploads, do NOT run `upload_scopes.py`'s
   upload mode — instead:
   ```bash
   python3 <SKILL_DIR>/scripts/upload_scopes.py . --emit-chunks
   ```
   Emit mode writes chunks of ≤45 KB — deliberately smaller than the API's
   payload limit so each chunk fits through the agent context in ONE full
   Read. Then per scope, for each chunk file IN ORDER:
   - Read the chunk file COMPLETELY (one Read; no offset/limit slicing).
     If the Read comes back truncated, do not upload the partial text and
     do not switch transport — re-run with a smaller size, e.g.
     `--emit-chunks --chunk-bytes 30000`, and start that scope over.
   - Call `create_knowledge_graph` natively with the chunk's exact contents
     as `text` (byte-exact — strip only the Read tool's line-number
     prefixes, change nothing else) plus that scope's `graphName`,
     `maxNodes`, and `wikilinksMode` from the printed plan (statements
     accumulate; wikilinksMode/maxNodes bind on the FIRST call that creates
     the graph). Pace calls ~20 s apart and back off minutes, not seconds,
     on rate-limit errors.
   Then, once a scope's chunks are all uploaded, finish it with BOTH of
   these — a scope is not done until both exist:
   - `upload_scopes.py . --record <scopeFile> <graphName> <url>` to write
     `graphName` + `url` into the manifest.
   - Call `analyze_existing_graph_by_name` natively with `includeGraph:
     true` **and `addNodesAndEdges: true`**, and Write the response verbatim
     to that scope's `graphJson` path from the emitted plan
     (`infranodus/<scope>-graph.json`, where `<scope>` is the scope file
     name minus the `repo-`/`vault-` prefix and the `-ontology.md` suffix —
     `repo-docs-projects-ontology.md` → `infranodus/docs-projects-graph.json`).

   `addNodesAndEdges` is what fills `knowledgeGraph.nodes[]` and
   `knowledgeGraph.edges[]`. Without it, `includeGraph` returns only
   `knowledgeGraph.attributes` (modularity, top_clusters, gaps) — useful as
   a summary, but not a graph you can render or traverse offline.

   A full graph response runs to hundreds of KB. If the harness spills it
   verbatim to a tool-results file, COPY that file byte-for-byte to the
   destination instead of retyping the JSON — retyping a 200 KB response
   risks silent truncation. Verify either way:
   `python3 -c "import json;kg=json.load(open(P))['knowledgeGraph'];print(len(kg['nodes']),len(kg['edges']))"`

   Node count note: retrieval compacts to the server default (~150 nodes)
   and `analyze_existing_graph_by_name` has NO `maxNodes` parameter, so a
   graph created with `maxNodes: 500` still exports ~150. The `fullGraph:
   true` flag overrides compaction where the server build supports it —
   check the running server's schema rather than assuming.

   `--record` updates the manifest and nothing else; it does NOT fetch. The
   fetch-and-save lives inside upload mode (transport 2), so on the native
   path it only happens if you do it explicitly — and skipping it leaves
   the local graph JSON this workflow promises silently missing, with a
   manifest that looks complete.

   Delete `infranodus/.chunks/` once every scope has both.
2. **mcporter** — ONLY when no native tools are in the session, and
   `mcporter` is on PATH and configured (`mcporter list infranodus`
   healthy): use the `mcporter call` commands as written below;
   `upload_scopes.py` upload mode uses it automatically.
3. **Neither** — extraction still works (local scope files are always built);
   for upload/queries, attempt setup:
   - `npm install -g mcporter` (needs Node; if npm is missing, stop and tell
     the user what to install).
   - If `INFRANODUS_API_KEY` is not set, AskUserQuestion: **A)** paste an API
     key now (from infranodus.com → settings → API access — recommended),
     **B)** OAuth browser login (`mcporter auth infranodus`), **C)** skip
     upload — keep local files only (they still render in Obsidian).
   - Then `mcporter config add infranodus ...` (see SKILL.md Setup & Auth)
     and continue as transport 2.

## Step 0 — Fast path (ALWAYS check first)

If `infranodus/manifest.json` exists in the project root AND the user is asking
a question (not requesting a build/update): **do not re-extract**. Answer from
the existing graphs:

```bash
# structure / clusters / influence / gaps of the whole project:
mcporter call infranodus.analyze_existing_graph_by_name --args '{"graphName": "<from manifest>"}'
# specific question, GraphRAG over the statements:
mcporter call infranodus.retrieve_from_knowledge_base --args '{"graphName": "<from manifest>", "prompt": "<user question>"}'
# "what is missing / what should we work on":
mcporter call infranodus.generate_content_gaps --args '{"graphName": "<from manifest>"}'
```

(As everywhere in this skill: with native MCP tools available, call
`mcp__infranodus__<tool>` directly with the same arguments instead of these
`mcporter call` commands.)

Rebuild only when the user says so (`--update`, "rebuild", "refresh") or when
the repo clearly changed since `manifest.json`'s `updated` dates.

## Step 1 — Understand the corpus, then ASK what to build

On a bare launch (user asked to graph/analyze the project without naming a
target), do a quick inventory first — top-level folders, md/code file counts,
biggest docs — e.g.:

```bash
ls -d */ | head -20; find . -name "*.md" -not -path "./node_modules/*" | wc -l
```

Then use **AskUserQuestion** (single question, not multiSelect) following this
structure: one sentence re-grounding (what folder, what you detected — "this
is an Obsidian vault with 480 notes in 7 folders"), then the options:

1. **Full graph (Recommended)** — everything the bare scan covers: all
   docs/notes + link structure (vault) or docs + code rationale + git/PR
   history (repo). → `repo2statements.py .`
2. **A specific folder only** — follow-up AskUserQuestion listing the
   top-level folders from the inventory as options (+ Other for a path).
   → `repo2statements.py . --include <folder>`
3. **Only documents containing certain terms** — follow-up question for the
   terms (seed options with 2-3 themes evident from folder/file names; Other
   for custom; multiple terms = any-of match).
   → `repo2statements.py . --term "<term1>" --term "<term2>"`
4. **A specific document only** — follow-up listing 3 notable candidates
   (largest / most-linked md files) + Other for a path.
   → `repo2statements.py . --include <path/to/doc.md>`
5. Handled by AskUserQuestion's built-in **Other**: a user-defined scope in
   free text — map it to the closest flag combination (`--include` and/or
   `--term`; both compose, `--vault` for structure-only).

Skip the question entirely when the user already named the target ("graph the
docs folder", "analyze notes mentioning trading") — map straight to the flags.
Filtered scans get their own suffixed scope files and graphs
(`repo-docs-<slug>-ontology.md`), so they never clobber the full scan — a
later full run can coexist with them in the same manifest.

## Step 2 — Extract (detection is inside the script)

Run the bundled script (stdlib-only Python 3, no dependencies):

```bash
python3 <SKILL_DIR>/scripts/repo2statements.py .            # bare launch: full scan
python3 <SKILL_DIR>/scripts/repo2statements.py . --vault    # vault STRUCTURE only
```

**Bare launch** mines the natural-language layer (code-structure extraction is
deferred — do not attempt it by reading source files yourself):
- `repo-docs-ontology.md` — md/rst/txt paragraphs, grouped under
  `## [[<filepath>]]` section headings (the parent-page contract of the
  MCP `parentAndConcepts`/`obsidianStyle` wikilinksMode: the heading sets
  each statement's parent page while keeping the statement text clean)
- `repo-code-rationale-ontology.md` — docstrings + `WHY:`/`NOTE:`/`TODO:`/
  `HACK:`/`FIXME:` comments, tagged `#docstring` / `#why` / `#note` / …,
  grouped under the same `## [[<filepath>]]` headings
- `repo-history-ontology.md` — commit-message bodies (`#commit`), PR
  descriptions (`#pr`), issue threads (`#issue`) via `git` and `gh`

Each generated file declares its intended processing in the frontmatter
(`wikilinksMode: parentAndConcepts` / `wikilinksOnly`) — any consumer that
processes a scope file separately (e.g. straight through the MCP tools)
should honor that declared mode.

The script auto-detects a vault (`.obsidian/` present, or md-dominated
folder). On a bare launch in a vault it ALSO runs the link scan
(`vault-links-ontology.md`) and names doc sections after the Obsidian page
stems (`## [[Page A]]` instead of `## [[notes/Page A.md]]`) so the content
scope and the link scope share node names and stitch into one graph.

**`--vault` flag** = map the vault structure ONLY: just
`vault-links-ontology.md` with one `[[Page A]] links to [[Page B]]` statement
per page connection, no content mining.

The script also creates/updates `infranodus/manifest.json` (the scope
registry). Files carry `generated: true` frontmatter → they are regenerated,
never hand-edited or appended to (curated ontologies from the llm-wiki skill
lack that flag and stay append-only).

## Step 3 — Upload (one graph per scope)

On transport 1 (native tools in session) SKIP this section's upload mode —
use the `--emit-chunks` native procedure from the Transport section above;
running the uploader here would route through mcporter. On transport 2, run
the bundled uploader — do NOT hand-roll `mcporter call
create_knowledge_graph` loops for scope files; the API rejects payloads over
~100 KB with a 413 and rate-limits bursts with a 429, and the script handles
both:

```bash
python3 <SKILL_DIR>/scripts/upload_scopes.py .                    # long-running: use run_in_background
python3 <SKILL_DIR>/scripts/upload_scopes.py . --prefix repo-myproject
python3 <SKILL_DIR>/scripts/upload_scopes.py . --force            # re-upload already-uploaded scopes
```

What it does per scope in `infranodus/manifest.json` (skipping scopes that
already have a `graphName`, unless `--force`):

- strips frontmatter, splits the text into ≤80 KB line-boundary chunks, and
  uploads them all under ONE `graphName` (`repo-<project>-<scope>` /
  `vault-<project>-<scope>`, auto-derived; override with `--prefix`) —
  statements accumulate in one context
- sets `maxNodes: 500` (the server default of 150 truncates repo/vault-sized
  corpora) and a per-scope `wikilinksMode` (recorded in the manifest):
  **link scopes** (`vault-links`) → `"wikilinksOnly"`, so only the `[[page]]`
  wikilinks become nodes — without it the repeated words "links"/"to" would
  form a fake hub; **prose scopes** (docs, rationale, history) →
  `"parentAndConcepts"`, where the `## [[page]]` section heading (or a
  `[[Page]]: ` line prefix) travels as a per-statement parent category
  (mention) instead of inline text — the page node connects to its
  statements' concepts WITHOUT suppressing the prose (an inline `[[Page]]`
  hashtag prefix makes the engine drop every non-wikilink word of that
  statement). The mode comes from the scope file's own frontmatter
  declaration when present. Chunking is heading-aware: a section split
  across chunks gets its heading re-emitted so no statement loses its
  parent. Both modes keep `[[name]]`-style node names, so all scopes
  merge/compare cleanly. These settings bind when the graph is first
  created; an existing graph keeps its original settings (delete it in
  InfraNodus and re-upload with `--force` to change them)
- paces calls 20 s apart; on a 429 waits 5 min and retries the same chunk
  (up to 24 times — observed lockouts can exceed an hour); on a 413 bisects
  the chunk and retries
- records `graphName` + `url` back into the manifest (this is what enables
  Step 0 next session)
- fetches the full graph via `analyze_existing_graph_by_name`
  (`includeGraph: true`) and saves it as `infranodus/<scope>-graph.json`

A large vault can take many minutes (rate limits allow only a few calls per
15-minute window on some plans) — launch it in the background and check its
output rather than waiting inline.

## Step 4 — Report

Write `infranodus/INFRANODUS_REPORT.md` — alongside the manifest, scope files,
and graph JSON, so every artifact this workflow produces lives in one folder —
from the upload responses. No extra analysis calls; the response already
contains everything:

```markdown
# InfraNodus Report — <project>
Graphs: <scope>: <graphName> (<url>) …  |  Built: <date>

## Structure
<modularity + diversity_stats in plain language: "focused — most discussion
concentrates in N of M clusters">

## Main topics            <- mainTopicalClusters
## Most influential       <- topInfluentialNodes (betweenness)
## Gateways               <- conceptualGateways (bridges between clusters)
## Gaps / what's missing  <- contentGaps — for a repo: rationale clusters that
                             never touch (e.g. caching decisions vs deploy
                             discussions); candidate docs/refactor targets
## Per-cluster graphs     <- knowledgeGraphByCluster (DOT, in <details> blocks)
```

Print the graph URL(s) at the end — they open in the browser, the InfraNodus
VSCode/Cursor extension, and the 3D view.

## Query mode (after a graph exists)

- Structure questions ("what are the main themes", "how organized") →
  `analyze_existing_graph_by_name`
- Content questions ("how does X work", "what was decided about Y") →
  `retrieve_from_knowledge_base` with the question as `prompt`
- Direction questions ("what's missing", "what next") →
  `generate_content_gaps`, then optionally `generate_research_questions`

### Learning loop (graph memory)

Past query outcomes are stored as a small InfraNodus memory graph so every
session gets smarter about THIS project. Memory context name:
`<prefix>-memory` (same prefix as the scopes, e.g. `repo-myproject-memory`);
record it in `infranodus/manifest.json` under a top-level `"memoryGraph"` key
the first time you create it.

**Recall — at the START of query mode:** if the manifest has `memoryGraph`,
call `memory_get_relations` with `memoryContextName` (add `entity:
"[[<concept>]]"` when the question names one) and fold any returned lessons
into how you answer — e.g. which scope answered this topic before, or a
correction the user made.

**Store — AFTER answering, sparingly.** Save a lesson only when it is
non-obvious and reusable: which scope/graph turned out to answer a topic, a
user correction, a dead end ("X is not covered by any scope"). Do NOT log
routine successful answers. Call `memory_add_relations` with one statement
per lesson, entities in `[[wikilinks]]`, outcome as a hashtag:

```
[[caching]] questions answered best by [[repo-myproject-history]] scope #useful
[[auth flow]] not covered by any scope — docs gap #dead-end
user corrected: [[session tokens]] rotate weekly not daily #corrected
```

These statements form a graph themselves — recurring `#dead-end` entities
cluster into visible documentation gaps over time.

## Conventions

- **Shared wikilink namespace:** file paths appear verbatim as
  `[[src/auth/service.py]]` in every scope — identical strings are the join
  keys that let multi-context and merged views stitch scopes together. Never
  paraphrase a path.
- **Separate graphs per scope** by default; merged view on demand via
  `merged_graph_from_texts` over the scope files, cross-scope comparison via
  `generate_difference_graph_from_text` (e.g. docs scope vs history scope =
  "what's discussed but never documented").
- **Obsidian:** the scope files are plain md with wikilinks — copy (or
  generate) them into a vault and the InfraNodus Obsidian plugin renders them
  in "[[Wiki Links]] and Concepts" mode.
- In an llm-wiki project (wiki CLAUDE.md schema present), this workflow
  complements the curated ontologies: same `infranodus/` folder, same
  manifest; only `generated: true` files are ever overwritten.
