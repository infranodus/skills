#!/usr/bin/env bash
# Sync project task states to the user-wide history log at ~/.plan/history.jsonl
# Detects deferred tasks (past deadline, not completed) and logs all states.
#
# Usage: sync.sh [project-dir]    — sync a specific project
#        sync.sh --all            — scan all known projects
#        sync.sh                  — sync current directory

set -euo pipefail

HISTORY_FILE="$HOME/.plan/history.jsonl"
PROJECTS_FILE="$HOME/.plan/projects.json"
mkdir -p "$HOME/.plan"

# Register a project in the known projects list
register_project() {
  local dir="$1"
  local name
  name=$(basename "$dir")
  if [ ! -f "$PROJECTS_FILE" ]; then
    echo "[]" > "$PROJECTS_FILE"
  fi
  python3 << PYEOF
import json
pf = "$PROJECTS_FILE"
with open(pf) as f:
    projects = json.load(f)
entry = {"path": "$dir", "name": "$name"}
if not any(p["path"] == "$dir" for p in projects):
    projects.append(entry)
    with open(pf, "w") as f:
        json.dump(projects, f, indent=2)
        f.write("\n")
    print(f"Registered project: $name")
else:
    print(f"Project already registered: $name")
PYEOF
}

# Sync one project directory
sync_project() {
  local project_dir="$1"
  local status_file="$project_dir/.plan/.status.json"

  if [ ! -f "$status_file" ]; then
    return 0
  fi

  register_project "$project_dir"

  python3 << PYEOF
import json
from datetime import datetime, date

status_file = "$status_file"
history_file = "$HISTORY_FILE"
project_dir = "$project_dir"
project_name = "$(basename "$project_dir")"
today = date.today()
now = datetime.now().isoformat()

with open(status_file) as f:
    data = json.load(f)

# Load existing history to avoid duplicates
existing = set()
try:
    with open(history_file) as f:
        for line in f:
            line = line.strip()
            if line:
                entry = json.loads(line)
                existing.add((entry.get("project"), entry.get("task_id"), entry.get("status")))
except FileNotFoundError:
    pass

new_entries = []
for t in data["tasks"]:
    deadline = datetime.strptime(t["deadline"], "%Y-%m-%d").date()

    # Determine effective status
    if t["status"] == "completed":
        effective = "completed"
    elif deadline < today and t["status"] != "completed":
        effective = "deferred"
    else:
        effective = "planned"

    key = (project_name, t["id"], effective)
    if key not in existing:
        entry = {
            "project": project_name,
            "task_id": t["id"],
            "task_name": t["name"],
            "description": "",
            "status": effective,
            "deadline": t["deadline"],
            "effort": t.get("effort", "?"),
            "timestamp": now,
            "plan_title": data.get("title", "")
        }

        # Try to read description from task markdown file
        import os
        task_file = os.path.join(os.path.dirname(status_file), t.get("file", ""))
        if os.path.exists(task_file):
            content = open(task_file).read()
            # Extract description section
            import re
            desc_match = re.search(r"## Description\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if desc_match:
                entry["description"] = desc_match.group(1).strip()

        new_entries.append(entry)

if new_entries:
    with open(history_file, "a") as f:
        for entry in new_entries:
            f.write(json.dumps(entry) + "\n")
    print(f"  {project_name}: {len(new_entries)} new entries logged")
else:
    print(f"  {project_name}: up to date")
PYEOF
}

# Main
if [ "${1:-}" = "--all" ]; then
  if [ -f "$PROJECTS_FILE" ]; then
    python3 -c "
import json
with open('$PROJECTS_FILE') as f:
    for p in json.load(f):
        print(p['path'])
" | while read -r dir; do
      if [ -d "$dir/.plan" ]; then
        sync_project "$dir"
      fi
    done
  else
    echo "No projects registered yet."
  fi
elif [ -n "${1:-}" ]; then
  sync_project "$1"
else
  sync_project "$(pwd)"
fi
