#!/usr/bin/env bash
# Send a Telegram nudge about deferred tasks, prompting user to run /actionize diagnose.
# Called by the 3-day cron job after sync.sh --all.

set -euo pipefail

HISTORY_FILE="$HOME/.plan/history.jsonl"

if [ ! -f "$HISTORY_FILE" ] || [ ! -s "$HISTORY_FILE" ]; then
  exit 0
fi

# Find any project .env with Telegram credentials
TELEGRAM_BOT_TOKEN=""
TELEGRAM_CHAT_ID=""
PROJECTS_FILE="$HOME/.plan/projects.json"

if [ -f "$PROJECTS_FILE" ]; then
  while read -r dir; do
    if [ -f "$dir/.env" ]; then
      token=$(grep "^TELEGRAM_BOT_TOKEN=" "$dir/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
      chatid=$(grep "^TELEGRAM_CHAT_ID=" "$dir/.env" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'")
      if [ -n "$token" ] && [ -n "$chatid" ]; then
        TELEGRAM_BOT_TOKEN="$token"
        TELEGRAM_CHAT_ID="$chatid"
        break
      fi
    fi
  done < <(python3 -c "
import json
with open('$PROJECTS_FILE') as f:
    for p in json.load(f):
        print(p['path'])
" 2>/dev/null)
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
  exit 0
fi

# Count deferred tasks and projects
STATS=$(python3 << PYEOF
import json
from datetime import datetime, date
from collections import defaultdict

today = date.today()
projects = defaultdict(lambda: {"deferred": 0, "completed": 0, "total": 0})

with open("$HISTORY_FILE") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        proj = e.get("project", "unknown")
        projects[proj]["total"] += 1
        if e.get("status") == "deferred":
            projects[proj]["deferred"] += 1
        elif e.get("status") == "completed":
            projects[proj]["completed"] += 1

total_deferred = sum(p["deferred"] for p in projects.values())
total_completed = sum(p["completed"] for p in projects.values())
total_all = sum(p["total"] for p in projects.values())
projects_with_deferred = sum(1 for p in projects.values() if p["deferred"] > 0)

if total_deferred == 0:
    print("NONE")
else:
    rate = total_completed / total_all * 100 if total_all > 0 else 0
    print(f"DEFERRED={total_deferred}")
    print(f"PROJECTS={projects_with_deferred}")
    print(f"RATE={rate:.0f}")
PYEOF
)

if echo "$STATS" | grep -q "NONE"; then
  exit 0
fi

DEFERRED=$(echo "$STATS" | grep "DEFERRED=" | cut -d= -f2)
PROJ_COUNT=$(echo "$STATS" | grep "PROJECTS=" | cut -d= -f2)
RATE=$(echo "$STATS" | grep "RATE=" | cut -d= -f2)

MSG="*Planning check-in*

${DEFERRED} deferred tasks across ${PROJ_COUNT} project(s)
Completion rate: ${RATE}%

Run \`/actionize diagnose\` in Claude Code for pattern analysis."

curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  -d parse_mode="Markdown" \
  -d text="${MSG}" \
  > /dev/null 2>&1
