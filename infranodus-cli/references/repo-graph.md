# Repo / Vault Graphs — the /infranodus folder workflow

Build a knowledge graph of the current repo or Obsidian vault, save it to
InfraNodus, store everything locally, and write a report. Deterministic
collection (no LLM), server-side graph computation.

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
- `repo-docs-ontology.md` — md/rst/txt paragraphs, prefixed `[[<filepath>]]:`
- `repo-code-rationale-ontology.md` — docstrings + `WHY:`/`NOTE:`/`TODO:`/
  `HACK:`/`FIXME:` comments, tagged `#docstring` / `#why` / `#note` / …
- `repo-history-ontology.md` — commit-message bodies (`#commit`), PR
  descriptions (`#pr`), issue threads (`#issue`) via `git` and `gh`

The script auto-detects a vault (`.obsidian/` present, or md-dominated
folder). On a bare launch in a vault it ALSO runs the link scan
(`vault-links-ontology.md`) and switches doc-statement prefixes to Obsidian
page stems (`[[Page A]]:` instead of `[[notes/Page A.md]]:`) so the content
scope and the link scope share node names and stitch into one graph.

**`--vault` flag** = map the vault structure ONLY: just
`vault-links-ontology.md` with one `[[Page A]] links to [[Page B]]` statement
per page connection, no content mining.

The script also creates/updates `infranodus/manifest.json` (the scope
registry). Files carry `generated: true` frontmatter → they are regenerated,
never hand-edited or appended to (curated ontologies from the llm-wiki skill
lack that flag and stay append-only).

## Step 3 — Upload (one graph per scope)

Run the bundled uploader — do NOT hand-roll `mcporter call
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

Write `INFRANODUS_REPORT.md` in the project root from the upload responses —
no extra analysis calls; the response already contains everything:

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
