# Phase 8: ACQUIRE and Phase 9: PROCESS

## Phase 8: ACQUIRE — Get Sources Into `raw/`

**This phase is re-runnable.** It handles **getting material onto disk** — copying files from the user's hard drive, fetching from URLs, transcribing YouTube, importing from reference managers — and landing everything in the correct typed subfolder under `raw/`.

**Phase 8 does NOT touch `wiki/`.** Turning `raw/` content into wiki pages is a separate operation — see Phase 9 (PROCESS). Keep them separate because:

- Acquisition and processing use totally different tools (file ops / web fetch / converters vs. pure LLM summarization)
- They fail in different ways and often happen on different cadences (e.g. dump 30 PDFs today, process over the week)
- The user may want to re-convert a source without re-running the wiki update, or bulk-import without immediately processing
- Skipping directly to Phase 9 is common when `raw/` already has unprocessed material

### Detecting the mode

```bash
SOURCES_COUNT=$(find wiki/sources -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
RAW_COUNT=$(find raw -type f \( -name '*.md' -o -name '*.txt' \) 2>/dev/null | wc -l | tr -d ' ')
echo "raw/ files: $RAW_COUNT | wiki/sources/: $SOURCES_COUNT"
```

- `SOURCES_COUNT == 0` → **first run** — acquire ONE source as a test drive (8.A below)
- `SOURCES_COUNT > 0` → **ongoing** — offer bulk acquisition (8.B below)

If the user just wants to process existing `raw/` content and skip acquisition entirely, jump directly to Phase 9.

### Phase 8.A — First Run (single-source test drive)

Walk the user through acquiring one source to validate the flow. Ask:

> "Do you already have a source you want to pull in (file on disk or URL), or should I fetch a relevant one from the web as a demo?"

**If they have a source on their hard drive:**

1. Ask for the path (or ask them to drop the file into the project folder)
2. Ask which `raw/` subfolder it belongs in by TYPE (`raw/notes/`, `raw/papers/`, `raw/youtube/`, etc.) — create the subfolder on the fly if missing. Organize by source TYPE, not topic.
3. **If it's a PDF, convert to markdown first** (`marker`, `pdftotext`, MarkItDown, Zotero markdown export) and land the `.md` in the typed subfolder. Keep the original PDF in `raw/assets/`.
4. If it's a YouTube or web URL, fetch + transcribe (InfraNodus `analyze_text` with url arg, yt-dlp + Whisper, Obsidian Web Clipper, or `WebFetch`)
5. Confirm the landing path with the user

Then hand off to **Phase 9 (PROCESS)** to turn it into wiki pages.

**If they don't have a source yet:**

- Offer to fetch a relevant web article via `WebSearch` / `WebFetch` based on the wiki's topic
- Offer to fetch a YouTube video they provide a URL for
- Walk through the capture-channel table in 8.B so they know what's possible

### Phase 8.B — Ongoing Acquisition (re-runnable)

When the user says "import new sources", "pull these in", "here's a folder of papers", or the wiki exists and `raw/` needs refreshing, use this mode.

#### Step 8.B.1 — Where is the material?

Ask with `AskUserQuestion` — the user picks one or more acquisition channels:

- **A) Point me at a folder on my disk** — user gives a path (e.g. `~/Zotero/storage`, `~/Documents/notes`, `~/Downloads/papers`). The LLM walks the folder, copies / converts what's there, drops into typed subfolders.
- **B) I'll paste a list of URLs** — web articles, YouTube videos, arXiv links, Google Patents, etc. The LLM fetches / transcribes each.
- **C) Import from a reference manager** — Zotero, Readwise, Obsidian vault export, Notion export. The LLM parses and places per-item.
- **D) Search for new sources** — given a gap or topic from Phase 10 priorities, the LLM uses `WebSearch` / InfraNodus `analyze_google_search_results` to propose candidates before fetching.
- **E) I'll drop files manually** — user dumps into `raw/` themselves; the LLM just organizes, converts, and reports.

#### Step 8.B.2 — Acquire, convert, place

For each incoming item:

1. **Determine source type** → maps to the right `raw/` subfolder (see table below)
2. **Convert if needed:**
   - PDF → markdown (`marker`, `pdftotext`, MarkItDown)
   - YouTube URL → transcript markdown (InfraNodus url arg, yt-dlp + Whisper)
   - Web URL → article markdown (Obsidian Web Clipper, InfraNodus fetch, `WebFetch`)
   - `.docx` / `.epub` / `.html` → markdown (`pandoc`, `readability`)
3. **Place** in the typed subfolder (create on the fly if missing)
4. **Preserve originals** in `raw/assets/` when the conversion is lossy (PDFs, ebooks)

Report a summary: how many files acquired, which subfolders, which failed to convert and why.

#### Capture channels by source type

| Source type                           | Where it comes from                     | Acquisition method                                        | Target subfolder                     |
| ------------------------------------- | --------------------------------------- | --------------------------------------------------------- | ------------------------------------ |
| Personal notes, journal, voice memos  | Hard drive, Obsidian vault, voice-memo app | Copy `.md` / Whisper transcribe                        | `raw/notes/`                         |
| Academic papers (PDFs)                | Zotero, hard drive, arXiv URL           | **Convert PDF → markdown** (`marker`, `pdftotext`, MarkItDown) | `raw/papers/`                   |
| YouTube videos / podcasts             | URL                                     | InfraNodus url arg auto-transcribes, or yt-dlp + Whisper  | `raw/youtube/`                       |
| Web articles, blog posts              | URL                                     | Obsidian Web Clipper, InfraNodus fetch, `WebFetch`        | `raw/articles/`                      |
| Google search results (SERPs)         | Live query                              | InfraNodus `analyze_google_search_results` export         | `raw/search-results/`                |
| Patents                               | Google Patents URL or PDF               | PDF → markdown                                            | `raw/patents/`                       |
| Books                                 | EPUB / PDF per chapter                  | Per-chapter conversion → markdown                         | `raw/books/`                         |
| Interviews, meetings                  | Audio files, existing transcripts       | Whisper / Otter / existing `.vtt` → markdown              | `raw/interviews/` or `raw/meetings/` |
| Email threads, Slack exports          | Provider export                         | Parse → markdown                                          | `raw/communications/`                |

**Create new subfolders on the fly** — don't ask permission for every new category. `raw/` is designed to grow new types as the project matures.

#### Step 8.B.3 — Hand off to Phase 9

After acquisition report:

> "X sources acquired into `raw/` across {subfolders}. Run **Phase 9 (PROCESS)** to turn them into wiki pages, or I can continue straight into processing now."

On confirmation, proceed to Phase 9.

---

## Phase 9: PROCESS — Ingest `raw/` → `wiki/`

**This phase is re-runnable.** It reads unprocessed files in `raw/` and produces / updates wiki pages according to the schema. **No file acquisition happens here** — if `raw/` is empty or stale, go back to Phase 8 first.

When the user says "ingest", "process raw/", "update the wiki", or re-invokes the skill and `raw/` has new material, **jump directly here**. Do NOT re-run DISCOVER / SCOPE / STRUCTURE / SCHEMA / SCAFFOLD — the wiki already exists.

### Step 9.1 — Confirmation prompt (use this wording verbatim)

Present this to the user every time, so the operation is predictable and they never need to type the instruction themselves:

> **Process `raw/` → `wiki/` — I'll ingest everything in `raw/` that doesn't yet have a matching `wiki/sources/*.md` page.**
>
> For each new source I'll: (1) read it, (2) create the source summary in `wiki/sources/`, (3) update or create relevant system / concept / connection / question pages, (4) update `wiki/index.md` and append to `wiki/log.md`, (5) flag any contradictions with existing wiki content.
>
> After the batch I'll refresh the ontologies in `infranodus/` (**append-only, never regenerated**) and re-run the InfraNodus knowledge-graph analysis into `output/`.
>
> Scope options:
>
> - **A)** Everything in `raw/` (default)
> - **B)** A specific subfolder only (e.g. just `raw/papers/`)
> - **C)** A specific file
>
> Proceed with A, or tell me B/C?

Wait for user confirmation. If they pick B or C, narrow the inventory accordingly.

### Step 9.2 — Inventory unprocessed sources

```bash
# For each file in raw/ (recursive), check whether a matching wiki/sources/<slug>.md exists.
# The slug is derived from the file stem (kebab-case).
find raw -type f \( -name '*.md' -o -name '*.txt' \) | while read -r f; do
  stem=$(basename "$f" | sed 's/\.[^.]*$//')
  if [ ! -f "wiki/sources/$stem.md" ]; then
    echo "UNPROCESSED: $f"
  fi
done
```

Report the count and list to the user before proceeding. If the list is long (>10), ask whether to process all in one batch or cap at N.

### Step 9.3 — Process each source

For every unprocessed file, follow the ingest workflow defined in the schema (typically: source summary → system/concept/connection updates → question pages → index → log → contradiction flags). Report one-line progress after each: `[3/12] processed raw/papers/hausdorff-1996.md → wiki/sources/hausdorff-1996.md (+2 concepts, +1 connection)`.

### Step 9.4 — Refresh ontologies and graph analyses

After the batch (not per-file):

1. For each wiki folder touched (systems/, concepts/, connections/, sources/, questions/), **append** new relations to `infranodus/<folder>-ontology.md` using the `ontology-generator` skill. **Never regenerate from scratch** — read the existing file first, then add only lines covering genuinely new content. Match existing format exactly. (This rule applies to CURATED ontologies only — files with `generated: true` frontmatter belong to their generator script and are never appended to; see knowledge-graphs.md.)
2. Sync the appends to the saved graphs: `python3 <this skill's dir>/scripts/upload_wiki_ontology.py .` — uploads ONLY the new lines of every curated scope (statements append server-side), and fully uploads + registers any ontology that has no saved graph yet, recording `graphName` + `url` in the manifest.
3. Overwrite `output/<folder>-knowledge-graph-analysis.md` with a fresh analysis of the saved graph (`analyze_existing_graph_by_name` + `generate_content_gaps` on its `graphName`)
4. If the project also has generated scopes (vault link scan, repo rationale — check the manifest), refresh them by re-invoking the `infranodus` skill (Skill tool) rather than editing the files.

### Step 9.5 — Iterate on the schema (first-run only)

If this is the very first processing run, flag any adjustments needed to `CLAUDE.md` / `AGENTS.md`:

- Page format tweaks
- Frontmatter field changes
- Cross-referencing rules that need refining
- Workflow steps to add or remove

Update the schema before the next batch to lock in improvements. This starts the co-evolution process — the schema keeps improving with use.

### Step 9.6 — Summarize

Close the batch with:

- How many sources processed, by subfolder
- Which wiki sections grew (and by how much)
- Which gaps closed, which new gaps opened (from the InfraNodus analysis diff)
- Suggest **Phase 10 (PLAN)** if ≥10 new sources came in or if gaps shifted meaningfully

---

### Handoff (after Phase 8 and/or Phase 9)

- Summarize what was acquired / processed and what changed in the wiki
- Quick reference for the four core operations: **acquire** (Phase 8), **process** (Phase 9), **query**, **lint**
- Reminder that the schema is a living document — update it whenever a better convention emerges
- Suggest running **Phase 10 (PLAN)** once ≥10 sources exist OR after a batch that meaningfully shifted gaps
