# Phase 7: Diagnose — Planning Pattern Analysis

This phase is triggered by `/actionize diagnose` or when the user asks to analyze
their planning patterns. It can run **project-wide** (from within a project) or
**user-wide** (across all projects).

### Overview

The diagnose system maintains a user-wide history at `~/.plan/history.jsonl` that
tracks every task across all projects with three states:
- **Planned** — tasks that were created and have future deadlines
- **Completed** — tasks marked done via `done.sh` or `/actionize`
- **Deferred** — tasks past their deadline that were never completed

It uses InfraNodus to find topical patterns in what the user plans, completes, and
defers — revealing blind spots, strengths, and recurring avoidance patterns.

### Step 7.0: Sync History

First, sync the current project's task states to the user-wide history:

```bash
"${CLAUDE_SKILL_DIR}/bin/sync.sh"
```

If the user asked for user-wide analysis:

```bash
"${CLAUDE_SKILL_DIR}/bin/sync.sh" --all
```

### Step 7.1: Prepare Diagnostic Data

Run the data preparation script:

```bash
"${CLAUDE_SKILL_DIR}/bin/diagnose-prep.sh"
```

Or for a specific project:

```bash
"${CLAUDE_SKILL_DIR}/bin/diagnose-prep.sh" --project "ProjectName"
```

This outputs:
- `~/.plan/diagnostics/{date}-planned.txt` — all planned task descriptions
- `~/.plan/diagnostics/{date}-completed.txt` — all completed task descriptions
- `~/.plan/diagnostics/{date}-deferred.txt` — all deferred task descriptions
- `~/.plan/diagnostics/{date}-summary.json` — stats snapshot

### Step 7.2: Scope Selection

Ask via AskUserQuestion:
> What scope should we analyze?

- A) This project only — patterns within the current project's plan
- B) All projects — patterns across everything you've planned (user-wide)
- C) Compare projects — see how planning patterns differ between projects

### Step 7.3: InfraNodus Topical Cluster Analysis

Read the three text files generated in Step 7.1. For each non-empty category,
call `mcp__infranodus__generate_topical_clusters` to discover what topics cluster
together.

**For planned tasks** (what the user aspires to do):

Call `mcp__infranodus__generate_topical_clusters` with:
- **text:** The content of `{date}-planned.txt` (all planned task descriptions,
  newline-separated)
- **context:** "Analyzing planned task descriptions to identify topical clusters
  in the user's planning patterns across projects."

**For completed tasks** (what the user actually finishes):

Call `mcp__infranodus__generate_topical_clusters` with:
- **text:** The content of `{date}-completed.txt`
- **context:** "Analyzing completed task descriptions to identify topical clusters
  in what the user actually accomplishes versus what was planned."

**For deferred tasks** (what the user consistently avoids):

Call `mcp__infranodus__generate_topical_clusters` with:
- **text:** The content of `{date}-deferred.txt`
- **context:** "Analyzing deferred task descriptions to identify topical patterns
  in what the user consistently postpones or avoids completing."

Present each cluster analysis with a plain-language interpretation:
- **What you plan:** The themes and topics you gravitate toward when planning
- **What you finish:** The themes that actually get done — your execution strengths
- **What you defer:** The themes you consistently push back — your blind spots

### Step 7.4: Gap Analysis via InfraNodus

This is the key insight — comparing planned vs completed reveals what falls through
the cracks, and comparing planned vs deferred reveals systematic avoidance patterns.

**Planned vs Completed — what you plan but don't finish:**

Call `mcp__infranodus__difference_between_texts` with:
- **contexts:** `[{ "text": "{planned-text}" }, { "text": "{completed-text}" }]`
  (first item is the target to analyze for missing parts; second is the reference)
- **context:** "Comparing planned tasks against completed tasks to identify conceptual
  gaps — topics the user plans for but consistently fails to execute on."
- **modifyAnalyzedText:** `"detectEntities"`

This reveals: topics present in planning but absent from completion. These are
systematic execution gaps.

**Completed vs Deferred — what separates done from not-done:**

Call `mcp__infranodus__difference_between_texts` with:
- **contexts:** `[{ "text": "{deferred-text}" }, { "text": "{completed-text}" }]`
- **context:** "Comparing deferred tasks against completed tasks to understand what
  conceptual themes distinguish tasks that get done from those that get postponed."
- **modifyAnalyzedText:** `"detectEntities"`

This reveals: what's unique to deferred tasks that's absent from completed ones.
These are the characteristics of tasks the user avoids.

### Step 7.5: Longitudinal Comparison

Check for previous diagnostic results:

```bash
ls -t ~/.plan/diagnostics/*-report.md 2>/dev/null | head -5
```

If previous reports exist, read the most recent one. Compare current stats
(completion rate, deferral rate, topic clusters) against the previous report.

Present trends:
- Is the completion rate improving or declining?
- Are the same topics being deferred repeatedly?
- Have any previously deferred themes moved to completed?

If there are 2+ previous reports, call `mcp__infranodus__difference_between_texts`
comparing the previous deferred topics against the current deferred topics to see
if avoidance patterns are shifting or persistent.

### Step 7.6: Save Diagnostic Report

Write the full analysis to `~/.plan/diagnostics/{date}-report.md`:

```markdown
# Planning Diagnostics — {date}

Scope: {project-wide or user-wide}
Period: {date range of history entries}

## Stats
- Total tasks tracked: {N}
- Completed: {N} ({%})
- Deferred: {N} ({%})
- Planned (active): {N}

## What You Plan (Topic Clusters)
{InfraNodus cluster analysis of planned tasks}

## What You Finish (Topic Clusters)
{InfraNodus cluster analysis of completed tasks}

## What You Defer (Topic Clusters)
{InfraNodus cluster analysis of deferred tasks}

## Execution Gaps (Planned vs Completed)
{difference_between_texts results — topics you plan but don't finish}

## Avoidance Patterns (Deferred vs Completed)
{difference_between_texts results — what distinguishes tasks you avoid}

## Trends
{comparison with previous reports, if available}

## Reflection
{2-3 actionable observations about the user's planning patterns}
```

### Step 7.7: Deliver Insights

Present the report to the user with a structured summary. Focus on actionable
insights, not just data. The tone should be reflective and constructive — like
a coach reviewing performance, not a judge.

Example delivery:

```
PLANNING DIAGNOSTICS
════════════════════════════════════════
Completion rate: 67% (up from 55% last week)
Deferral rate:   25%

WHAT YOU FINISH:
  Backend infrastructure, data pipelines, testing
  → You execute well on technical foundation work

WHAT YOU DEFER:
  UI polish, documentation, user-facing design
  → Frontend and docs consistently slip past deadlines

EXECUTION GAP:
  You plan "text analysis" and "visualization" but
  complete "schema" and "data pipeline" — the analytical
  backend gets done, the presentation layer doesn't.

RECOMMENDATION:
  Front-load one UI task per week before backend work.
  Your deferred items suggest avoidance of visual/design
  decisions, not lack of time.
════════════════════════════════════════
```

Ask via AskUserQuestion:
> Based on this analysis, would you like to adjust your current plan?

- A) Yes — rebalance deadlines based on these patterns
- B) Save and continue — I'll think about this
- C) Send to Telegram — push this summary to my Telegram
- D) Run deeper analysis — I want to explore a specific pattern

If C: send via Telegram using the remind.sh pattern (curl to Bot API).
If D: ask what pattern to explore, then use
`mcp__infranodus__generate_research_questions` on that subset.

---

## Phase 8: Diagnose Cron — Automated Sync + Nudge

During Phase 4 (reminder setup), also set up a 3-day sync cron. This runs
`sync.sh --all` to detect newly deferred tasks across all projects, then sends
a Telegram message nudging the user to run `/actionize diagnose`.

Check if the diagnostics cron already exists:

```bash
crontab -l 2>/dev/null | grep -q "actionize-diagnose" && echo "DIAG_CRON_EXISTS" || echo "DIAG_CRON_MISSING"
```

If DIAG_CRON_MISSING, add it alongside the daily reminder:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR}"
PROJECT_DIR=$(pwd)
(crontab -l 2>/dev/null || true; echo "# actionize-diagnose: sync + nudge every 3 days"; echo "17 11 */3 * * ${SKILL_DIR}/bin/sync.sh --all && ${SKILL_DIR}/bin/diagnose-nudge.sh") | crontab -
```

The nudge script sends a short Telegram message: "You have N deferred tasks across
M projects. Run /actionize diagnose for pattern analysis."
