#!/usr/bin/env bash
# Mark a task as completed by ID
# Usage: .plan/bin/done.sh <task-id> [task-id ...]
# Example: .plan/bin/done.sh 3        — marks task 3 done
#          .plan/bin/done.sh 1 2 3     — marks tasks 1, 2, 3 done
#          .plan/bin/done.sh list      — show all tasks with status
#          .plan/bin/done.sh undo 3    — revert task 3 to pending

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLAN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STATUS_FILE="$PLAN_DIR/.status.json"

if [ ! -f "$STATUS_FILE" ]; then
  echo "No plan found at $STATUS_FILE" >&2
  exit 1
fi

if [ $# -eq 0 ]; then
  echo "Usage: done.sh <task-id> [task-id ...]"
  echo "       done.sh list"
  echo "       done.sh undo <task-id>"
  exit 1
fi

# List mode
if [ "$1" = "list" ]; then
  python3 << PYEOF
import json
from datetime import datetime, date

with open("$STATUS_FILE") as f:
    data = json.load(f)

today = date.today()
print(f"\n  {data['title']}  —  deadline {data['deadline']}\n")

for t in data["tasks"]:
    deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()
    if t["status"] == "completed":
        mark = "x"
    elif deadline < today:
        mark = "!"  # overdue
    else:
        mark = " "
    tag = "DONE" if t["status"] == "completed" else ("OVERDUE" if deadline < today else t["deadline"])
    print(f"  [{mark}] {t['id']:>2}. {t['name']}  ({tag})")

done = sum(1 for t in data["tasks"] if t["status"] == "completed")
total = len(data["tasks"])
print(f"\n  {done}/{total} completed\n")
PYEOF
  exit 0
fi

# Undo mode
if [ "$1" = "undo" ]; then
  shift
  if [ $# -eq 0 ]; then
    echo "Usage: done.sh undo <task-id>" >&2
    exit 1
  fi
  python3 << PYEOF
import json, sys

ids = [$(echo "$@" | sed 's/ /, /g')]
status_file = "$STATUS_FILE"

with open(status_file) as f:
    data = json.load(f)

updated = []
for t in data["tasks"]:
    if t["id"] in ids:
        t["status"] = "pending"
        updated.append(t)

with open(status_file, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

for t in updated:
    print(f"  Task {t['id']} ({t['name']}) -> pending")

# Sync markdown files
import os, re
tasks_dir = os.path.join(os.path.dirname(status_file), "tasks")
for t in updated:
    task_file = os.path.join(os.path.dirname(status_file), t["file"])
    if os.path.exists(task_file):
        content = open(task_file).read()
        content = re.sub(r"^Status:.*$", "Status: pending", content, count=1, flags=re.MULTILINE)
        open(task_file, "w").write(content)
PYEOF
  exit 0
fi

# Complete mode
python3 << PYEOF
import json, os, re
from datetime import date

ids = [$(echo "$@" | sed 's/ /, /g')]
status_file = "$STATUS_FILE"
today = date.today().isoformat()

with open(status_file) as f:
    data = json.load(f)

updated = []
for t in data["tasks"]:
    if t["id"] in ids:
        if t["status"] == "completed":
            print(f"  Task {t['id']} ({t['name']}) already done")
            continue
        t["status"] = "completed"
        updated.append(t)

with open(status_file, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

for t in updated:
    print(f"  Task {t['id']} ({t['name']}) -> completed")

    # Sync the markdown file
    task_file = os.path.join(os.path.dirname(status_file), t["file"])
    if os.path.exists(task_file):
        content = open(task_file).read()
        content = re.sub(r"^Status:.*$", "Status: completed", content, count=1, flags=re.MULTILINE)
        if f"- {today}: Completed" not in content:
            content = content.rstrip() + f"\n- {today}: Completed\n"
        open(task_file, "w").write(content)

done = sum(1 for t in data["tasks"] if t["status"] == "completed")
total = len(data["tasks"])
print(f"\n  {done}/{total} completed")

# Log to user-wide history
import pathlib
from datetime import datetime
history_file = pathlib.Path.home() / ".plan" / "history.jsonl"
history_file.parent.mkdir(parents=True, exist_ok=True)
project_name = pathlib.Path("$PLAN_DIR").parent.name
now = datetime.now().isoformat()
with open(history_file, "a") as hf:
    for t in updated:
        desc = ""
        task_file = os.path.join(os.path.dirname(status_file), t["file"])
        if os.path.exists(task_file):
            content = open(task_file).read()
            import re as re2
            dm = re2.search(r"## Description\n(.+?)(?=\n##|\Z)", content, re2.DOTALL)
            if dm:
                desc = dm.group(1).strip()
        entry = {
            "project": project_name, "task_id": t["id"],
            "task_name": t["name"], "description": desc,
            "status": "completed", "deadline": t["deadline"],
            "effort": t.get("effort", "?"), "timestamp": now,
            "plan_title": data.get("title", "")
        }
        hf.write(json.dumps(entry) + "\n")
PYEOF
