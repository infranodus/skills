#!/usr/bin/env bash
# Prepare diagnostic data from task history for InfraNodus analysis.
# Outputs three text blocks (planned/completed/deferred) to ~/.plan/diagnostics/
#
# Usage: diagnose-prep.sh [--project NAME]   — filter by project
#        diagnose-prep.sh                    — all projects
#        diagnose-prep.sh --stats            — just show stats, no file output

set -euo pipefail

HISTORY_FILE="$HOME/.plan/history.jsonl"
DIAG_DIR="$HOME/.plan/diagnostics"
mkdir -p "$DIAG_DIR"

PROJECT_FILTER="${2:-}"
MODE="${1:-prep}"

if [ ! -f "$HISTORY_FILE" ] || [ ! -s "$HISTORY_FILE" ]; then
  echo "No task history found. Complete some tasks first." >&2
  echo "History is logged to: $HISTORY_FILE" >&2
  exit 1
fi

python3 << PYEOF
import json, os, sys
from datetime import datetime, date
from collections import defaultdict

history_file = "$HISTORY_FILE"
diag_dir = "$DIAG_DIR"
project_filter = "$PROJECT_FILTER" or None
mode = "$MODE"
today = date.today()

# Load history
entries = []
with open(history_file) as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

if project_filter:
    entries = [e for e in entries if e.get("project") == project_filter]

if not entries:
    scope = f"project '{project_filter}'" if project_filter else "any project"
    print(f"No history entries found for {scope}.", file=sys.stderr)
    sys.exit(1)

# Group by status
planned = []
completed = []
deferred = []

for e in entries:
    name = e.get("task_name", "")
    desc = e.get("description", "")
    project = e.get("project", "unknown")
    effort = e.get("effort", "?")
    deadline = e.get("deadline", "?")
    text = f"[{project}] {name}: {desc}" if desc else f"[{project}] {name}"

    status = e.get("status", "planned")
    if status == "completed":
        completed.append(text)
    elif status == "deferred":
        deferred.append(text)
    else:
        planned.append(text)

# Stats
total = len(entries)
print(f"\nDIAGNOSTIC SUMMARY")
print(f"{'=' * 40}")
print(f"  Total entries:  {total}")
print(f"  Planned:        {len(planned)}")
print(f"  Completed:      {len(completed)}")
print(f"  Deferred:       {len(deferred)}")
if total > 0:
    completion_rate = len(completed) / total * 100
    deferral_rate = len(deferred) / total * 100
    print(f"  Completion rate: {completion_rate:.0f}%")
    print(f"  Deferral rate:   {deferral_rate:.0f}%")
print(f"{'=' * 40}\n")

if mode == "--stats":
    sys.exit(0)

# Write text blocks for InfraNodus analysis
timestamp = today.isoformat()

def write_block(filename, items, label):
    path = os.path.join(diag_dir, filename)
    with open(path, "w") as f:
        f.write(f"# {label} Tasks — {timestamp}\n\n")
        for item in items:
            f.write(item + "\n")
    print(f"  {label}: {len(items)} entries -> {path}")

if planned:
    write_block(f"{timestamp}-planned.txt", planned, "Planned")
if completed:
    write_block(f"{timestamp}-completed.txt", completed, "Completed")
if deferred:
    write_block(f"{timestamp}-deferred.txt", deferred, "Deferred")

# Also write a combined summary for longitudinal tracking
summary_path = os.path.join(diag_dir, f"{timestamp}-summary.json")
with open(summary_path, "w") as f:
    json.dump({
        "date": timestamp,
        "project_filter": project_filter,
        "total": total,
        "planned": len(planned),
        "completed": len(completed),
        "deferred": len(deferred),
        "completion_rate": len(completed) / total * 100 if total > 0 else 0,
        "deferral_rate": len(deferred) / total * 100 if total > 0 else 0,
        "planned_topics": planned[:50],
        "completed_topics": completed[:50],
        "deferred_topics": deferred[:50]
    }, f, indent=2)
    f.write("\n")
print(f"  Summary: {summary_path}")
PYEOF
