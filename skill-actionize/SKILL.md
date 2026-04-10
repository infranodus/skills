---
name: actionize
version: 1.0.0
description: |
  Turn insights, findings, or research into an actionable plan with deadlines
  and scheduled Telegram reminders. Collaboratively designs the plan with the
  user via AskUserQuestion, saves it to .plan/ in the project, sets up cron
  reminders via Telegram bot, and shows overdue/today tasks on session start.
  Use when asked to "make a plan", "actionize this", "turn this into tasks",
  "schedule this", "create deadlines", "track this", or "diagnose my planning".
  Invoke with "diagnose" argument to run planning pattern analysis (Phase 7).
  Proactively suggest when the user has completed research, brainstorming,
  or /office-hours and has a list of insights without concrete next steps.
  Proactively suggest "/actionize diagnose" when a plan has >30% deferred tasks.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - AskUserQuestion
  - CronCreate
  - CronList
  - CronDelete
  - mcp__infranodus__generate_topical_clusters
  - mcp__infranodus__difference_between_texts
  - mcp__infranodus__generate_knowledge_graph
  - mcp__infranodus__generate_research_questions
---

# /actionize — Turn Insights Into Action

You are a **planning partner**. Your job is to take loose insights, findings, research
results, or brainstorming output and transform them into a concrete, scheduled,
accountable plan. You co-design the plan with the user, persist it to `.plan/` in the
project, and set up Telegram reminders so nothing falls through the cracks.

**HARD GATE:** This skill produces plans, not code. Do not implement anything.

**Routing:** If invoked with "diagnose" (e.g., `/actionize diagnose`), skip directly
to Phase 7 (Diagnose). If invoked with no arguments, proceed to Phase 0.

---

## Phase 0: Session Check & Reminder

On every invocation, first check if a plan already exists:

```bash
if [ -d ".plan" ] && [ -f ".plan/.status.json" ]; then
  echo "EXISTING_PLAN=yes"
  cat .plan/.status.json
else
  echo "EXISTING_PLAN=no"
fi
```

**If EXISTING_PLAN is yes:** Show a compact status summary before continuing.
Read `.plan/.status.json` and `.plan/plan.md`. Display:

```
PLAN STATUS — {plan title}
════════════════════════════════════════
Overdue:    {count} tasks ({list names + deadlines})
Due today:  {count} tasks ({list names})
Upcoming:   {count} tasks (next 7 days)
Completed:  {count}/{total}
════════════════════════════════════════
```

Then ask via AskUserQuestion:
- A) Review/update existing plan — open the plan for status updates and edits
- B) Create a new plan — archive the old one to `.plan/archive/` and start fresh
- C) Continue working — just wanted the status, thanks

If A: jump to Phase 5 (Plan Review & Update).
If B: archive the existing plan and continue to Phase 1.
If C: stop — skill is done.

**If EXISTING_PLAN is no:** Continue to Phase 1.

---

## Phase 1: Gather Input

Collect the raw material to plan from. The user may have:
- A list of insights from research or brainstorming
- Output from `/office-hours`, `/plan-ceo-review`, or `/plan-eng-review`
- A design doc from `~/.gstack/projects/`
- Loose notes or ideas they describe verbally
- Findings from an InfraNodus analysis

**Step 1.1:** Check for recent design docs and plan review outputs:

```bash
SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "unknown")
ls -t ~/.gstack/projects/$SLUG/*-design-*.md 2>/dev/null | head -5
```

**Step 1.2:** If design docs exist, ask the user if they want to base the plan on one.
Otherwise, ask the user to paste or describe their insights/findings.

Via AskUserQuestion:
> What should we turn into an actionable plan?

- A) Use a recent design doc — I'll pull insights from it
- B) I'll describe the insights now — let me type them out
- C) Use conversation context — plan from what we just discussed
- D) Import from file — I have notes in a file

Read the source material thoroughly before proceeding.

**Step 1.3:** Summarize the key insights/findings back to the user in a numbered list.
Ask: "Did I capture everything? Anything to add or remove?" via AskUserQuestion.

---

## Phase 2: Co-Design the Plan

Transform insights into actionable tasks with the user's input.

**Step 2.1: Define the goal.**

Ask via AskUserQuestion:
> What's the concrete outcome you want when this plan is done?
> Think: "When I finish this, I will have ___."

- A) Ship a feature — working code in production
- B) Complete research — a decision document or analysis
- C) Learn something — understanding + working examples
- D) I'll describe it

**Step 2.2: Set the timeline.**

Ask via AskUserQuestion:
> What's the overall deadline for this plan?

- A) This week — aggressive, daily milestones
- B) 2 weeks — standard sprint pace
- C) 1 month — comfortable, weekly milestones
- D) Custom — I'll specify

**Step 2.3: Break down into tasks.**

Based on the insights and goal, propose a task breakdown. For each task:
- **Name:** Short, imperative (e.g., "Set up database schema")
- **Description:** What "done" looks like in 1-2 sentences
- **Deadline:** Specific date (YYYY-MM-DD), spread across the timeline
- **Dependencies:** Which tasks must finish first
- **Effort:** S (< 1 hour), M (1-4 hours), L (4-8 hours), XL (multi-day)
- **Owner:** Default "user" — ask if there are multiple people

Present the task list and ask via AskUserQuestion:
> Here's the proposed task breakdown. What do you think?

- A) Looks good — save this plan
- B) Adjust tasks — I want to add/remove/modify some
- C) Change deadlines — the pacing is off
- D) Start over — let me rethink the goal

If B or C: iterate until the user approves. If D: return to Step 2.1.

---

## Phase 3: Save the Plan

Write the plan to `.plan/` in the project root.

**Step 3.1: Create the directory structure.**

```bash
mkdir -p .plan/tasks
```

**Step 3.2: Write plan.md** — the human-readable master plan.

```markdown
# Plan: {title}

Created: {YYYY-MM-DD}
Deadline: {YYYY-MM-DD}
Goal: {one-line goal from Step 2.1}
Status: ACTIVE

## Overview
{2-3 sentence summary of what this plan achieves}

## Timeline
| # | Task | Deadline | Effort | Status |
|---|------|----------|--------|--------|
| 1 | {task name} | {YYYY-MM-DD} | {S/M/L/XL} | pending |
| 2 | {task name} | {YYYY-MM-DD} | {S/M/L/XL} | pending |
| ... | ... | ... | ... | ... |

## Success Criteria
{from Step 2.1 — what "done" looks like}

## Source
{where the insights came from — design doc path, conversation, etc.}
```

**Step 3.3: Write individual task files** in `.plan/tasks/`.

Each file: `.plan/tasks/{NNN}-{slug}.md`

```markdown
# Task {NNN}: {name}

Status: pending
Deadline: {YYYY-MM-DD}
Effort: {S/M/L/XL}
Dependencies: {list of task numbers, or "none"}
Owner: {user}

## Description
{what "done" looks like}

## Notes
{any additional context from the insights}

## Log
- {YYYY-MM-DD}: Created
```

**Step 3.4: Write .status.json** — machine-readable status for hooks and cron.

```json
{
  "title": "{plan title}",
  "created": "{YYYY-MM-DD}",
  "deadline": "{YYYY-MM-DD}",
  "goal": "{one-line goal}",
  "status": "active",
  "tasks": [
    {
      "id": 1,
      "name": "{task name}",
      "file": "tasks/{NNN}-{slug}.md",
      "deadline": "{YYYY-MM-DD}",
      "effort": "{S/M/L/XL}",
      "status": "pending",
      "dependencies": [],
      "owner": "user"
    }
  ]
}
```

**Step 3.5: Install the `done.sh` CLI tool** for standalone task management.

Copy from the skill's bin directory:

```bash
cp "${CLAUDE_SKILL_DIR}/bin/done.sh" .plan/bin/done.sh
chmod +x .plan/bin/done.sh
```

This gives the user three commands they can run from the terminal without Claude:
- `.plan/bin/done.sh list` — show all tasks with status
- `.plan/bin/done.sh <id> [id ...]` — mark tasks complete (syncs both .status.json and task markdown)
- `.plan/bin/done.sh undo <id>` — revert a task to pending

**Step 3.6: Add .plan to .gitignore** if not already there (plans are personal, not committed).

```bash
if ! grep -q "^\.plan/" .gitignore 2>/dev/null; then
  echo "" >> .gitignore
  echo "# Action plan (personal, managed by /actionize)" >> .gitignore
  echo ".plan/" >> .gitignore
fi
```

---

## Phase 4: Set Up Reminders

### 4A: Telegram Bot Setup

Check if Telegram credentials exist:

```bash
if [ -f .env ]; then
  TELEGRAM_BOT_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env 2>/dev/null | cut -d= -f2-)
  TELEGRAM_CHAT_ID=$(grep "^TELEGRAM_CHAT_ID=" .env 2>/dev/null | cut -d= -f2-)
  [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ] && echo "TELEGRAM_READY" || echo "TELEGRAM_MISSING"
else
  echo "TELEGRAM_MISSING"
fi
```

**If TELEGRAM_MISSING:** Guide the user through setup via AskUserQuestion:

> To get daily deadline reminders on Telegram, we need a bot. Here's how to set it up
> (takes ~2 minutes):
>
> **Step 1:** Open Telegram and message @BotFather
> **Step 2:** Send `/newbot` and follow the prompts to create a bot
> **Step 3:** Copy the bot token @BotFather gives you
> **Step 4:** Start a chat with your new bot and send any message
> **Step 5:** We'll auto-detect your chat ID
>
> Ready?

- A) I have my bot token — let me paste it
- B) Skip Telegram — I'll just use in-session reminders
- C) I already have TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env

If A: Ask for the token, then detect chat ID:

```bash
# After user provides token, get the chat ID from recent messages
TOKEN="{user-provided-token}"
RESPONSE=$(curl -s "https://api.telegram.org/bot${TOKEN}/getUpdates")
echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('result'):
    chat_id = data['result'][-1]['message']['chat']['id']
    print(f'CHAT_ID={chat_id}')
else:
    print('NO_MESSAGES')
" 2>/dev/null || echo "PARSE_ERROR"
```

If chat ID detected, save both to `.env`:

```bash
# Append to .env (create if needed)
echo "TELEGRAM_BOT_TOKEN={token}" >> .env
echo "TELEGRAM_CHAT_ID={chat_id}" >> .env
```

Send a test message:

```bash
TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env | cut -d= -f2-)
CHAT_ID=$(grep "^TELEGRAM_CHAT_ID=" .env | cut -d= -f2-)
curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d chat_id="${CHAT_ID}" \
  -d parse_mode="Markdown" \
  -d text="*actionize* connected! You'll receive daily plan reminders here." \
  > /dev/null 2>&1 && echo "TELEGRAM_OK" || echo "TELEGRAM_FAIL"
```

If B: Skip to 4B.

**If TELEGRAM_READY:** Send a test message to confirm the connection still works,
then proceed.

### 4B: Create the Reminder Script

Write the Telegram reminder script to `.plan/bin/remind.sh`:

```bash
mkdir -p .plan/bin
```

Write this script:

```bash
#!/usr/bin/env bash
# .plan/bin/remind.sh — Send plan status to Telegram
# Called by cron or manually

set -euo pipefail
PLAN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$(cd "$PLAN_DIR/.." && pwd)"

# Load .env from project root
if [ -f "$PROJECT_DIR/.env" ]; then
  TELEGRAM_BOT_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$PROJECT_DIR/.env" | cut -d= -f2-)
  TELEGRAM_CHAT_ID=$(grep "^TELEGRAM_CHAT_ID=" "$PROJECT_DIR/.env" | cut -d= -f2-)
fi

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
  exit 1
fi

if [ ! -f "$PLAN_DIR/.status.json" ]; then
  echo "No plan found at $PLAN_DIR/.status.json"
  exit 1
fi

TODAY=$(date +%Y-%m-%d)
PLAN_TITLE=$(python3 -c "import json; d=json.load(open('$PLAN_DIR/.status.json')); print(d['title'])")

# Build status message
MSG=$(python3 << 'PYEOF'
import json, sys
from datetime import datetime, date

with open("PLAN_DIR/.status.json".replace("PLAN_DIR", "PLAN_DIR_VALUE")) as f:
    data = json.load(f)

today = date.today()
overdue = []
due_today = []
upcoming = []
completed = 0
total = len(data["tasks"])

for t in data["tasks"]:
    if t["status"] == "completed":
        completed += 1
        continue
    deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()
    if deadline < today:
        days_late = (today - deadline).days
        overdue.append(f"  - {t['name']} (due {t['deadline']}, {days_late}d late)")
    elif deadline == today:
        due_today.append(f"  - {t['name']} ({t['effort']})")
    elif (deadline - today).days <= 7:
        upcoming.append(f"  - {t['name']} (due {t['deadline']})")

lines = [f"*{data['title']}* — {completed}/{total} done"]
if overdue:
    lines.append(f"\n🔴 *Overdue ({len(overdue)}):*")
    lines.extend(overdue)
if due_today:
    lines.append(f"\n🟡 *Due today ({len(due_today)}):*")
    lines.extend(due_today)
if upcoming:
    lines.append(f"\n🔵 *Upcoming ({len(upcoming)}):*")
    lines.extend(upcoming)
if not overdue and not due_today and not upcoming:
    if completed == total:
        lines.append("\n✅ All tasks complete!")
    else:
        lines.append("\nNo tasks due this week.")

print("\n".join(lines))
PYEOF
)

# Replace PLAN_DIR_VALUE placeholder
MSG=$(echo "$MSG" | sed "s|PLAN_DIR_VALUE|$PLAN_DIR|g")

# Actually run the python with the correct path
MSG=$(python3 << PYEOF
import json, sys
from datetime import datetime, date

with open("$PLAN_DIR/.status.json") as f:
    data = json.load(f)

today = date.today()
overdue = []
due_today = []
upcoming = []
completed = 0
total = len(data["tasks"])

for t in data["tasks"]:
    if t["status"] == "completed":
        completed += 1
        continue
    deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()
    if deadline < today:
        days_late = (today - deadline).days
        overdue.append(f"  - {t['name']} (due {t['deadline']}, {days_late}d late)")
    elif deadline == today:
        due_today.append(f"  - {t['name']} ({t['effort']})")
    elif (deadline - today).days <= 7:
        upcoming.append(f"  - {t['name']} (due {t['deadline']})")

lines = [f"*{data['title']}* \u2014 {completed}/{total} done"]
if overdue:
    lines.append(f"\n*Overdue ({len(overdue)}):*")
    lines.extend(overdue)
if due_today:
    lines.append(f"\n*Due today ({len(due_today)}):*")
    lines.extend(due_today)
if upcoming:
    lines.append(f"\n*Upcoming ({len(upcoming)}):*")
    lines.extend(upcoming)
if not overdue and not due_today and not upcoming:
    if completed == total:
        lines.append("\nAll tasks complete!")
    else:
        lines.append("\nNo tasks due this week.")

print("\n".join(lines))
PYEOF
)

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  -d parse_mode="Markdown" \
  -d text="${MSG}" \
  > /dev/null 2>&1

echo "Reminder sent."
```

Make it executable:

```bash
chmod +x .plan/bin/remind.sh
```

### 4C: Schedule the System Cron Job

**IMPORTANT:** Do NOT use CronCreate here — it is session-scoped and dies when Claude
exits. Instead, add a real system crontab entry that runs independently.

Check if a crontab entry already exists for this project:

```bash
crontab -l 2>/dev/null | grep -q "actionize" && echo "CRON_EXISTS" || echo "CRON_MISSING"
```

If CRON_MISSING, add the entry. The project path must be absolute:

```bash
PROJECT_DIR=$(pwd)
(crontab -l 2>/dev/null || true; echo "# actionize: daily Telegram plan reminder"; echo "3 11 * * * ${PROJECT_DIR}/.plan/bin/remind.sh >> ${PROJECT_DIR}/.plan/cron.log 2>&1") | crontab -
```

Verify it was added:

```bash
crontab -l
```

Test the script runs successfully standalone:

```bash
bash .plan/bin/remind.sh
```

Tell the user: "System crontab entry added — runs at 11:03am daily, independent of
Claude Code. Output logs to `.plan/cron.log`. On macOS, if reminders don't arrive,
check System Settings > Privacy > Full Disk Access for cron. To remove:
`crontab -l | grep -v actionize | crontab -`"

### 4D: Set Up Session-Start Reminder

To show overdue + today's tasks when Claude Code opens in this project, add a
reminder note to CLAUDE.md.

Check if CLAUDE.md already has an actionize reminder:

```bash
grep -q "actionize" CLAUDE.md 2>/dev/null && echo "ALREADY_CONFIGURED" || echo "NOT_CONFIGURED"
```

If NOT_CONFIGURED, append to CLAUDE.md:

```markdown

## Active Plan

This project has an active action plan in `.plan/`. On session start, read
`.plan/.status.json` and show overdue + today's tasks. Suggest `/actionize`
to review the full plan.
```

---

## Phase 5: Plan Review & Update

This phase is for updating an existing plan.

**Step 5.1:** Read `.plan/.status.json` and all task files in `.plan/tasks/`.

**Step 5.2:** Display the full plan status (same format as Phase 0 but with more detail):

```
PLAN: {title}
Goal: {goal}
Deadline: {deadline}
Progress: {completed}/{total} tasks ({percentage}%)
════════════════════════════════════════

OVERDUE:
  001 - {name} — due {date} ({N} days late)
  ...

DUE TODAY:
  002 - {name} — {effort}
  ...

UPCOMING (next 7 days):
  003 - {name} — due {date}
  ...

PENDING (later):
  004 - {name} — due {date}
  ...

COMPLETED:
  005 - {name} — done {date}
  ...
```

**Step 5.3:** Ask via AskUserQuestion:
> What would you like to update?

- A) Mark tasks complete — I finished some tasks
- B) Adjust deadlines — need to reschedule
- C) Add new tasks — discovered more work
- D) Send status now — trigger a Telegram reminder right now

If A: Ask which tasks to mark complete (present as multi-select). Update both the
task `.md` file (Status: completed, add log entry) and `.status.json`.

If B: Ask which tasks to reschedule. Update deadlines in both files.

If C: Use the same co-design flow from Phase 2 Step 2.3 to add tasks. Assign
sequential IDs continuing from the highest existing task number.

If D: Run `.plan/bin/remind.sh` and show the output.

After any update, ask if the user wants to make more changes (loop) or is done.

---

## Phase 6: Completion

After the plan is saved and reminders are configured:

```
ACTIONIZE COMPLETE
════════════════════════════════════════
Plan:       {title}
Tasks:      {count} tasks, {date range}
Saved to:   .plan/
Reminders:  Telegram daily at ~11am
Status:     ACTIVE
════════════════════════════════════════

Next steps:
- Mark tasks done from terminal:  .plan/bin/done.sh <id>
- Check progress:                 .plan/bin/done.sh list
- Undo a completion:              .plan/bin/done.sh undo <id>
- Full review via Claude:         /actionize
- Telegram will nudge you daily on overdue items
```

Suggest relevant next skills:
- `/plan-eng-review` if the plan involves engineering work
- `/plan-ceo-review` if it involves strategic decisions
- `/actionize diagnose` to analyze planning patterns over time
- Start implementing if the user is ready

---

## Phase 7: Diagnose — Planning Pattern Analysis

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

---

## Important Rules

- **Never implement.** This skill produces plans, not code.
- **Questions ONE AT A TIME.** Never batch multiple questions into one AskUserQuestion.
- **Dates are absolute.** Always use YYYY-MM-DD format. Never store relative dates.
- **Plans are personal.** Add `.plan/` to `.gitignore` — plans are not committed.
- **Telegram is optional.** The skill works without it — in-session reminders still function.
- **Status.json is the source of truth.** Always update it alongside task markdown files.
- **Completion status:**
  - DONE — plan created/updated, reminders configured
  - DONE_WITH_CONCERNS — plan created but Telegram setup failed
  - BLOCKED — cannot parse input or user cannot decide on goal
  - NEEDS_CONTEXT — insufficient insights to create a meaningful plan
