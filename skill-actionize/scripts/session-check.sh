#!/usr/bin/env bash
# Session-start plan check for /actionize
# Outputs a compact summary of overdue + today's tasks if a .plan exists
# Designed to be called from a Claude Code hook or preamble

set -euo pipefail

PLAN_DIR="${1:-.plan}"
STATUS_FILE="$PLAN_DIR/.status.json"

if [ ! -f "$STATUS_FILE" ]; then
  exit 0  # No plan, nothing to show
fi

python3 << PYEOF
import json
from datetime import datetime, date

with open("$STATUS_FILE") as f:
    data = json.load(f)

if data.get("status") != "active":
    exit(0)

today = date.today()
overdue = []
due_today = []
completed = 0
total = len(data["tasks"])

for t in data["tasks"]:
    if t["status"] == "completed":
        completed += 1
        continue
    try:
        deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()
    except (ValueError, KeyError):
        continue
    if deadline < today:
        days_late = (today - deadline).days
        overdue.append(f"{t['name']} ({days_late}d late)")
    elif deadline == today:
        due_today.append(t["name"])

if not overdue and not due_today:
    exit(0)

print(f"PLAN: {data['title']} [{completed}/{total} done]")
if overdue:
    print(f"  OVERDUE: {', '.join(overdue)}")
if due_today:
    print(f"  TODAY:   {', '.join(due_today)}")
print("  Run /actionize to review and update.")
PYEOF
