# InfraNodus Skills

**Knowledge graph + gap finder for your notes, vault or agent memory: shows what's missing and what to write next.**

Give it a folder of notes, an Obsidian vault, an LLM wiki, a set of articles or a single text. It maps the main topics, shows how they connect, and turns the gaps between them into concrete prompts: what to research, link or write next. The graph comes from [InfraNodus](https://infranodus.com) text network analysis, so it is measured, not guessed: word co-occurrence and network metrics, with the default extraction of a folder running locally without an LLM. That is why the gaps can be checked.

Made for AI researchers, Obsidian and second-brain users, researchers and content publishers. You don't need a terminal to start.

## Get started without a terminal (Claude web / desktop)

1. **Connect InfraNodus.** In Claude, go to **Settings → Connectors**, add `https://mcp.infranodus.com` as a connector and sign in with your InfraNodus account (OAuth). Details: [infranodus.com/mcp](https://infranodus.com/mcp).
2. **Add the core skill.** Download [`infranodus.zip`](https://github.com/infranodus/skills/releases/latest/download/infranodus.zip) (latest release). In Claude, open **Settings → Capabilities**, turn on **Code execution and file creation**, then click **Upload Skill** in the Skills section and pick the zip. Other skills from this repo are on the same [Releases](https://github.com/infranodus/skills/releases) page as `<skill-name>.zip`.
3. **Ask for the gaps.** Paste a text, attach documents or give a URL: *"Use InfraNodus to show the main topics in these notes and the gaps between them, then suggest three questions I should write about next."*

Graphs of a whole folder, repo or vault (and keeping them up to date) need an agent that can read your files, such as Claude Code.

## Claude Code (one line)

```
/plugin marketplace add infranodus/skills
/plugin install infranodus@infranodus-skills
```

Then run `/mcp`, select InfraNodus and sign in once, open a project or vault folder and type `/infranodus`. Want every skill in this repo? `/plugin install infranodus-all@infranodus-skills`. Other routes (`npx skills`, `install.sh`, Cursor, OpenClaw, ChatGPT) are under [Installation](#installation-all-routes).

## The workflow: gaps at the centre

Every stage feeds back into the gap analysis, and every gap suggests the next piece of research or writing.

```
research -> ANALYZE TOPICS & GAPS -> collect / curate -> refine -> publish
   ^                 |                                               |
   +-----------------+------------ next gap / next question <--------+
```

| Stage | Skills | Example prompt |
|---|---|---|
| **Research** | `infranodus` | "Analyze this YouTube talk <url> with InfraNodus and turn its gaps into research questions." |
| **Analyze topics & gaps** (centre) | `infranodus`, `shifting-perspective` | "/infranodus - graph this vault and show me the main topic clusters and the content gaps between them." |
| **Collect / curate** | `llm-wiki`, `ontology-generator`, `project-learnings` | "Set up an LLM wiki for my research on sleep and memory, with raw sources and wiki pages in Obsidian." |
| **Refine** | `shifting-perspective`, `cognitive-variability` | "My draft feels one-sided. What perspectives are missing, and how do I develop them?" |
| **Publish** | `writing-assistant`, `seo-analysis` | "Do keyword research for 'knowledge graphs for note-taking' and show what people search for that nobody covers well." |

## Skills in this repo

**Core (start here)**

- **InfraNodus** (`infranodus`, the core skill and default) - The front door. Turns a folder, Obsidian vault, LLM wiki or code repo into knowledge graphs and tells you what's missing: topic clusters, content gaps, research questions, central concepts, GraphRAG retrieval over the saved graphs. Invoked inside a project (`/infranodus`), it mines docs, PDF text, docstrings, `WHY:`/`NOTE:` comments and commit/PR/issue history deterministically (stdlib Python, no LLM), and keeps the graphs current: `repo2statements.py --detect` lists the files that changed since the last build, `--update` extracts only those, and the uploader replaces their statements in place with the server's `delete_statements` tool, so no graph is deleted by hand or duplicated. Also a reference for every [InfraNodus MCP server](https://infranodus.com/mcp) tool (text analysis, comparison, SEO/GEO, structured memory) for Claude Code, Cursor, [OpenClaw](https://openclaw.ai/) or any MCP client.

**Collect and curate**

- **LLM Wiki** (`llm-wiki`) - Based on [Andrej Karpathy's LLM Wiki proposal](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) this skill offers a guided workflow for designing and scaffolding a personal LLM-maintained wiki — a persistent, compounding knowledge base where the LLM incrementally builds interlinked markdown pages from raw sources. Instead of re-deriving knowledge on every query (like RAG), the wiki extracts, cross-references, and synthesizes knowledge once, then stays current as new sources arrive. Covers the full setup: raw sources, wiki pages, output layer, and a schema that co-evolves with the project. Use it when you want to build a "second brain", organize research, or set up an Obsidian + LLM knowledge base workflow.

- **Ontology Generator** (`ontology-generator`, folder `skill-ontology-creator`) - Build structured ontologies, taxonomies, and knowledge graphs by extracting entities, defining relationships, and mapping conceptual structures for any topic or for a collection of texts.

- **Project Learnings** (`project-learnings`) - Self-learning for agents working inside a project (a repo, folder, or vault). Runs proactively: at the start of a multi-step task the agent retrieves what earlier sessions learned about operating in the project; at the end it reflects and saves the durable insights — where things live, traps, conventions, decisions with their rationale, workflows, open questions, what to do differently — to an opt-in, append-only knowledge graph (`learn-<project>`) in your InfraNodus account that any client and any machine can query. Uses the [InfraNodus MCP server](https://infranodus.com/mcp) `get_project_learnings` / `add_project_learnings` / `enable_project_learnings` tools. Nothing is written without your explicit per-project opt-in and a review of each batch; until you enable a project, an automatic run is a single read that returns `enabled: false`. Only project knowledge is kept, never anything about you. Prefer it manual-only? Set `disable-model-invocation: true` in its `SKILL.md` or `"skillOverrides": { "project-learnings": "user-invocable-only" }` in `.claude/settings.local.json`.

**Analyze and refine**

- **Shifting Perspective** (`shifting-perspective`) - Analyze discourse structure using [InfraNodus MCP server](https://infranodus.com/mcp) knowledge graph analysis to diagnose the structural diversity of a text and then actively shift perspective. Based on the diversity score (biased, focused, diversified, or dispersed), applies targeted interventions: develops underrepresented viewpoints, bridges conceptual gaps, or surfaces latent ideas grounded in the actual topology of the text's knowledge graph. Use it when a conversation feels one-sided, when research needs broadening, or when you want to understand what perspectives are missing from any text, URL, or YouTube video.

- **Cognitive Variability** (`cognitive-variability`) - A skill that promotes the [cognitive variability](https://infranodus.com/about/cognitive-variability) framework for adaptive thinking to help evolve ideas and avoid getting stuck.

**Publish**

- **Writing Assistant** (`writing-assistant`) - Grammar correction, style refinement, and pattern detection that can trigger cognitive state analysis.

- **SEO Analysis** (`seo-analysis`) - Perform advanced SEO analysis to study the current informational supply and demand for a topic. Build your topical authority and create content that covers the important concepts and bridges the market gaps. Suitable for SEO and LLMO. Uses [InfraNodus MCP server](https://infranodus.com/mcp) search intent and results import functionalities.

## What gets uploaded and where

Everything below is what the skills currently do, per their `SKILL.md` and scripts. Content is sent only to the InfraNodus MCP server your agent is connected to (hosted: `https://mcp.infranodus.com`, saved to **your** InfraNodus account; or a local/self-hosted server you configured).

| Skill | Stays on your machine | Sent to InfraNodus | Saved in your account as |
|---|---|---|---|
| `infranodus`: one-off text/URL analysis | nothing written | the text or URL you give it | nothing, unless you or the agent call a saving tool (`create_knowledge_graph`, `memory_add_relations`) |
| `infranodus`: repo/vault graphs | `infranodus/manifest.json` (routing metadata: graph names, topics, gaps, endpoint, account), `infranodus/INFRANODUS_REPORT.md` (append-only build log). Scope files (`repo-*-ontology.md`, `vault-*-ontology.md`) are build intermediates: **deleted after a successful upload** unless `--keep-scopes` is passed | statements extracted from docs (md/rst/txt), the PDF text layer, docstrings and `WHY`/`NOTE`/`TODO` comments, commit/PR/issue text (via `git` and `gh`), vault page links, and any digest you approve | graphs named `repo-<project>-<scope>` / `vault-<project>-<scope>`; optional `onto-<project>` ontology (generated by the server's LLM) |
| `infranodus`: `--register-project` | marker blocks in the project's `CLAUDE.md` | nothing | with `--with-memory` only, and on your approval per session: a `<slug>-insights` memory graph |
| `llm-wiki` | raw sources, wiki pages, `output/` analyses, curated ontology files in `infranodus/` (kept; append-only) | curated ontology files: the whole file on first upload, then only newly appended lines | `wiki-<project>-<scope>` graphs |
| `ontology-generator` | the ontology is returned in chat | only if you ask to analyze or save it | only if you ask (`create_knowledge_graph` or `memory_add_relations`) |
| `project-learnings` | nothing | after you explicitly enable it for a project, the learnings batch you review | `learn-<project>` (append-only); before opt-in a run is a single read |
| `shifting-perspective`, `cognitive-variability`, `writing-assistant`, `seo-analysis` | nothing written by the skill | the text, topic or search query you analyze, when the InfraNodus tools are connected (analysis tools only, e.g. `optimize_text_structure`, `generate_content_gaps`, `generate_seo_report`) | nothing; these skills don't call saving tools |

Never mined by the repo/vault scanner: `.git`, `node_modules`, `dist`, `build`, `out`, `vendor`, virtualenvs and tool caches, `target`, `.next`/`.nuxt`, `.obsidian`, `.idea`/`.vscode`, the `infranodus/` folder itself, and likely-secret files (`.env*`, keys, anything named credential/secret/apikey). Lockfiles, minified bundles and licences are left out of the digest reading list. Scanned PDFs without a text layer are skipped (no OCR).

**Credentials.** Queries use the MCP connection you signed into (`/mcp`). The core skill's fallback uploader (`upload_scopes.py`) reads the key only from the `INFRANODUS_API_KEY` environment variable and sends it only to `infranodus.com` or a loopback address. The `llm-wiki` uploader (`upload_wiki_ontology.py`) currently also looks for a key in local MCP config files (`.mcp.json`, `~/.claude.json`, `~/.claude/settings.json`, `~/.cursor/mcp.json`, `~/.codex/config.json`); aligning both on one policy is on the [roadmap](docs/ROADMAP.md).

## Moved to InfraNodus Skills Lab

Eight experimental skills moved to a separate repository, **InfraNodus Skills Lab** ([infranodus/skills-lab](https://github.com/infranodus/skills-lab)): `actionize`, `critical-perspective`, `embodied-navigation`, `perspective-reversal`, `rhetorical-analyst`, `shopping-assistant`, `vipassana-llm`, and `youtube-viral-optimizer` (YouTube titles, thumbnails and video scripts, built from graph gaps).

- Claude Code: the same ids keep working from this marketplace, e.g. `/plugin install actionize@infranodus-skills` (fetched from the Lab repo).
- Their old folders here contain only a `README.md` pointing to the new location.
- Or use the Lab marketplace directly: `/plugin marketplace add infranodus/skills-lab`, then `/plugin install skills-lab-all@infranodus-skills-lab` (all Lab skills) or `<id>@infranodus-skills-lab`.
- They are no longer part of `infranodus-all`.
- Installed them with `npx skills add infranodus/skills -g`? Re-running that command does not remove them; they stay as unmaintained copies. Remove them, then reinstall from the Lab repo if you still want them:

  ```bash
  npx skills remove actionize critical-perspective embodied-navigation perspective-reversal rhetorical-analyst shopping-assistant vipassana-llm youtube-viral-optimizer -g
  npx skills add infranodus/skills-lab -g
  ```

## Installation (all routes)

The skills work with any LLM client. Download them from the GitHub releases page and follow the instructions for your client below.

### Step 1: Download the Skills

**Option A — From Releases (Recommended)**

1. Go to the [Releases](https://github.com/infranodus/skills/releases) page
2. Download the `.zip` or `.skill` file for the skill(s) you want

**Option B — Clone the Repository**

1. Clone this repository or download the `infranodus` folder or individual `skill-*` folders (folders that contain only a `README.md` are stubs for skills that moved to InfraNodus Skills Lab)
2. Each folder contains all necessary files for that skill
3. Create a `.zip` of the folder contents if your client requires it

### Step 2 (Optional): Get an InfraNodus API Key

Some skills can access the [InfraNodus MCP Server](https://infranodus.com/mcp) to perform more complex tasks and extract real-time data from external sources (e.g. search intent or search results). The MCP server provides free access for the first few iterations, but you'll need to [get an InfraNodus API key](https://infranodus.com/api-access) for more advanced workflows and to avoid hitting rate limits.

### Step 3: Install to Your LLM Client

#### Claude Web / Desktop

1. Go to **Settings → Capabilities**
2. Activate **"Code execution and file creation"**
3. Scroll down to the **Skills** section and activate any default skills you find useful
4. Click **"Upload Skill"** to add InfraNodus skills (`.zip` or `.skill` files downloaded in Step 1)

#### Claude Code

**Option A — Plugin marketplace (recommended):**

This repository is a Claude Code plugin marketplace. Inside Claude Code, run:

```
/plugin marketplace add infranodus/skills
/plugin install infranodus@infranodus-skills
```

Replace `infranodus` with any other skill name from this repo (e.g. `/plugin install seo-analysis@infranodus-skills`), or install all 8 skills of this repo in one go:

```
/plugin install infranodus-all@infranodus-skills
```

Installed skills are invoked with their plugin namespace, e.g. `/infranodus:infranodus` (or `/infranodus-all:infranodus` for the bundle). To update later, run `/plugin marketplace update infranodus-skills`.

> **Note:** install either the `infranodus-all` bundle **or** individual plugins, not both. Each skill would then be loaded twice under the same name and Claude Code drops one of the copies. (The Lab skills are not part of `infranodus-all`; install them by id, see [Moved to InfraNodus Skills Lab](#moved-to-infranodus-skills-lab).)

The `infranodus-all`, `infranodus` and `llm-wiki` plugins also connect the [InfraNodus MCP server](https://infranodus.com/mcp) (`https://mcp.infranodus.com`), so you don't need to add it separately. Run `/mcp`, select InfraNodus and sign in once. If you already use the InfraNodus connector on claude.ai, Claude Code recognizes the same server and connects to it only once. The other single-skill plugins don't bundle the server; follow the [MCP setup guide](https://infranodus.com/mcp) if you want their InfraNodus features.

**Option B — `npx skills` CLI:**

From your terminal:

```bash
npx skills add infranodus/skills --skill infranodus -g
```

Omit `--skill infranodus` to choose from all the skills in this repo interactively, and omit `-g` to install into the current project instead of globally.

**Option C — Manual copy:**

Copy each skill folder to the `~/.claude/skills` directory to make it available globally across all projects. **Name the destination folder after the skill's `name:` field** (the first line of its `SKILL.md` frontmatter), not after the repository folder: Claude Code uses the directory name as the slash command, and the claude.ai uploader expects the folder to match `name`. For example:

```bash
cp -r skill-cognitive-variability ~/.claude/skills/cognitive-variability
```

One skill has a `name` that is not just the folder without the `skill-` prefix:

| Repository folder | Install as |
|---|---|
| `skill-ontology-creator` | `ontology-generator` |

Alternatively, run `./install.sh` (or `./install.sh --symlink`) from the repository root — it installs the core set (`infranodus`, `ontology-generator`, `llm-wiki`, `project-learnings`) under the right names; `./install.sh --core-only` installs just `infranodus`.

To scope a skill to a specific project, create a `.claude/skills` folder inside that project and copy the skill folder(s) there instead.

#### Cursor / Windsurf / Other Code Editors

Copy each skill folder to your project's skills directory (e.g. `.cursor/skills/` for Cursor) or to a global skills directory defined in the editor settings. The skill's `SKILL.md` file will be picked up automatically.

#### ChatGPT

ChatGPT doesn't support automatic skill installation, but you can use either of these approaches:

1. **Custom GPT** — Create a new Custom GPT and paste the contents of the skill's `SKILL.md` into the instructions. Save with a descriptive name. You can then start a new conversation with it or mention it in an existing chat using the `@` sign.

2. **Project prompt** — Create a new project and paste the `SKILL.md` file (plus any additional reference files from the skill folder) into the project's system prompt. The skill will be active in every conversation within that project.

#### OpenClaw

[OpenClaw](https://openclaw.ai/) is a local autonomous AI agent that uses skills and MCP servers via [MCPorter](https://github.com/steipete/mcporter).

**Install via OpenClaw chat (recommended):**

```bash
install this skill: https://github.com/infranodus/skills/releases/latest/download/infranodus.zip
```

This link always points to the [latest release](https://github.com/infranodus/skills/releases). To pin a specific version, use `releases/download/v1.6.2/infranodus.zip` instead.

**Manual installation:**

```bash
cp infranodus.zip ~/.openclaw/skills/infranodus.zip
unzip ~/.openclaw/skills/infranodus.zip -d ~/.openclaw/skills/infranodus
```

To scope the skill to a specific project, copy it to that project's skills folder instead.

> **Note:** OpenClaw also needs [MCPorter](https://infranodus.com/mcp/deploy-terminal) installed to access MCP server tools. See the [full OpenClaw deployment guide](https://infranodus.com/mcp/deploy-openclaw) for setting up MCPorter with OAuth or API key authentication.

#### Other LLM Clients

For any client not listed above, paste the contents of the skill's `SKILL.md` file into the project instructions or system prompt of the conversation where you want to use it. If the client supports custom assistants or GPTs, you can create one using the `SKILL.md` content and invoke it with an `@` mention.

## Using the Skills

Your LLM client will automatically infer the necessary skill from the skill's description. However, you can also explicitly ask it to use a certain skill.

If you find the skill is not activated as often as you'd like (or is activated too frequently), you can modify the description of the skill and upload it again to your LLM client.

## Developing Skills

1. Download or fork the repository

2. Use Claude Web or Desktop to develop new skills (as they have the "skills_creator" skill)

3. Once created, add a new folder, add the skill inside

4. To augment the skill, open the repo in Claude Code or Cursor AI and use [InfraNodus MCP](https://infranodus.com/mcp) to find content gaps or develop the content of the skill. It will use InfraNodus' tools automatically to improve the structure and the content of the skill for you.

5. Ready to launch?

If you tag a new version, when you push the commit to your repo, a GitHub action will be triggered that will generate the release with the `.zip` files you can use to add the skills to Claude Web and Desktop.

a. Create a new tag (e.g., v1.0.0, v1.0.1, v2.0.0)

```bash
git tag v1.0.0
```

b. Push the tag to GitHub

```bash
git push origin v1.0.0
```

## Glossary

- **Knowledge graph**: a network of concepts (nodes) and the connections between them (edges). InfraNodus builds it from which words appear together.
- **Topic cluster**: a group of concepts that are more connected to each other than to the rest of the graph; roughly, one theme.
- **Content gap**: two clusters that are both important but barely connected. Bridging them is often the most useful next thing to write or research.
- **Central concepts**: the concepts that connect the most parts of the graph (high betweenness centrality).
- **Measured / deterministic**: the graph is computed with network metrics, so the same input gives the same graph; an LLM only writes on top of it.
- **MCP / connector**: the Model Context Protocol, the standard way to plug tools such as InfraNodus into Claude and other AI clients. In Claude web/desktop it is called a connector.
- **Skill**: a folder with a `SKILL.md` file that teaches the AI a workflow. **Plugin / marketplace**: Claude Code's way to install and update skills from a repository.
- **GraphRAG**: answering questions by retrieving from a knowledge graph instead of only from text chunks.
- **Ontology / `[[wikilinks]]`**: a curated list of concepts and their relations, written with Obsidian-style double-bracket links.
- **LLM wiki / second brain**: a set of interlinked notes that an AI maintains from your raw sources and that grows over time.
- **Scope / manifest**: in a project, each graph (docs, links, history) is a scope; `infranodus/manifest.json` records which graphs exist and where.

## License

Code (scripts, `bin/`, `install.sh`, plugin manifests) is licensed under [Apache-2.0](LICENSE); the skill content (`SKILL.md` files and other Markdown) under [CC BY 4.0](LICENSE). When you share or adapt the skills, credit them as "InfraNodus Skills by InfraNodus (https://infranodus.com)". See [LICENSE](LICENSE) and [NOTICE](NOTICE).
