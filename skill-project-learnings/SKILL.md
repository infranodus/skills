---
name: project-learnings
description: >
  Self-learning for agents working inside a project (a repo, a folder, a vault): retrieve what earlier sessions learned about operating in it, reflect at the end of a task on what was learned, and save the durable insights — where things live, traps, conventions, decisions with their rationale, workflows, open questions — to an opt-in, append-only InfraNodus knowledge graph (learn-<project>) that any client and any machine can query. Uses the InfraNodus MCP server's get_project_learnings / add_project_learnings / enable_project_learnings tools. Use at the start of a substantive task in a named project ("what do we know about this repo?"), at the end of one ("what did I learn?"), or when the user says "save learnings", "remember this about the project", "start keeping learnings", "what did previous sessions find", or "/learnings". Never writes without the user's explicit per-project opt-in and review of each batch. Keeps knowledge about the project only, never about the person.
---

# Project Learnings

An agent that works in a project keeps rediscovering the same things: which
of nine files holds the model list, that the tests only exist as ad-hoc
scripts, why a cache is per-process, which command actually deploys. This
skill turns those rediscoveries into a **learnings graph** in the user's
InfraNodus account — `learn-<project>` — that the next session reads before
it starts and appends to when it finishes.

It is a graph rather than a notes file because learnings link to the same
entities (file paths, modules, concepts) as everything else in the project:
"which parts of the codebase accumulate traps" is a graph query, and the
gaps between what is known and what the code contains show where nobody has
looked yet.

## Prerequisites

The connected InfraNodus MCP server must expose these three tools (added
after `infranodus-mcp-server` 1.7.4; hosted at https://mcp.infranodus.com or
the npm package):

- `get_project_learnings` — read (by prompt, by entity, overview, or list)
- `add_project_learnings` — propose / write (dry run by default)
- `enable_project_learnings` — create the graph, **only on the user's explicit request**

If they are missing from the tool list, say so once ("the connected
InfraNodus server doesn't expose project learnings; update it or connect
https://mcp.infranodus.com") and continue the task without this skill. Do
not emulate the feature with `memory_add_relations` — that would bypass the
consent model.

## Consent — read before anything else

1. **Nothing is written unless the user enabled learnings for this project.**
   `add_project_learnings` refuses (`enabled: false`) when the graph does not
   exist and never creates it. Never call `enable_project_learnings` on your
   own initiative — only when the user explicitly asks to start keeping
   learnings for a project. Before that call, tell them in two sentences what
   will be stored (project knowledge only), where (a private, append-only
   graph in their InfraNodus account that they can delete at any time), and
   that each batch is shown before it is saved.
2. **Show every batch before it is written.** `add_project_learnings` is a
   dry run by default. Present the plan, ask, and only then call again with
   `confirm: true`. If the client supports MCP elicitation the server asks
   the user itself and writes in the same call. Skip the question only when
   the user has said, in this conversation, that they do not want to be asked.
3. **Project knowledge only.** "The model list lives in nine files" is a
   learning. "The user prefers short answers" is not — that belongs in the
   client's own memory, never in a shared graph.
4. **No secrets, hostnames, env values, credentials, customer data, or
   verbatim error output.** Paths and descriptions only. The server rejects
   secret-like statements and reports only their index.
5. If `get_project_learnings` returns `enabled: false`, carry on silently.
   Do not suggest enabling unless the user asks about memory or you notice
   yourself rediscovering something a previous session should have known.

## Workflow

### 1. Start of a substantive task — retrieve

Call `get_project_learnings` with the project name and the task as `prompt`.
Use the same project name every time (the repo or folder name; call the tool
with no `project` to see which names already exist in the account). The
response carries the most relevant learnings, the areas that have
accumulated knowledge (`knownAreas`), and the `gaps`. Read them before
opening files. Skip for trivial tasks (a typo, a one-line answer).

### 2. Before touching an unfamiliar area — look up the entity

`get_project_learnings` with `entity` set to the file path, module, or
concept returns every learning that mentions it. Cheap; do it before the
first edit in an area this session has not visited.

### 3. End of a substantive task — reflect

A substantive task is multi-step, involved discovery, a correction from the
user, or a non-obvious fix. Ask yourself four questions:

- What did I have to discover that was not in the docs or obvious from the code?
- Where did I go wrong first, and what was the actual cause?
- What decision did I make, and why that one?
- What would I check first next time?

Draft 0–5 statements. **Zero is a normal answer**; do not pad. Each must pass
all five admission criteria:

1. Not derivable from the code, docs, or git history in a few reads
2. Would have saved time if known at the start
3. Survived verification — only after the thing actually worked
4. About the project, never about the person
5. Adds insight, not just a fact: prefer learnings that connect things that
   are not obviously connected — a cross-module dependency, a pattern that
   recurs across files, the non-obvious consequence of a design choice, a
   hypothesis about *why* something is the way it is. A location fact is
   admissible; a location fact plus the reason it is scattered is better.

Then `add_project_learnings` (dry run) → show the plan → `confirm: true`
on agreement.

### 4. User-initiated

"Save what you learned", "remember this about the project", "/learnings":
run step 3 immediately for the current session, whatever its size.

## Statement contract

One statement per learning, at most two sentences, with **at least two
`[[wikilinked]]` entities** — file paths, modules, functions, concepts,
tools. Entities are what make the graph queryable, so link the things a
future session would search for.

Each statement carries one `type`:

| type | use for |
|---|---|
| `location` | where X lives, especially when it is scattered or misnamed |
| `trap` | what went wrong first and why |
| `convention` | how things are done here that the code does not spell out |
| `decision` | what was chosen and the rationale |
| `workflow` | how to run, test, build, deploy, debug |
| `question` | open, unresolved, worth a future session's attention |

Example (a real one):

> `The list of available AI model names is duplicated in 9 places: the modelToUse enums in [[src/schemas/index.ts]], [[src/instructions.ts]], [[src/resources/about.ts]], [[README.md]], and the tool defaults in [[generateOntologyGraph.ts]] and [[analyzeLlmResults.ts]]. Source of truth is [[infranodus-app]] routes/ai.js getModelsAvailable, which keeps old names as aliases.` — `location`

## Reading the tool responses

- `enabled: false` → not enabled for this project; nothing written. Carry on
  (or, if the user asked to save, tell them it is not enabled and offer to
  enable it — they decide).
- `dryRun: true` with `wouldWrite` → show it. Items marked `reinforced` are
  near-duplicates of something already known; they are written as a short
  "Confirmed again" statement, which raises the weight of the same links.
  That is deliberate: things that keep being rediscovered become central.
- `declined: true` with a `note` → the user wants a change; adjust and try
  once more. Without a note → do not retry.
- `rejected` with indices → strip the secret-like content from those
  statements (the server never echoes it) and resubmit.
- A stale learning is not deleted (the graph is append-only); it is
  superseded by a newer statement, and retrieval sorts newest first. If you
  find a learning that names a file that no longer exists, add the
  correction as a new statement.

## Using the graph as a graph

Once a project has a few dozen learnings, the InfraNodus tools that work on
any saved graph work on `learn-<project>` too:

- `get_project_learnings` with no `prompt`/`entity` → overview: known areas,
  main concepts, gaps.
- `analyze_existing_graph_by_name` on the graph name → clusters and the
  `[[type_trap]]` neighbourhood, i.e. the fragile parts of the codebase.
- If the **infranodus** skill has built `repo-<project>-*` graphs,
  `difference_between_texts` with `{graphName}` contexts shows modules that
  have code but no learnings — unexplored territory — and the learnings
  graph can be added to that project's `infranodus/manifest.json` as a scope
  with `policy: "learnings"` so question routing sees it. Optional; nothing
  here depends on the manifest.

The `type-*` labels are mention nodes attached to each statement's concepts.
They are useful for filtering and neighbourhood queries and noisy for
cluster analysis; hide mention nodes in the InfraNodus UI when studying the
concept structure.

## Relationship to other skills

- **infranodus** — maps what a repo or vault *contains* (deterministic
  extraction). This skill records what an agent *learned operating in it*.
  They share entity names, so the graphs compose.
- **llm-wiki** — authored knowledge pages compounding over time. Route there
  when the user wants prose, not one-line operational learnings.
- Claude Code's own file memory — per-user, per-machine. Keep using it for
  user preferences and for project facts when learnings are not enabled;
  when they are, project-type facts go to both.

## Example

> **User:** start keeping learnings for this repo
>
> **Agent:** I'll create a private, append-only graph `learn-mcp-server-infranodus` in your InfraNodus account. It will hold knowledge about operating in this project — where things live, traps, conventions, decisions — never anything about you, never secrets. I'll show each batch before saving, and you can delete the graph any time. Enabling now.
> *(calls `enable_project_learnings`)*
>
> …later, after a task…
>
> **Agent:** Two things from this session worth keeping:
> 1. [trap] `Reading a graph right after creating it can fail on infranodus.com: the app runs several instances with a per-process contexts-list cache ([[lib/middleware/getOwnerContextsList.js]]); [[src/utils/learnings.ts]] retries reads and treats any positive as authoritative.`
> 2. [workflow] `There is no test runner in the repo; [[npm test]] builds with tsc and runs [[node --test]] over test/*.test.mjs against dist/.`
>
> Save these? *(dry run shown; on "yes" → `confirm: true`)*
