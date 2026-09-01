---
name: actionize
description: |-
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
metadata:
  version: "1.0.0"
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

## Requirements

- `python3`, `curl`, and `crontab` on the host. Cron scheduling does not work in
  containers or WSL without a running cron daemon: if `command -v crontab` fails,
  warn the user and offer the manual-reminder alternative (run
  `.plan/bin/remind.sh` by hand, or from Phase 5 option D) instead of a crontab entry.
- A Telegram bot token and chat id for reminders — see Phase 4 and
  [Reminders setup](references/reminders-setup.md). Telegram is optional.
- `${CLAUDE_SKILL_DIR}` in the commands below is substituted by Claude Code with the
  skill's directory; in other clients substitute the skill's install path by hand.

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

### Session start

`bin/session-check.sh` is a compact, non-interactive version of the check above.
It takes an optional plan directory argument (default `.plan`); if
`.plan/.status.json` is missing, the plan is not `active`, or nothing is overdue or
due today, it exits 0 silently. Otherwise it prints one `PLAN: {title} [{done}/{total} done]`
line plus `OVERDUE:` and `TODAY:` lines and a hint to run `/actionize`. Use it from a
Claude Code SessionStart hook or as the Phase 0 preamble command:

```bash
bash "${CLAUDE_SKILL_DIR}/bin/session-check.sh" .plan
```

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

Summary of the steps (exact commands, prompts, and the reminder script are in the reference):

1. **Telegram bot (4A):** check `.env` for `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. If missing, guide the user through creating a bot with @BotFather, have them message the bot once, detect the chat id via `getUpdates`, save both to `.env`, and send a test message. Telegram is optional — the user may skip it.
2. **Reminder script (4B):** `mkdir -p .plan/bin`, then copy `${CLAUDE_SKILL_DIR}/bin/remind.sh` to `.plan/bin/remind.sh` and `chmod +x` it (the reference also shows the script inline).
3. **System cron (4C):** do NOT use CronCreate (session-scoped). Add a real crontab entry that runs `.plan/bin/remind.sh` daily, logging to `.plan/cron.log`. Test with `bash .plan/bin/remind.sh`.
4. **Session-start note (4D):** append an "Active Plan" section to CLAUDE.md if not already present.
5. **Diagnose cron:** optionally add the 3-day sync + nudge crontab entry from Phase 8.

See [Reminders setup](references/reminders-setup.md).

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

Triggered by `/actionize diagnose` or when the user asks to analyze their planning
patterns. Runs project-wide or user-wide. Summary of the steps:

1. Sync task states to `~/.plan/history.jsonl`: `"${CLAUDE_SKILL_DIR}/bin/sync.sh"` (add `--all` for user-wide).
2. Prepare data: `"${CLAUDE_SKILL_DIR}/bin/diagnose-prep.sh"` (optionally `--project "ProjectName"`) writes `~/.plan/diagnostics/{date}-{planned,completed,deferred}.txt` and `{date}-summary.json`.
3. Ask the scope via AskUserQuestion (this project / all projects / compare projects).
4. Run `mcp__infranodus__generate_topical_clusters` on each of the planned, completed, and deferred texts, then `mcp__infranodus__difference_between_texts` for planned-vs-completed and deferred-vs-completed.
5. Compare with previous `~/.plan/diagnostics/*-report.md`, save `{date}-report.md`, deliver the insights, and ask whether to adjust the current plan.

See [Diagnose](references/diagnose.md) for the full procedure, tool parameters, report template, and delivery format.

---

## Phase 8: Diagnose Cron — Automated Sync + Nudge

During Phase 4, also add a 3-day crontab entry (tagged `actionize-diagnose`) that runs
`${CLAUDE_SKILL_DIR}/bin/sync.sh --all` and then `${CLAUDE_SKILL_DIR}/bin/diagnose-nudge.sh`,
which sends a short Telegram message nudging the user to run `/actionize diagnose`.

See [Diagnose](references/diagnose.md#phase-8-diagnose-cron--automated-sync--nudge) for the check and install commands.

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
