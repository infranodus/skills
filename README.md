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

- **InfraNodus CLI / Tool Use** - A comprehensive reference for all [InfraNodus MCP server](https://infranodus.com/mcp) tools: text analysis, knowledge graph generation, content gap detection, SEO/GEO optimization, structured memory, text comparison, and GraphRAG retrieval. Includes setup instructions, a full tool catalog with parameters, and practical examples. Designed to be copied into [OpenClaw](https://openclaw.ai/), Claude Code, Cursor, or any LLM client that supports MCP or tool-use prompts — giving any AI assistant access to InfraNodus' text network analysis capabilities.

## Installation

### Option 1: Download from Releases (Recommended)

1. Go to the [Releases](https://github.com/infranodus/skills/releases) page
2. Download the `.zip` file for the skill you want to use
3. Install the skill in your Claude client (see below)

### Option 2: Manual Installation

1. Clone this repository or download individual skill folders
2. Each `skill-*` folder contains all necessary files for that skill
3. Create a `.zip` file of the skill folder contents if needed

## Installing the Skills

### In Claude Web and Claude Desktop

- Add skills via Settings → Capabilities

### In Claude CLI (Claude Code)

- Add the markdown skills folders into the `.claude/skills` folder for global access or into the `~/your_project/.claude/skills` for project access only.

### In Claude API

- Access specific skills using the `/v1/skills` endpoint

### In Other LLM Clients

- Upload the SKILL.md file from the skill folder to a conversation or a project folder and instruct the model to follow the guidelines provided.

## Using the Skills

Your Claude client will automatically infer the necessary skill from the Skill's description. However, you can also explicitly ask it to use a certain skill.

If you find the skill is not activated as often as you'd like (or is activated too frequently), you can also modify the description of the skill and upload it again to your LLM client.

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
