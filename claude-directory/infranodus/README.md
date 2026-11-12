# InfraNodus

A knowledge graph and gap finder for your texts, notes, vault or agent memory. InfraNodus turns any text into a network of concepts and shows its structure: the main topics, how they connect, and the gaps between them that are worth developing.

## What you can do

- Analyze a text, a web page or a YouTube video: topical clusters, key concepts, structural gaps, and how diverse or biased the discourse is.
- Generate research questions and ideas that bridge the gaps between topics.
- Compare texts: what they share, and what one covers that the other is missing.
- Analyze Google search results and related search queries to find content opportunities (SEO / GEO).
- Analyze and optimize an AI assistant's memories: find duplicates, contradictions and gaps between groups of memories.
- Graph a project folder, code repo or Obsidian vault: Claude reads the docs, notes and PDFs, maps which code file imports which, collects the WHY/NOTE comments and the commit, pull request and issue history, saves all of it to your InfraNodus account as knowledge graphs, writes a digest of how the project works, and later answers questions from the graphs instead of re-reading the files.

## Requirements

Connect the InfraNodus connector first: in Claude, open **Settings → Connectors**, add `https://mcp.infranodus.com` and sign in with your InfraNodus account. In Claude Code you can also run `claude mcp add --transport http infranodus https://mcp.infranodus.com`. The plugin does not bring the server with it; it uses the one you connected.

## What this plugin runs, reads and sends

- It is one skill: Markdown instructions for Claude. It contains no scripts, hooks, programs or MCP server, and it never asks for or reads an API key.
- Text you ask it to analyze is sent to InfraNodus (`mcp.infranodus.com`) through the connector you signed in to. Graphs are saved to your account only when you ask for it.
- When you ask it to analyze an assistant's memories, Claude reads the memory files you point at and sends their text to InfraNodus; it changes them only after you agree.
- When you ask it to graph a project folder, Claude reads the files you chose with its own file tools and sends their text to InfraNodus. It then writes three things in that folder: `infranodus/manifest.json` (the list of saved graphs), `infranodus/INFRANODUS_REPORT.md` (an append-only log) and a marked block in `CLAUDE.md` that routes later questions to the graphs. Delete the marked block to opt out.
- When you ask for the project's history, Claude reads the commits with the read-only `git log` command, and reads pull requests and issues only through a GitHub connector you connected yourself. It never pushes, comments or changes anything on GitHub.
- When you ask for an AI-written entity graph, the text is processed by an AI model on the InfraNodus side and counts against your InfraNodus AI quota. Claude asks before doing that.

## Large folders: the full edition

In this plugin Claude does the reading and the uploading, so every file passes through your conversation. That is fine for a docs folder or a mid-sized repo and slow on a large one. The full edition of this skill extracts and uploads the folder with programs on your machine, in the background, using only your InfraNodus account, and tracks changes per file exactly. It is published with the rest of the InfraNodus skills at [github.com/infranodus/skills](https://github.com/infranodus/skills). In Claude Code:

```
/plugin marketplace add infranodus/skills
/plugin install infranodus@infranodus-skills
```

Both editions have the same name and read the same `infranodus/manifest.json`, so uninstall this one when you switch.

## Links

- [InfraNodus](https://infranodus.com) · [MCP server](https://infranodus.com/mcp) · [Support](https://support.noduslabs.com)
- [Privacy policy](https://infranodus.com/about/privacy-policy) · [Terms](https://infranodus.com/about/terms-conditions)

Licensed under Apache-2.0 (manifests) and CC BY 4.0 (skill content); see `LICENSE`.
