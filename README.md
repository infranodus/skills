# InfraNodus Claude Skills Repository

This collection of skills is based on the [InfraNodus cognitive variability](https://infranodus.com/about/cognitive-variability) framework that is implemented in [InfraNodus](https://infranodus.com) text analysis tool.
Use the skills as extended prompts in Claude Web or in your favorite LLM client. They will augment the capacities of the model and help you introduce custom logic, frameworks, workflows, and guidelines into the model's behavior.

The skills are designed to work with each other and to hand off important tasks when needed. They are also integrated with the [InfraNodus MCP Server](https://infranodus.com/mcp) tools, so you can use advanced text gap analysis, SEO optimization and data import, and knowledge graph memory in your workflows.

## Skills Available

- **Cognitive Variability** - A skill that promotes the [cognitive variability](https://infranodus.com/about/cognitive-variability) framework for adaptive thinking to help evolve ideas and avoid getting stuck.

- **Critical Perspective** - Engage in critical thinking by questioning assumptions, exploring alternative perspectives, and uncovering latent topics in conversations.

- **Writing Assistant** - Grammar correction, style refinement, and pattern detection that can trigger cognitive state analysis.

- **Ontology Creator** - Build structured ontologies, taxonomies, and knowledge graphs by extracting entities, defining relationships, and mapping conceptual structures for any topic or for a collection of texts.

- **SEO Analysis** - Perform advanced SEO analysis to study the current informational supply and demand for a topic. Build your topical authority and create content that covers the important concepts and bridges the market gaps. Suitable for SEO and LLMO. Uses [InfraNodus MCP server](https://infranodus.com/mcp) search intent and results import functionalities.

- **YouTube Viral Optimizer** - Generate high-CTR YouTube titles, thumbnails, and full video scripts optimized for virality. Covers psychological triggers, SEO-driven title strategy, thumbnail copywriting, algorithm positioning, and a complete script structure (Pattern Interrupt → Hook → Framing → Curiosity Loop → Escalation → Payoff → Relevance Bridge → Loop Reopen). Includes a Graph-to-Script pipeline that uses [InfraNodus MCP server](https://infranodus.com/mcp) to extract structural gaps from any topic and turn them into ready-made curiosity loops. Works for any niche or channel.

- **Shopping Assistant** - A systematic, multi-phase shopping research workflow that acts as your personal shopping advisor. Gathers requirements, researches product categories via web search, builds comparison matrices, analyzes reviews for recurring praise and complaints, and converges on 3-4 best options with clear reasoning. Designed to save hours of research and avoid both impulse buys and analysis paralysis.

- **Rhetorical Analyst** - Analyze arguments, debate tactics, and rhetorical moves across three dimensions: persuasion, rhetoric, and logic. Identifies the moves being made, scores their effectiveness, exposes hidden assumptions, tracks logical gaps, and checks for asymmetric standards — including the analyst's own. Use it to break down debates, stress-test your own arguments, or understand why something feels persuasive but wrong.

- **InfraNodus CLI / Tool Use** - A comprehensive reference for all [InfraNodus MCP server](https://infranodus.com/mcp) tools: text analysis, knowledge graph generation, content gap detection, SEO/GEO optimization, structured memory, text comparison, and GraphRAG retrieval. Includes setup instructions, a full tool catalog with parameters, and practical examples. Designed to be copied into [OpenClaw](https://openclaw.ai/), Claude Code, Cursor, or any LLM client that supports MCP or tool-use prompts — giving any AI assistant access to InfraNodus' text network analysis capabilities.

## Installation

The skills work with any LLM client. Download them from the GitHub releases page and follow the instructions for your client below.

### Step 1: Download the Skills

**Option A — From Releases (Recommended)**

1. Go to the [Releases](https://github.com/infranodus/skills/releases) page
2. Download the `.zip` or `.skill` file for the skill(s) you want

**Option B — Clone the Repository**

1. Clone this repository or download individual `skill-*` folders
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

Copy each skill folder (e.g. `skill-cognitive-variability`) to the `~/.claude/skills` directory to make it available globally across all projects.

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
install this skill: https://github.com/infranodus/skills/releases/download/v1.0.8/infranodus-cli.zip
```

Replace `v1.0.8` with the [latest release version](https://github.com/infranodus/skills/releases).

**Manual installation:**

```bash
cp infranodus-cli.zip ~/.openclaw/skills/infranodus-cli.zip
unzip ~/.openclaw/skills/infranodus-cli.zip -d ~/.openclaw/skills/infranodus-cli
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
