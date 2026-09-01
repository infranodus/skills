# Directory Structure Templates

## Base Template

Every wiki has at least:

```
wiki-name/
  raw/                    # Immutable source documents — organize by source TYPE
    notes/                # Personal notes, journal entries, voice-memo transcripts (.md)
    papers/               # Academic papers — PDFs CONVERTED to markdown before landing here
    youtube/              # YouTube / podcast transcripts (optional)
    articles/             # Web articles (e.g. from Obsidian Web Clipper) (optional)
    search-results/       # SERP / Google search data, InfraNodus exports (optional)
    patents/              # Patent filings — PDF converted to markdown (optional)
    books/                # One markdown file per chapter (optional)
    interviews/           # Interview or meeting transcripts (optional)
    assets/               # Downloaded images, original PDFs, binaries
  wiki/                   # LLM-generated pages (the wiki itself)
    index.md              # Content catalog — what's in the wiki
    log.md                # Chronological record of operations
    overview.md           # High-level synthesis of everything
  output/                 # Folder for output of the interactions
  todos/                  # Research priorities and actionable task lists
  CLAUDE.md               # Schema — instructions for the LLM
  AGENTS.md               # Schema - instructions for the LLM (Codex-compatible)
```

## Typed `raw/` subfolders

Organize `raw/` by source TYPE, not by topic — the LLM applies format-specific ingest rules (e.g. a YouTube transcript is summarized differently from an academic paper, a patent differently from a personal note). Standard subfolders: `raw/notes/` and `raw/papers/`. Add more as the user's source mix grows: `raw/youtube/`, `raw/articles/`, `raw/search-results/`, `raw/patents/`, `raw/books/`, `raw/interviews/`, `raw/meetings/`, etc. **Create new subfolders on the fly** — don't ask permission for every new type.

PDFs must be **converted to markdown before landing in `raw/papers/`** so the LLM can read them without burning context on PDF extraction each time. Suggest `marker`, `pdftotext`, MarkItDown, or a Zotero markdown export. The original PDF can live in `raw/assets/` for reference.

## Page Types to Consider

Propose page types based on the domain. Common ones:

| Page Type                 | When to Include                                     | Example                                             |
| ------------------------- | --------------------------------------------------- | --------------------------------------------------- |
| **Source summaries**      | Always                                              | `sources/article-name.md` — summary + key takeaways |
| **Entity pages**          | Medium+ tier, or when tracking people/orgs/products | `entities/company-name.md`                          |
| **Concept pages**         | When building conceptual understanding              | `concepts/market-efficiency.md`                     |
| **Comparison pages**      | When comparing things is core to the domain         | `comparisons/tool-a-vs-tool-b.md`                   |
| **Timeline pages**        | When chronology matters                             | `timelines/project-history.md`                      |
| **Question pages**        | Research-heavy wikis                                | `questions/why-did-x-happen.md`                     |
| **Thesis/argument pages** | When developing original analysis                   | `thesis/main-argument.md`                           |
| **Data pages**            | When tracking quantitative information              | `data/metrics-dashboard.md`                         |
| **Log entries**           | Always (append-only)                                | Entries in `log.md`                                 |
