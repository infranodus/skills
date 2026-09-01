# Knowledge Graphs and Ontology Policy

All ontology/knowledge-graph files are stored in a single `infranodus/` folder at the project root (sibling of `wiki/`, `raw/`, etc.). This folder has no subfolders — all graph files live flat in `infranodus/`. This is a core part of the wiki workflow — not optional.

## The scope registry: `infranodus/manifest.json`

`infranodus/manifest.json` is the shared registry of every graph artifact in the project (used by this skill AND the `infranodus` skill's repo/vault workflow). Each entry maps a local file to its saved InfraNodus graph: `{"scopes": {"<file>": {"file", "policy", "graphName", "url", "updated", ...}}}`. Create it if missing; update the entry whenever an ontology is (re)uploaded. A future session that finds the manifest can query the saved graphs directly (`analyze_existing_graph_by_name`, `retrieve_from_knowledge_base`) instead of re-analyzing.

## Two file policies: curated vs generated

Files in `infranodus/` carry a policy, declared in YAML frontmatter and mirrored in the manifest:

- **Curated** (no flag, or `curated: true`) — the ontologies this skill maintains via ontology-generator. Append-only, never regenerated (see CRITICAL below).
- **Generated** (`generated: true` + `generator:` in frontmatter) — machine-derived files written by their generator (e.g. the `infranodus` skill's repo/vault scans). These are regenerated wholesale by their generator; do NOT append to them, hand-edit them, or apply the append-only rule to them. Their statements are grouped under `## [[page]]` section headings (the parent-page contract of the `parentAndConcepts`/`obsidianStyle` wikilinksMode) — the headings are structure, not relations; never mistake them for ontology lines.

Every file should also declare its processing mode in frontmatter — `wikilinksMode: wikilinksOnly` for curated ontologies (add it when creating a new ontology file), `parentAndConcepts`/`wikilinksOnly` in generated scopes (written by their generator). Uploaders honor this declaration, so a file processed separately through the MCP tools still gets the right mode.

**Always check the frontmatter before updating any file in `infranodus/`.**

## Ontology Generation Workflow

1. **When to generate**: After creating or significantly updating pages in any wiki folder (systems/, concepts/, connections/, sources/, questions/, etc.)

2. **How to generate**: Use the `ontology-generator` skill (invoke via `/ontology-generator` or the Skill tool) to generate an ontology from the content of all files in that folder. The ontology must use `[[wikilinks]]` syntax with `[relationCode]` tags as specified by the skill.

3. **What to feed**: Read all `.md` files in the folder, combine their content (stripping YAML frontmatter), and pass the combined text to the ontology-generator skill. The skill will extract entities and relationships in `[[wikilinks]]` format.

4. **Where to save**: Save the generated ontology as `<folder-name>-ontology.md` inside the `infranodus/` folder at the project root, with frontmatter declaring `curated: true` and `wikilinksMode: wikilinksOnly`. For example:
   - `infranodus/systems-ontology.md`
   - `infranodus/concepts-ontology.md`
   - `infranodus/connections-ontology.md`
   - `infranodus/sources-ontology.md`
   - `infranodus/full-wiki-ontology.md` (for the whole wiki combined)

## CRITICAL: Incremental Updates, Never Full Rewrites

**NEVER regenerate ontology files from scratch.** Ontology files are curated artifacts that accumulate human-reviewed knowledge over time. They contain specific phrasings, relationship nuances, and domain-specific insights that cannot be automatically reconstructed from source pages alone.

### Adding new relations

When updating ontologies after new sources are ingested:

- **READ the existing ontology file FIRST** — understand its format, style, and content
- **APPEND new lines at the end** — add only lines covering genuinely new content from the new sources
- **Match the existing format exactly** — same casing conventions, same `[relationCode]` tag style, same entity naming patterns
- **If delegating to sub-agents**: include the existing file content (or its path) in the prompt, explicitly instruct "READ FIRST, then APPEND ONLY, do not rewrite", and verify the diff afterward

### Removing or modifying existing relations

Removal and modification of existing lines IS allowed when there is a clear reason:

- **Factually wrong**: A relation contradicts the current wiki content (e.g., a source was reinterpreted, a claim was debunked by newer evidence)
- **Superseded**: A newer, more precise relation replaces a vague or incomplete one — remove the old line and add the improved version
- **Duplicate**: Two lines say the same thing with slightly different wording — keep the better one
- **Stale**: A relation references content that was removed from the wiki (e.g., a source was deleted, a concept was merged into another)

When removing or modifying, briefly note the reason in the commit message or log so the change is traceable.

**What is NOT allowed**: wholesale regeneration that replaces all lines with freshly generated content. The default operation is always append. Removal is a deliberate, line-by-line editorial decision.

### Why this matters

A full rewrite loses:

- Relationship type tags (`[isA]`, `[causes]`, etc.) that carry semantic meaning
- Specific nuanced phrasings (e.g., "[[choreographed routine]] is still [[periodic]] even on complex terrain")
- Entity casing and naming conventions established by the ontology-generator skill
- Content that came from personal observations not derivable from wiki pages alone

5. **Upload to InfraNodus**: After generating or appending to an ontology, upload it with the bundled uploader — never by passing file contents through `create_knowledge_graph` calls in the agent context (the API rejects payloads over ~100 KB with 413 and rate-limits bursts with 429; the script chunks, paces, backs off, and bisects):

   ```bash
   # first-time upload of a new ontology file (registers it in the manifest):
   python3 <this skill's dir>/scripts/upload_wiki_ontology.py . --file infranodus/<folder-name>-ontology.md
   # after appending relations — syncs ONLY the new lines of every curated scope:
   python3 <this skill's dir>/scripts/upload_wiki_ontology.py .
   ```

   The script is stdlib-only and ships with this skill. It names graphs `wiki-<project>-<scope>` (the `wiki-*` namespace belongs to this skill; `repo-*`/`vault-*` belong to the `infranodus` skill's scanner), honors the file's frontmatter `wikilinksMode` (default `wikilinksOnly`), records `graphName` + `url` + `updated` in `infranodus/manifest.json`, and tracks how much of each file has been uploaded so re-runs append only the new lines (server-side uploads to an existing graphName APPEND — exactly right for append-only ontologies). It only ever touches `policy: "curated"` scopes. If already-uploaded lines were edited or removed (a deliberate editorial change), it refuses to append: delete the graph in InfraNodus first, then re-run with `--rebuild`. Verify credentials once with `--check-auth` (uses `INFRANODUS_API_KEY` or a local `infranodus` MCP server entry). The saved graph is then queryable across sessions (`retrieve_from_knowledge_base` for content questions, `generate_content_gaps` for planning) and viewable in the browser, Cursor/VSCode extension, and 3D view.

6. **Save analysis results**: After the upload, run the analysis on the saved graph (`analyze_existing_graph_by_name` with the `graphName` from the manifest; `generate_content_gaps` for the gaps) and save the output to the `output/` folder as `<folder-name>-knowledge-graph-analysis.md`. Include:
   - Graph statistics (nodes, edges, modularity, diversity)
   - Topical clusters with their influence percentages
   - Content gaps between clusters
   - Key concepts and gateway nodes
   - Recommendations for improving coverage

7. **Act on gaps**: Use the identified content gaps to create new question pages, suggest missing sources, or flag areas where the wiki needs development.

If the `ontology-generator` skill is not available, ask the user to install it from [https://github.com/infranodus/skills](https://github.com/infranodus/skills).
