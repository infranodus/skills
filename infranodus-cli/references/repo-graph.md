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

## Step 1 — Detect (deterministic, no questions)

- `.obsidian/` directory present, or md files dominate → **vault**
- code-file majority / `.git` + package manifests → **repo**
- both → run both pipelines (separate scopes, one manifest)

## Step 2 — Extract

Run the bundled script (stdlib-only Python 3, no dependencies):

```bash
python3 <SKILL_DIR>/scripts/repo2statements.py .            # repo mode
python3 <SKILL_DIR>/scripts/repo2statements.py . --vault    # vault mode
```

Repo mode mines the natural-language layer (code-structure extraction is
deferred — do not attempt it by reading source files yourself):
- `repo-docs-ontology.md` — md/rst/txt paragraphs, prefixed `[[<filepath>]]:`
- `repo-code-rationale-ontology.md` — docstrings + `WHY:`/`NOTE:`/`TODO:`/
  `HACK:`/`FIXME:` comments, tagged `#docstring` / `#why` / `#note` / …
- `repo-history-ontology.md` — commit-message bodies (`#commit`), PR
  descriptions (`#pr`), issue threads (`#issue`) via `git` and `gh`

Vault mode emits `vault-links-ontology.md` — `[[Page A]] links to [[Page B]]`
per page connection.

The script also creates/updates `infranodus/manifest.json` (the scope
registry). Files carry `generated: true` frontmatter → they are regenerated,
never hand-edited or appended to (curated ontologies from the llm-wiki skill
lack that flag and stay append-only).

## Step 3 — Upload (one graph per scope)

For each scope file the script reported, upload with a graphName of
`repo-<project>-<scope>` or `vault-<project>-<scope>` (lowercase, dashes):

```bash
ARGS=$(python3 - <<'EOF'
import json, re
raw = open('infranodus/repo-docs-ontology.md', encoding='utf-8').read()
text = re.sub(r'^---.*?---\s*', '', raw, flags=re.S)   # strip frontmatter
print(json.dumps({"graphName": "repo-myproject-docs", "text": text}))
EOF
)
mcporter call infranodus.create_knowledge_graph --args "$ARGS"
```

- Large scope file (> ~200 KB)? Split by lines into several calls with the
  SAME `graphName` — statements accumulate in one context.
- Then record results in the manifest (fill `graphName` and `url` for that
  scope from the tool response) — this is what enables Step 0 next session.
- Fetch the full graph once for local storage and traversal:

```bash
mcporter call infranodus.create_knowledge_graph --args '{"graphName": "repo-myproject-docs", "text": "", "includeGraph": true, "addNodesAndEdges": true}' 2>/dev/null \
  || mcporter call infranodus.analyze_existing_graph_by_name --args '{"graphName": "repo-myproject-docs", "includeGraph": true}'
```

Save the returned nodes/edges JSON as `infranodus/<scope>-graph.json`.

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
