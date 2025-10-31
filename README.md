# InfraNodus Claude Skills Repository

This collection of skills is based on the [InfraNodus cognitive variability](https://infranodus.com/about/cognitive-variability) framework that is implemented in [InfraNodus](https://infranodus.com) text analysis tool.
Use the skills as extended prompts in Claude Web or in your favorite LLM client. They will augment the capacities of the model and help you introduce custom logic, frameworks, workflows, and guidelines into the model's behavior.

The skills are designed to work with each other and to hand off important tasks when needed. They are also integrated with the [InfraNodus MCP Server](https://github.com/infranodus/mcp-server-infranodus) tools, so you can use advanced text gap analysis, SEO optimization, and knowledge graph memory in your workflows.

## Skills Available

- **Cognitive Variability** - A skill that promotes the [cognitive variability](https://infranodus.com/about/cognitive-variability) framework for adaptive thinking to help evolve ideas and avoid getting stuck.

- **Critical Perspective** - Engage in critical thinking by questioning assumptions, exploring alternative perspectives, and uncovering latent topics in conversations.

- **Writing Assistant** - Grammar correction, style refinement, and pattern detection that can trigger cognitive state analysis.

## Installation

### Option 1: Download from Releases (Recommended)

1. Go to the [Releases](https://github.com/infranodus/skills/releases) page
2. Download the `.zip` file for the skill you want to use
3. Install the skill in your Claude client (see below)

### Option 2: Manual Installation

1. Clone this repository or download individual skill folders
2. Each `skill-*` folder contains all necessary files for that skill
3. Create a `.zip` file of the skill folder contents if needed

## Using the Skills

### In Claude Web

- Add skills via Settings → Capabilities

### In Claude CLI (Claude Code)

- Activate skills using the `/skills` command and follow the instructions

### In Claude API

- Access specific skills using the `api/v1/skills` endpoint

### In Other LLM Clients

- Upload the SKILL.md file from the skill folder and instruct the model to follow the guidelines
