# Phase 4: Set Up Reminders

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
