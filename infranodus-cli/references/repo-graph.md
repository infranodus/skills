# Repo / Vault Graphs — the /infranodus folder workflow

Build a knowledge graph of the current repo or Obsidian vault, save it to
InfraNodus, and write a report. Deterministic collection (no LLM),
server-side graph computation. Division of labor:

- **Uploads** (bulk writes): `scripts/upload_scopes.py` talks to the MCP
  server itself over HTTP. It discovers its credential on its own —
  `INFRANODUS_API_KEY` env var, else the key of an already-configured local
  `infranodus` MCP server entry (`.mcp.json`, `~/.claude.json`, …) — so a
  locally-installed MCP server needs no extra setup. The agent never
  carries scope-file contents through its own context.
- **Queries** (reads): the session's native InfraNodus MCP tools
  (`mcp__infranodus__<tool>` or the connector's equivalents).

Before an upload, `upload_scopes.py --check-auth` verifies a credential
exists and works. If it finds none (env unset and no local MCP entry — a
cloud OAuth connector holds its token remotely), AskUserQuestion once:
**A)** paste an API key (infranodus.com → settings → API access —
recommended), **B)** skip upload — keep the local scope files only (they
still render in Obsidian).

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

## Step 1 — Scope (default: full scan, no questions)

If the user named a target ("graph the docs folder", "analyze notes
mentioning trading"), map it straight to flags: `--include <path>`
(repeatable), `--term <word>` (repeatable, any-of), `--vault` (link
structure only). Filtered scans write suffixed scope files and graphs that
never clobber the full scan.

Otherwise run the full scan without asking. Only when a quick inventory
shows the corpus is very large (roughly >500 candidate files or >2 MB of
docs/md) ask ONE AskUserQuestion: full scan anyway, or narrow to one of the
3–4 biggest top-level folders (listed as options, plus Other for a path or
terms).

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
link scopes — only `[[page]]` wikilinks become nodes). Files carry
`generated: true` → they are regenerated, never hand-edited (curated
ontologies from the llm-wiki skill lack that flag and stay append-only).
Likely-secret files (`.env*`, keys, anything named credential/secret/apikey)
are never mined. The script also creates/updates `infranodus/manifest.json`.

## Step 3 — Upload (one graph per scope)

```bash
python3 <SKILL_DIR>/scripts/upload_scopes.py .            # long-running: use run_in_background
python3 <SKILL_DIR>/scripts/upload_scopes.py . --prefix repo-myproject
python3 <SKILL_DIR>/scripts/upload_scopes.py . --force    # re-upload (APPENDS — see below)
```

Do NOT hand-roll `create_knowledge_graph` loops over scope files — the API
rejects payloads over ~100 KB (413) and rate-limits bursts (429); the
script chunks on heading-aware line boundaries, paces calls 20 s apart,
backs off 5 min on 429s, bisects on 413s, uploads all chunks of a scope
under ONE `graphName` (`repo-<project>-<scope>` / `vault-<project>-<scope>`),
sets `maxNodes: 500` and the scope's declared `wikilinksMode` (these bind
when the graph is FIRST created), and records `graphName` + `url` back into
the manifest — which is what enables the Step 0 fast path next session.

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

## Step 5 — Report

Write `infranodus/INFRANODUS_REPORT.md` (alongside the manifest and scope
files, not the project root) from the upload responses — no extra analysis
calls; the response already contains everything:

```markdown
# InfraNodus Report — <project>
Graphs: <scope>: <graphName> (<url>) …  |  Built: <date>

## Structure             <- modularity + diversity_stats in plain language
## Main topics           <- mainTopicalClusters
## Most influential      <- topInfluentialNodes (betweenness)
## Gateways              <- conceptualGateways (bridges between clusters)
## Gaps / what's missing <- contentGaps — for a repo: rationale clusters
                            that never touch; candidate docs/refactors
## Per-cluster graphs    <- knowledgeGraphByCluster (DOT, in <details>)
```

Print the graph URL(s) at the end — they open in the browser, the
InfraNodus VSCode/Cursor extension, and the Obsidian plugin.

## Query mode (after a graph exists)

- Structure questions ("main themes", "how organized") →
  `analyze_existing_graph_by_name`
- Content questions ("how does X work", "what was decided about Y") →
  `retrieve_from_knowledge_base` with the question as `prompt`
- Direction questions ("what's missing", "what next") →
  `generate_content_gaps`, then optionally `generate_research_questions`

## Conventions

- **Shared wikilink namespace:** file paths appear verbatim as
  `[[src/auth/service.py]]` in every scope — identical strings are the join
  keys that let merged and difference views stitch scopes together. Never
  paraphrase a path.
- **Separate graphs per scope** by default; merged view on demand via
  `merged_graph_from_texts` over the scope files; cross-scope comparison
  via `difference_between_texts` (e.g. docs vs history = "discussed but
  never documented").
- **Obsidian:** the scope files are plain md with wikilinks — copied into a
  vault, the InfraNodus Obsidian plugin renders them in "[[Wiki Links]] and
  Concepts" mode.
- In an llm-wiki project (wiki CLAUDE.md schema present), this workflow
  complements the curated ontologies: same `infranodus/` folder, same
  manifest; only `generated: true` files are ever overwritten.
