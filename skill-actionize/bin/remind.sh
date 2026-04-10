#!/usr/bin/env bash
# Telegram reminder for /actionize plans — with escalating nudge frequency.
#
# Cron runs this 4x/day. The script decides whether to actually send based on
# how overdue tasks are:
#   1-2 days overdue  → 1 nudge/day  (morning slot only)
#   3-4 days overdue  → 2 nudges/day (morning + afternoon)
#   5-6 days overdue  → 3 nudges/day (morning + midday + afternoon)
#   7+  days overdue  → 4 nudges/day (every slot)
#   14+ days at max   → "let's reorganize" message, then stop nudging that task
#
# Escalation state is tracked in .plan/.escalation.json
#
# Usage: remind.sh           — normal cron-driven run (checks escalation)
#        remind.sh --force    — always send, ignore escalation logic
#
# Requires: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in project .env

set -euo pipefail

FORCE="${1:-}"

# Find project root
find_project_root() {
  local dir="$1"
  while [ "$dir" != "/" ]; do
    if [ -f "$dir/.plan/.status.json" ]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR=$(find_project_root "$SCRIPT_DIR") || {
  echo "Error: No .plan/.status.json found" >&2
  exit 1
}

PLAN_DIR="$PROJECT_DIR/.plan"
STATUS_FILE="$PLAN_DIR/.status.json"
ESCALATION_FILE="$PLAN_DIR/.escalation.json"

# Load Telegram credentials
if [ -f "$PROJECT_DIR/.env" ]; then
  TELEGRAM_BOT_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" "$PROJECT_DIR/.env" | cut -d= -f2- | tr -d '"' | tr -d "'")
  TELEGRAM_CHAT_ID=$(grep "^TELEGRAM_CHAT_ID=" "$PROJECT_DIR/.env" | cut -d= -f2- | tr -d '"' | tr -d "'")
fi

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in $PROJECT_DIR/.env" >&2
  exit 1
fi

if [ ! -f "$STATUS_FILE" ]; then
  echo "Error: No plan status at $STATUS_FILE" >&2
  exit 1
fi

# Main logic: escalation + message generation
RESULT=$(python3 << PYEOF
import json, os, sys
from datetime import datetime, date

status_file = "$STATUS_FILE"
escalation_file = "$ESCALATION_FILE"
force = "$FORCE" == "--force"

with open(status_file) as f:
    data = json.load(f)

today = date.today()
now = datetime.now()
hour = now.hour

# Determine which slot this is (cron runs at ~7, ~11, ~15, ~19)
# Slots: 0=morning(5-9), 1=midday(10-13), 2=afternoon(14-17), 3=evening(18-23)
if hour < 10:
    slot = 0
elif hour < 14:
    slot = 1
elif hour < 18:
    slot = 2
else:
    slot = 3

# Load escalation state
escalation = {}
if os.path.exists(escalation_file):
    try:
        with open(escalation_file) as f:
            escalation = json.load(f)
    except (json.JSONDecodeError, IOError):
        escalation = {}

# Analyze tasks
overdue_tasks = []
due_today = []
upcoming = []
completed = 0
total = len(data["tasks"])
max_days_overdue = 0
reorganize_tasks = []

for t in data["tasks"]:
    tid = str(t["id"])
    if t["status"] == "completed":
        completed += 1
        # Clear escalation for completed tasks
        if tid in escalation:
            del escalation[tid]
        continue

    try:
        deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()
    except (ValueError, KeyError):
        continue

    if deadline < today:
        days_late = (today - deadline).days
        if days_late > max_days_overdue:
            max_days_overdue = days_late

        # Initialize or update escalation tracking
        if tid not in escalation:
            escalation[tid] = {
                "first_overdue": today.isoformat(),
                "nudge_count": 0,
                "reorganize_sent": False
            }

        task_esc = escalation[tid]

        # Determine nudges/day for this task based on days overdue
        if days_late <= 2:
            nudges_per_day = 1   # morning only
        elif days_late <= 4:
            nudges_per_day = 2   # morning + afternoon
        elif days_late <= 6:
            nudges_per_day = 3   # morning + midday + afternoon
        else:
            nudges_per_day = 4   # every slot

        # Check if this slot should fire for this task's frequency
        # slots that fire: nudges=1 → [0], nudges=2 → [0,2], nudges=3 → [0,1,2], nudges=4 → [0,1,2,3]
        active_slots = {
            1: [0],
            2: [0, 2],
            3: [0, 1, 2],
            4: [0, 1, 2, 3]
        }
        should_nudge = force or (slot in active_slots.get(nudges_per_day, [0]))

        # Check for reorganize threshold: 14+ days overdue at max frequency
        if days_late >= 14 and not task_esc.get("reorganize_sent", False):
            reorganize_tasks.append(t["name"])
            task_esc["reorganize_sent"] = True

        if should_nudge:
            freq_label = f" [{nudges_per_day}x/day]" if nudges_per_day > 1 else ""
            overdue_tasks.append(f"  {t['name']} ({days_late}d late){freq_label}")
            task_esc["nudge_count"] = task_esc.get("nudge_count", 0) + 1

    elif deadline == today:
        due_today.append(f"  {t['name']} ({t.get('effort', '?')})")
    elif (deadline - today).days <= 7:
        days_left = (deadline - today).days
        upcoming.append(f"  {t['name']} ({days_left}d)")

# Save escalation state
with open(escalation_file, "w") as f:
    json.dump(escalation, f, indent=2)
    f.write("\n")

# Decide whether to send anything
if not force and not overdue_tasks and not due_today and not upcoming:
    if completed == total:
        # All done — only send once in morning slot
        if slot == 0:
            print("SEND")
            print("MSG:*" + data["title"] + "* \u2014 all tasks complete!")
        else:
            print("SKIP")
    else:
        # Nothing due this week — morning only
        if slot == 0:
            print("SEND")
            print("MSG:*" + data["title"] + "* \u2014 " + str(completed) + "/" + str(total) + " done\n\nNothing due this week.")
        else:
            print("SKIP")
    # Handle reorganize messages separately
    if reorganize_tasks:
        print("REORG:" + "|".join(reorganize_tasks))
    sys.exit(0)

if not force and not overdue_tasks and slot != 0:
    # No overdue tasks and not morning slot — only morning gets due_today/upcoming
    print("SKIP")
    sys.exit(0)

# Build the message
lines = [f"*{data['title']}* \u2014 {completed}/{total} done"]

if overdue_tasks:
    lines.append(f"\n*OVERDUE ({len(overdue_tasks)}):*")
    lines.extend(overdue_tasks)
if due_today:
    lines.append(f"\n*DUE TODAY ({len(due_today)}):*")
    lines.extend(due_today)
if upcoming and slot == 0:  # upcoming only in morning digest
    lines.append(f"\n*THIS WEEK ({len(upcoming)}):*")
    lines.extend(upcoming)

print("SEND")
print("MSG:" + "\n".join(lines))

if reorganize_tasks:
    print("REORG:" + "|".join(reorganize_tasks))
PYEOF
)

# Parse result
ACTION=$(echo "$RESULT" | head -1)

if [ "$ACTION" = "SKIP" ]; then
  echo "Skipped (not this slot's turn)."
  exit 0
fi

# Extract message
MSG=$(echo "$RESULT" | grep "^MSG:" | sed 's/^MSG://' || true)

if [ -n "$MSG" ]; then
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d parse_mode="Markdown" \
    -d text="${MSG}")

  if [ "$HTTP_CODE" = "200" ]; then
    echo "Reminder sent."
  else
    echo "Error: Telegram HTTP $HTTP_CODE" >&2
  fi
fi

# Send reorganize message if needed
REORG=$(echo "$RESULT" | grep "^REORG:" | sed 's/^REORG://' || true)

if [ -n "$REORG" ]; then
  REORG_NAMES=$(echo "$REORG" | tr '|' '\n' | sed 's/^/  - /')
  REORG_MSG="*Time to reorganize.*

These tasks have been overdue for 2+ weeks with no progress:
${REORG_NAMES}

Let's be honest \u2014 the current schedule isn't working for these. Run \`/actionize\` to reschedule or drop them."

  curl -s -o /dev/null \
    -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d parse_mode="Markdown" \
    -d text="${REORG_MSG}" 2>/dev/null

  echo "Reorganize nudge sent."
fi
