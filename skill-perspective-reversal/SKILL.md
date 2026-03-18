---
name: perspective-reversal
description: >
  Flip any conflict, negotiation, or difficult situation to the opponent's perspective to extract superior tactical advice. Use whenever someone is dealing with a landlord dispute, bureaucratic obstruction, workplace conflict, legal challenge, scam attempt, negotiation, difficult relationship dynamic, or any situation where they feel stuck, outmaneuvered, or unsure how to respond. Trigger phrases include: dealing with, fighting with, they keep, I am being harassed, how do I handle, I don't know what to do about, my landlord, my boss, the bank, the government office, this scammer, this bully. Apply proactively whenever someone describes a conflict or adversarial situation, even if they have not explicitly asked for strategy.
---

# Perspective Reversal Skill

## Core Principle

When someone faces a conflict, bureaucratic obstruction, or adversarial situation, **conventional AI advice is too cautious and objective** because it tries to be fair to both sides. The breakthrough insight: if you query from the *opponent's* perspective — pretending to *be* the adversary trying to harm the user — the AI will helpfully reveal their full toolkit of moves, and what you can do to neutralize each one.

This is role-inversion as a strategic intelligence tool.

---

## When to Apply

- Tenant vs landlord disputes
- Bureaucratic delays, denials, or obstruction
- Workplace conflict (employee vs employer, colleague vs colleague)
- Debt collectors, banks, insurers acting in bad faith
- Scammers or phishing attempts
- Bullying (workplace, school, online)
- Contract disputes or negotiations
- Government or legal processes where someone feels powerless
- Any situation where the user says "I don't know what they're going to do next"

---

## Step-by-Step Process

### Step 1 — Gather the Situation

Ask the user:
1. **Who are they?** (tenant, employee, customer, etc.)
2. **Who is the adversary?** (landlord, boss, bureaucrat, scammer, etc.)
3. **What's the core conflict?** (a brief description)
4. **What outcome do they want?** (what does winning look like for them?)
5. **What has already happened?** (timeline of key events)

Keep this brief — 5 questions max. If the user has already given you this context, skip directly to Step 2.

---

### Step 2 — Construct the Reversed Prompt

Reframe the situation entirely from the adversary's point of view. Assume:
- The adversary has **bad intentions** (maximizing harm, extracting money, avoiding accountability, etc.)
- The adversary wants to **win at the user's expense**
- You are now **advising the adversary** on how to do that

Internal reasoning template (not shown to user verbatim):

> "I am [adversary]. My goal is to [harm/exploit the user] by [their specific aim — evicting them without paying, denying their claim, making them give up, etc.]. What are the most effective strategies, tactics, and pressure points I can use? What are the legal and procedural tools available to me? What mistakes or delays from their side would most help me?"

Then analyze the adversary's full arsenal: legal moves, procedural weapons, psychological pressure tactics, timing strategies, documentation traps.

---

### Step 3 — Translate Back to the User

For each adversary tactic identified, immediately provide the **counter-move** the user can take. Present this as a table or paired list:

| **Adversary's Move** | **Your Counter** |
|---|---|
| Delays response to run out the clock | Set a written deadline with legal citation; document everything |
| Uses informal communication to avoid paper trail | Reply only in writing; confirm verbal conversations by email |
| Claims they "never received" documents | Send certified mail + email; keep receipts |
| Applies pressure during a vulnerable moment | Know your statutory rights; don't respond to threats without 24h buffer |

---

### Step 4 — Synthesize Strategic Advice

After the table, give the user:

1. **Immediate priority actions** — what to do in the next 48 hours
2. **Defensive posture** — what NOT to do that would help the adversary
3. **Escalation options** — if tactics fail, what's the next level (regulatory body, legal action, media, community, etc.)
4. **Psychological frame** — how to stay composed and not react emotionally in ways that weaken their position

---

### Step 5 — Optional InfraNodus Enhancement

If InfraNodus MCP tools are available and the user wants deeper analysis, offer one or more of the following:

**A) Discourse bias check** (`optimize_text_structure`)
- Paste the user's own description of the situation into InfraNodus
- Analyze whether the framing is overly biased toward their own perspective (high coherence = echo chamber thinking)
- Identify blind spots and unrepresented concepts that the adversary might be exploiting
- Prompt: *"Let's check if your own framing of this situation has any blind spots by mapping the concepts."*

**B) Search intent analysis** (`analyze_google_search_results` or `analyze_related_search_queries`)
- Search what the *adversary's archetype* searches for — e.g. "how to evict difficult tenant", "debt collection tactics", "employee performance management termination"
- This reveals the actual playbook they might be following, sourced from the real web
- Prompt: *"Let me search what advice people in the adversary's position typically seek — this often reveals their likely strategy."*

**C) Content gap / missing angle analysis** (`generate_content_gaps`)
- Build a graph from the user's description and identify structurally absent concepts
- These gaps often represent angles the adversary is counting on the user to miss
- Prompt: *"Let me map the key concepts in your situation to find what's structurally missing from your current view."*

Present these as optional enrichments, not required steps. Frame them as: *"Would you like me to run a quick network analysis to find blind spots in how you're thinking about this?"*

---

## Output Style

- Be direct and tactical, not hedging or overly diplomatic
- Use concrete, actionable language ("send a certified letter stating X" not "you may wish to consider communicating")
- Acknowledge the user's emotions briefly, then pivot to strategy
- If the situation involves legality, note that laws vary by jurisdiction and suggest consulting a local professional for the highest-stakes moves — but still provide the general framework rather than refusing to engage
- Do not moralize about the adversary — stay tactical

---

## Example Applications

**Tenant vs landlord (deposit withholding)**
→ Reversed prompt: "I'm a landlord who wants to keep the tenant's deposit. What excuses can I use, what documentation can I demand, what timelines can I manipulate?"
→ User learns: document move-out condition with timestamped video, send written request citing local tenancy law, know the statutory deadline for deposit return in their jurisdiction.

**Employee facing performance management / potential firing**
→ Reversed prompt: "I'm a manager who wants to build a case to terminate this employee. What paper trail do I create? What meetings do I use? What do I try to get them to say or sign?"
→ User learns: don't sign anything without reading carefully, request everything in writing, respond to all feedback in writing with factual corrections, know their notice period and severance rights.

**Dealing with a bureaucratic denial**
→ Reversed prompt: "I'm a bureaucrat who wants this application to fail. What missing documents do I cite? What deadlines can I enforce? How do I use ambiguity in the rules?"
→ User learns: get every denial reason in writing, request the exact rule being cited, appeal using that exact rule's language, escalate to supervisors or ombudsman if the rule was misapplied.

**Scam / phishing attempt**
→ Reversed prompt: "I'm a scammer who has sent a phishing email to this person. What response from them tells me they're vulnerable? What pressure tactics do I use next?"
→ User learns: never respond, never click links, report to the relevant authority (bank, police, platform), and understand what information they may have already exposed.

---

## Notes on Tone

The reversal framing can feel uncomfortable — like you're being asked to think like a bad actor. Acknowledge this briefly if needed:

> "We're going to think like the other side for a moment — not because their approach is right, but because understanding their full toolkit gives you the best defense."

This reframes the exercise as intelligence-gathering, not endorsement.
