---
name: llm-wiki
description: >
  Guide users through setting up a personal LLM-maintained wiki — a persistent, compounding knowledge base where the LLM incrementally builds and maintains interlinked markdown pages from raw sources. Use this skill when the user wants to: set up a personal knowledge base, create a research wiki, organize notes with LLM help, build a "second brain", set up an Obsidian + LLM workflow, create a persistent knowledge graph from documents, or mentions "LLM wiki". This skill asks questions to understand the user's domain and goals, then scaffolds the entire wiki structure, schema, and workflows tailored to their needs.
allowed-tools:
  - Read
  - Write
  - Grep
  - Glob
  - AskUserQuestion
  - Bash
  - MCPorter
---

# LLM Wiki Setup Assistant

A guided, multi-phase workflow for designing and scaffolding a personal LLM-maintained wiki. The core idea: instead of re-deriving knowledge from raw documents on every query (like RAG), the LLM incrementally builds a persistent wiki — extracting, cross-referencing, and synthesizing knowledge once, then keeping it current as new sources arrive. The wiki compounds over time. The human curates sources and asks questions; the LLM does all the bookkeeping.

## Preamble (run first)

```
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
echo "BRANCH: $_BRANCH"
```

## Architecture (for context)

Every LLM Wiki has three layers:

1. **Raw sources** — immutable collection of source documents (articles, papers, transcripts, images). The LLM reads but never modifies these. You need to understand from the user what the scope of the raw sources is for a particular project.
2. **The wiki** — LLM-generated markdown files (summaries, entity pages, concept pages, comparisons, synthesis). The LLM owns this layer entirely. You create the `/wiki` folder (or user-defined) in the project's folder for that (if it doesn't exist yet).
3. **The output** — This is where you store the output of your interactions with user for a particular project - you create it in the `/output` folder of the project (or user-defined) if it doesn't exist yet.
4. **The schema** — a configuration document (CLAUDE.md for Claude and AGENTS.md for Codex) that tells the LLMs how the wiki is structured, what conventions to follow, and what workflows to use. Co-evolved by user and LLM over time. Create both files so the folder is compatible with most LLMs.

## Phase Overview

```
1. DISCOVER    -> What domain? What's the goal? What sources?
2. SCOPE       -> How big? How deep? What outputs matter?
3. STRUCTURE   -> Directory layout, page types, naming conventions - see architecture above
4. SCHEMA      -> Write the CLAUDE.md and AGENTS.md of the local folder where the skill is invoked for configuration
5. WORKFLOWS   -> Define ingest, query, and lint operations
6. TOOLING     -> Obsidian plugins, InfraNodus tools for gap analysis, research, and text optimization, CLI tools, search, git
7. SCAFFOLD    -> Create the directory structure and starter files
8. FIRST RUN   -> Ingest the first source together as a test drive
```

---

## Phase 1: DISCOVER — What Are You Building This For?

Start by understanding the user's domain and motivation. Ask conversationally — 2-3 questions max per message using the AskUserQuestion tool.

### Core Questions

- **What domain or topic is this wiki for?** Get specific. Not just "research" but "competitive analysis of AI coding tools" or "tracking my health and psychology over time" or "reading notes for a political philosophy course."

- **What kinds of sources will you be feeding it?** Examples:
  - Academic papers (PDFs, arXiv links)
  - Web articles and blog posts
  - YouTube videos / podcast transcripts
  - Meeting notes / Slack threads
  - Books (chapter by chapter)
  - Journal entries / personal notes
  - Data files (CSVs, JSON)
  - Images, screenshots, diagrams

- **What's your end goal?** What does success look like?
  - "I want to deeply understand topic X and develop an original thesis"
  - "I want a living reference I can query months from now"
  - "I want to track how my understanding evolves over time"
  - "I want to produce a report / paper / presentation at the end"
  - "I want a structured record of everything I've read on this topic"

- **Are you starting fresh or do you already have sources?** If they have existing material, understand the volume and format.

- **Who else will use this?** Just the user, or a team? This affects structure and access conventions.

### Contextual Probes

Based on the domain, ask domain-specific questions using the AskUserQuestion tool:

- **Personal/self-improvement**: What aspects are you tracking? (health, goals, psychology, habits, relationships) Do you journal regularly? What format?
- **Research**: What's your current level of expertise? Are you exploring broadly or going deep on a specific question? Is there a deadline?
- **Book reading**: One book or a reading list? Fiction or non-fiction? What do you want to get out of it?
- **Business/team**: What's the knowledge problem you're solving? Who generates the sources? Who consumes the wiki?
- **Course/learning**: What course? What's the structure? Lectures, readings, problem sets?

Don't overwhelm. Gather enough to move to Phase 2. You can refine as you go.

---

## Phase 2: SCOPE — How Big and How Deep?

Now calibrate the wiki's scale and depth. This determines how much structure to build.

### Scale Assessment

Ask the user to estimate:

- **Source volume**: How many sources do you expect to add? (5-10? 50-100? 500+?)
- **Timeframe**: Over what period? (one weekend sprint? months of ongoing work?)
- **Session frequency**: How often will you work with it? (daily? weekly? sporadic bursts?)

### Depth Assessment

- **Entity tracking**: Do you need pages for individual entities (people, organizations, products, concepts)? Or is topic-level granularity enough?
- **Chronological tracking**: Does time matter? (e.g., tracking how a company's strategy evolved, or how your health changed over months)
- **Contradictions and debates**: Is tracking disagreement between sources important? (critical for research, less so for course notes)
- **Quantitative data**: Will there be numbers, metrics, data to track? Or is it primarily qualitative?

### Output Needs

- **What formats will you want to extract from the wiki?**
  - Markdown pages (default — always)
  - Comparison tables
  - Slide decks (Marp)
  - Charts / visualizations
  - Structured data (YAML frontmatter, Dataview queries)
  - Exportable reports

### Tier Classification

Based on answers, classify the wiki into a tier (share this with the user):

| Tier       | Sources | Entities | Duration     | Example                                                           |
| ---------- | ------- | -------- | ------------ | ----------------------------------------------------------------- |
| **Light**  | 5-20    | Few/none | Days-weeks   | Reading a single book, trip planning                              |
| **Medium** | 20-100  | Dozens   | Weeks-months | Research project, course notes, competitive analysis              |
| **Heavy**  | 100+    | Hundreds | Months-years | Ongoing team wiki, long-term research program, personal life wiki |

The tier determines how much indexing infrastructure, how many page types, and how formal the schema needs to be.

---

## Phase 3: STRUCTURE — Design the Directory Layout

Based on Phases 1-2, propose a directory structure. Present it to the user and iterate.

### Base Template

Every wiki has at least:

```
wiki-name/
  raw/                    # Immutable source documents
    assets/               # Downloaded images, PDFs
  wiki/                   # LLM-generated pages (the wiki itself)
    index.md              # Content catalog — what's in the wiki
    log.md                # Chronological record of operations
    overview.md           # High-level synthesis of everything
  output/                 # Folder for output of the interactions
  CLAUDE.md               # Schema — instructions for the LLM
  AGENTS.md               # Schema - instructions for the LLM (Codex-compatible)
```

### Knowledge Graphs

All ontology/knowledge-graph files are stored in a single `.infranodus/` folder at the project root (sibling of `wiki/`, `raw/`, etc.). This folder has no subfolders — all graph files live flat in `.infranodus/`. This is a core part of the wiki workflow — not optional.

#### Ontology Generation Workflow

1. **When to generate**: After creating or significantly updating pages in any wiki folder (systems/, concepts/, connections/, sources/, questions/, etc.)

2. **How to generate**: Use the `ontology-creator` skill (invoke via `/ontology-creator` or the Skill tool) to generate an ontology from the content of all files in that folder. The ontology must use `[[wikilinks]]` syntax with `[relationCode]` tags as specified by the skill.

3. **What to feed**: Read all `.md` files in the folder, combine their content (stripping YAML frontmatter), and pass the combined text to the ontology-creator skill. The skill will extract entities and relationships in `[[wikilinks]]` format.

4. **Where to save**: Save the generated ontology as `<folder-name>-ontology.md` inside the `.infranodus/` folder at the project root. For example:
   - `.infranodus/systems-ontology.md`
   - `.infranodus/concepts-ontology.md`
   - `.infranodus/connections-ontology.md`
   - `.infranodus/sources-ontology.md`
   - `.infranodus/full-wiki-ontology.md` (for the whole wiki combined)

#### CRITICAL: Incremental Updates Only

**NEVER regenerate ontology files from scratch.** Ontology files are curated artifacts that accumulate human-reviewed knowledge over time. They contain specific phrasings, relationship nuances, and domain-specific insights that cannot be automatically reconstructed from source pages alone.

When updating ontologies after new sources are ingested:

- **READ the existing ontology file FIRST** — understand its format, style, and content
- **PRESERVE all existing lines** — do not modify, rephrase, reformat, or delete any existing content
- **APPEND new lines at the end** — add only lines covering genuinely new content from the new sources
- **Match the existing format exactly** — same casing conventions, same `[relationCode]` tag style, same entity naming patterns
- **If delegating to sub-agents**: include the existing file content (or its path) in the prompt, explicitly instruct "APPEND ONLY, do not rewrite", and verify the diff afterward

Violations of this rule destroy curated knowledge. A full rewrite loses:
- Relationship type tags (`[isA]`, `[causes]`, etc.) that carry semantic meaning
- Specific nuanced phrasings (e.g., "[[choreographed routine]] is still [[periodic]] even on complex terrain")
- Entity casing and naming conventions established by the ontology-creator skill
- Content that came from personal observations not derivable from wiki pages alone

5. **InfraNodus analysis**: After generating each ontology, feed it to InfraNodus using the `generate_knowledge_graph` tool with `modifyAnalyzedText: 'none'` (since entities are already marked with `[[wikilinks]]`). This returns cluster structure, content gaps, key concepts, and diversity metrics.

6. **Save analysis results**: Save the InfraNodus analysis output (clusters, gaps, key concepts, diversity score) to the `output/` folder as `<folder-name>-knowledge-graph-analysis.md`. Include:
   - Graph statistics (nodes, edges, modularity, diversity)
   - Topical clusters with their influence percentages
   - Content gaps between clusters
   - Key concepts and gateway nodes
   - Recommendations for improving coverage

7. **Act on gaps**: Use the identified content gaps to create new question pages, suggest missing sources, or flag areas where the wiki needs development.

If the `ontology-creator` skill is not available, ask the user to install it from [https://github.com/infranodus/skills](https://github.com/infranodus/skills).

### Page Types to Consider

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

### Naming Conventions

Propose and confirm with the user:

- **File naming**: kebab-case (`market-analysis.md`) vs other conventions
- **Wikilinks**: `[[page-name]]` style for cross-references (Obsidian-compatible)
- **Frontmatter**: What YAML fields? (title, date, tags, source_count, status)
- **Date format**: ISO 8601 (`2026-04-08`) recommended

### Present and Iterate

Show the proposed structure as a tree diagram. Ask:

- "Does this capture the categories you need?"
- "Any page types missing for your domain?"
- "Do you want to add/remove any directories?"

---

## Phase 4: SCHEMA — Write the Configuration Document

This is the most important phase. The schema (CLAUDE.md / AGENTS.md) is what turns a generic LLM into a disciplined wiki maintainer.

### Determine Which Schema File

- **Claude Code**: `CLAUDE.md`
- **OpenAI Codex**: `AGENTS.md`
- **Other agents**: Ask the user what their agent uses for system instructions

### Schema Sections to Include

Write the schema document with these sections, tailored to the user's domain:

#### 1. Project Overview

- One paragraph describing what this wiki is, what domain it covers, and its purpose.

#### 2. Directory Structure

- Document the agreed structure from Phase 3. Explain what goes where.

#### 3. Page Templates

- For each page type, provide a template with:
  - Required YAML frontmatter fields
  - Section structure (what headings to use)
  - Content guidelines (what to include, what level of detail)
  - Cross-referencing rules (when to create wikilinks)

#### 4. Ingest Workflow

- Step-by-step instructions for when a new source is added:
  1. Read the source
  2. Discuss key takeaways with the user (optional — based on user preference)
  3. Create a source summary page
  4. Update or create entity/concept pages
  5. Update the index
  6. Update the overview if the new source significantly changes the picture
  7. Append to the log
  8. Flag any contradictions with existing wiki content

#### 5. Query Workflow

- How to answer questions against the wiki:
  1. Read the index to find relevant pages
  2. Read the relevant pages
  3. Synthesize an answer with citations to wiki pages
  4. Optionally: file the answer as a new wiki page if it's valuable

#### 6. Lint Workflow

- Periodic health checks:
  - Find contradictions between pages
  - Find stale claims superseded by newer sources
  - Find orphan pages (no inbound links)
  - Find concepts mentioned but lacking their own page
  - Find missing cross-references
  - Suggest new questions to investigate
  - Suggest sources to look for

#### 7. Conventions

- Tone and voice (academic? casual? technical?)
- Citation style (inline links? footnotes? source page references?)
- How to handle uncertainty and contradictions
- When to create a new page vs update an existing one
- When to flag something for user review vs handle autonomously

### Present and Iterate

Show the user the draft schema. This is the document they'll live with, so get it right. Ask:

- "Does the ingest workflow match how you want to work? Some people prefer to stay involved at every step; others want to batch-ingest with minimal supervision."
- "Any conventions you want to add or change?"
- "How much autonomy should the LLM have? Should it create new entity pages automatically, or always ask first?"

---

## Phase 5: WORKFLOWS — Define the Operations

Flesh out the three core operations based on user preferences.

### Ingest Preferences

Ask with AskUserQuestion tool:

- **Interactive or batch?** "Do you want to discuss each source as it's ingested, or just tell me to process a batch and review the results?"
- **Depth of summaries**: "How detailed should source summaries be? A paragraph? A full page? Depends on the source?"
- **Auto-create entities?** "Should I automatically create pages for new entities I encounter, or ask you first?"
- **Image handling**: "Will your sources contain images? Should I download them locally?" (If yes, configure Obsidian's attachment folder)

### Query Preferences

Ask using the AskUserQuestion tool:

- **Filing answers**: "When you ask a question and get a good answer, should I automatically file it as a wiki page, ask first, or never?"
- **Output formats**: "Do you want answers as plain text, as new markdown pages, as tables, or should I ask each time?"
- **Citation style**: "How should I cite sources in answers? Link to the wiki summary page? Link to the original source? Both?"

### Lint Preferences

Ask using the AskUserQuestion:

- **Frequency**: "Should I suggest a lint pass after every N ingests? Or only when you ask?"
- **Scope**: "Should lint be comprehensive (check everything) or focused (only check recently changed pages)?"
- **Auto-fix**: "Should I fix minor issues (broken links, missing cross-refs) automatically, or list them for your review?"

### Document the Workflows

Add the agreed workflows to the schema document with enough detail that the LLM can follow them in future sessions without re-asking these questions.

---

## Phase 6: TOOLING — Set Up the Environment

Based on the user's setup, recommend and configure tools.

### Essential: File Viewer

- **Obsidian** (recommended): Markdown editor with graph view, wikilinks, and plugins.
  - Configure: Attachment folder path for images
  - Recommend plugins based on needs:
    - **Dataview**: If using YAML frontmatter for structured queries
    - **Marp Slides**: If generating presentations
    - **Graph View**: Built-in, but call attention to it for wiki navigation
    - **Obsidian Web Clipper**: Browser extension for capturing web articles as markdown
    - **InfraNodus AI Graph View**: Advanced knowledge graph visualization and analysis of the pages' content and connections between the pages

- **VS Code / other editor**: Works fine, just loses graph view and wikilink navigation.

- **InfraNodus**: Content gap analysis, insight generation, and knowledge graph analysis and optimization via the InfraNodus MCP server tools or via MCPorter as described at [https://infranodus.com/mcp/deploy-mcporter](https://infranodus.com/mcp/deploy-mcporter). Ask the user to set up an API key for InfraNodus and update the environment you're using to be able to access that key when needed without saving it to the conversation or wiki.

### Optional: Search

Assess search needs based on tier:

- **Light tier**: Index file is sufficient. No additional tooling needed.
- **Medium tier**: Index file works, but suggest they revisit if it gets slow. Mention `qmd` as an option.
- **Heavy tier**: Recommend setting up `qmd` or a similar local search tool from the start. Offer to help configure it.

### Optional: Version Control

- **Git**: Recommend initializing the wiki as a git repo. Free version history, branching, collaboration. Do it for the user if they agree.
- Offer to set up `.gitignore` (exclude `.obsidian/workspace.json` and other ephemeral Obsidian files).

### Optional: CLI Tools

For power users or heavy-tier wikis, offer to build simple helper scripts:

- Search script (grep/ripgrep wrapper for the wiki)
- Stats script (page count, word count, orphan detection)
- Ingest helper (moves a file to `raw/` and kicks off the ingest workflow)

Ask what the user already has installed and what they're comfortable with. Don't over-engineer the tooling for light-tier wikis.

---

## Phase 7: SCAFFOLD — Create the Directory Structure

Now build it. Create the agreed directory structure with starter files.

### Create directories and files:

1. **Directory tree** — create all agreed directories
2. **CLAUDE.md / AGENTS.md** — the schema document from Phase 4
3. **index.md** — empty index with the agreed format and section headers
4. **log.md** — initialized with a first entry: `## [YYYY-MM-DD] init | Wiki created`
5. **overview.md** — a placeholder noting the wiki's purpose and that it will be populated as sources are ingested
6. **Page templates** — optionally create example template files in a `_templates/` directory for reference
7. **.gitignore** — if git was chosen
8. **Initialize git repo** — if git was chosen

### Present the Result

Show the user the created structure. Walk through each file briefly. Ask:

- "Does this look right?"
- "Want to adjust anything before we do the first ingest?"

---

## Phase 8: FIRST RUN — Test Drive with a Real Source

The best way to validate the setup is to use it. Guide the user through their first ingest.

### If they have a source ready:

1. Ask them if they want to copy it to the `raw/` folder
2. Run the full ingest workflow as defined in the schema
3. Show them the results: the source summary, any entity/concept pages created, the updated index and log
4. Ask for feedback: "Is this the right level of detail? Too much? Too little? Want me to adjust the format?"

### If they don't have a source yet:

- Suggest they grab a web article related to their domain using Obsidian Web Clipper or by pasting a URL
- Offer to fetch a relevant article via web search as a demo source
- Walk through what the ingest would produce

### Iterate on the Schema

The first ingest almost always reveals adjustments needed:

- Page format tweaks
- Frontmatter field changes
- Cross-referencing rules that need refining
- Workflow steps to add or remove

Update the schema based on feedback. This is the beginning of the co-evolution process — the schema will keep improving with use.

### Handoff

Close with:

- A summary of what was built
- Quick reference for the three core operations (ingest, query, lint)
- Reminder that the schema is a living document — they should update it whenever they discover a better convention
- Encourage them to ingest a few more sources to build momentum

---

## Adaptation Rules

### For Personal / Journal Wikis

- Emphasize privacy and local-only storage
- Suggest lighter structure — fewer page types, less formal conventions
- Focus on the compounding benefit: "In 6 months you'll have a structured picture of patterns you can't see day-to-day"
- Consider chronological organization alongside topical

### For Academic Research

- Emphasize citation tracking, contradiction detection, and thesis development
- Suggest more formal page templates with methodology sections
- Recommend tracking evidence strength (how well-supported is each claim?)
- Consider a dedicated "open questions" page

### For Book Reading

- Structure around the book's own organization (parts, chapters)
- Entity pages for characters, places, themes
- A "threads" or "themes" section for tracking cross-chapter connections
- Consider a timeline page for complex narratives

### For Business / Team Use

- Emphasize access control and review workflows
- Suggest human-in-the-loop for sensitive updates
- Consider integrating with existing tools (Slack, meeting recorders)
- Focus on keeping the wiki current — staleness is the #1 failure mode for team wikis

### For Quick / Light Projects

- Compress phases 3-6. Use a minimal structure: `raw/`, `wiki/`, `CLAUDE.md`
- Skip tooling discussion — Obsidian or any markdown viewer is fine
- Get to the first ingest fast

### User Wants More Structure

- Expand page types, add more frontmatter fields, suggest Dataview queries
- Consider multiple index files (by topic, by date, by entity type)
- Suggest periodic "state of the wiki" synthesis pages

### User Wants Less Structure

- Pare down to essentials: source summaries, one flat wiki directory, minimal frontmatter
- Let structure emerge organically — start simple and add page types only when needed
- "You can always add structure later. You can't easily remove it."

---

## AskUserQuestion Format

**ALWAYS follow this structure for every AskUserQuestion call:**

1. **Re-ground:** State the project, the current branch (use the `_BRANCH` value printed by the preamble — NOT any branch from conversation history or gitStatus), and the current plan/task. (1-2 sentences)
2. **Simplify:** Explain the problem in plain English a smart 16-year-old could follow. No raw function names, no internal jargon, no implementation details. Use concrete examples and analogies. Say what it DOES, not what it's called.
3. **Recommend:** `RECOMMENDATION: Choose [X] because [one-line reason]` — always prefer the complete option over shortcuts (see Completeness Principle). Include `Completeness: X/10` for each option. Calibration: 10 = complete implementation (all edge cases, full coverage), 7 = covers happy path but skips some edges, 3 = shortcut that defers significant work. If both options are 8+, pick the higher; if one is ≤5, flag it.
4. **Options:** Lettered options: `A) ... B) ... C) ...` — when an option involves effort, show both scales: `(human: ~X / CC: ~Y)`

Assume the user hasn't looked at this window in 20 minutes and doesn't have the code open. If you'd need to read the source to understand your own explanation, it's too complex.

Per-skill instructions may add additional formatting rules on top of this baseline.

--

## Important Principles

Throughout all phases, keep these in mind:

1. **The user never writes the wiki.** The LLM writes and maintains all wiki pages. The user curates sources, asks questions, and directs the analysis.

2. **Start simple, add complexity as needed.** Don't build a heavy-tier structure for a light-tier project. The user can always add page types and conventions later.

3. **The schema is a living document.** It will evolve as the user discovers what works. Encourage experimentation.

4. **Knowledge should compound.** Good answers to questions should be filed back into the wiki. Explorations should become pages. The wiki should get richer with every interaction.

5. **The wiki replaces chat history.** Insights that emerge in conversation should be captured in the wiki, not lost when the chat window closes.

6. **Make it concrete.** Don't just describe what pages could look like — create actual examples during scaffolding so the user can see and react to real content.

7. **Obsidia (or a similar MD file viewer) is the IDE, the LLM is the programmer, the wiki is the codebase, InfraNodus is the researcher** Frame it this way to help the user understand the workflow.
