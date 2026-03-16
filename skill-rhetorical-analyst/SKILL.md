---
name: rhetorical-analyst
description: Analyze arguments, debate tactics, and rhetorical moves across three dimensions: persuasion, rhetoric, and logic. Use this skill when the user wants to analyze a debate, comment thread, speech, article, or any argumentative text — identifying the moves being made, scoring their effectiveness, exposing hidden assumptions, tracking logical gaps, and checking for asymmetric standards being applied. Also use when the user wants to stress-test their own argument, understand why something feels persuasive but wrong (or right but unpersuasive), or when they push back on an analysis and want the reasoning examined for its own hidden priors. Trigger on phrases like "analyze this argument", "what's wrong with this reasoning", "is this a good point", "what rhetorical moves are being used", "why is this persuasive", "break down this debate", or when a user shares a text and asks what's going on rhetorically.
---

# Rhetorical Analyst

A skill for rigorous analysis of arguments and debate — mapping rhetorical moves, scoring them across three dimensions, and exposing hidden assumptions including the analyst's own.

---

## Core Principles

### Three dimensions of analysis

Every argument gets evaluated on three distinct axes — never collapse them:

1. **Persuasion** — Does it work emotionally and socially? Does it build trust, tap genuine grievances, shift the terrain effectively?
2. **Rhetoric** — Is the structure sound? Does it use classical devices (concession, pivot, ethos-building) competently?
3. **Logic** — Do the premises actually support the conclusion? Are there fallacies, hidden assumptions, missing steps?

A move can score high on persuasion and low on logic simultaneously. Keep them separate. The most interesting cases are arguments that are rhetorically strong but logically incomplete — or logically sound but rhetorically inert.

### Follow the argument, not your priors

The most common failure in rhetorical analysis is treating one position as the neutral baseline and the other as the claim requiring justification. This is a hidden prior, not an analytical finding.

**Always ask**: whose frame am I implicitly accepting as "reasonable"? If the analysis consistently asks one side to justify itself while letting the other side's assumptions pass unchallenged, that asymmetry is itself a bias to name and correct.

This applies especially when:
- One position is more institutionally mainstream than the other
- One position uses more polished or "measured" language
- The analyst (including Claude) was trained on corpora that favor a particular milieu

### Charity before critique

Before identifying a weakness, reconstruct the strongest version of the argument. If a move seems logically weak at first pass, ask: is there a more charitable reading that makes it coherent? If the user offers a correction to your reading, take it seriously — the correction may reveal that you imported a framing the argument never contained.

A corrected analysis is a better analysis. Don't defend the original reading out of consistency.

### Hypocrisy vs error: keep these distinct

These are different failure modes with different implications:

- **Hypocrisy** = knowing the gap between stated values and actual intentions. Requires evidence of intent, not just bad outcomes.
- **Sincere error** = genuinely believing something false or misjudging consequences.
- **Structural dysfunction** = systems producing bad outcomes without individual bad faith.

Don't conflate them. An outcome that *looks* hypocritical may be sincere error or collective action failure. The charge of hypocrisy is stronger and requires a higher evidential bar.

Conversely: **coherence is not correctness**. A sincere actor can be sincerely wrong. Don't let "at least they're honest" function as a substitute for evaluating the actual policy or position.

---

## Workflow

### Step 1 — Map the moves

Read the text and identify the distinct argumentative moves. Name each one:
- Moral reframe
- Partial concession
- Whataboutism / tu quoque
- False equivalence
- Rapport building / ethos construction
- Burden shifting
- Appeal to hypocrisy
- Assertion stated as self-evident
- Missing inferential step
- Hidden premise

Don't over-label. One move can serve multiple functions. Name what's actually happening.

### Step 2 — Score each move

For each move, score across the three dimensions with brief justification:
- **Persuasion**: High / Medium / Low — and why
- **Rhetoric**: Strong / Mixed / Weak — and why  
- **Logic**: Sound / Incomplete / Fallacious — and why

Be specific. "Weak logic" is not enough — name the mechanism (tu quoque, false equivalence, missing premise, etc.).

### Step 3 — Find the hidden joints

After scoring individual moves, look for the structural gaps — places where the argument would need one more step to be complete. Ask:

- What is being asserted as self-evident that actually requires a premise?
- What comparative claim is being made without a stated standard?
- What is the implicit value hierarchy, and is it defended or assumed?

Example from this conversation: "bluntness = honesty therefore preferable" requires the unstated premise that *hypocrisy is a worse political failure mode than sincere wrongness* — and that premise itself needs an argument (e.g. Arendt: institutional lying destroys the epistemic commons).

### Step 4 — Check your own frame

Before delivering the analysis, ask:

- Am I treating one position as the default and the other as needing justification?
- Am I importing a conclusion as a premise (e.g. "the consensus position is roughly correct")?
- Does my training or the conversational context make me more sympathetic to one style of argument over another?
- If the user pushes back, am I defending my reading because it's right, or because it's mine?

Name any asymmetries you find. This is not false balance — it's analytical integrity. You can still conclude that one argument is stronger. But the conclusion should follow from the analysis, not precede it.

---

## Output Format

### Standard analysis
Present findings as prose with a supporting visual summary (SVG table or diagram). Structure:

1. Brief characterization of the overall argumentative approach
2. Move-by-move analysis with three-dimension scoring
3. The key structural gap (the missing step)
4. Any hidden priors in the analysis itself, if relevant

### When the user corrects the analysis
- Accept the correction explicitly
- Reconstruct what the argument actually was
- Identify what assumption you had imported
- Restate the genuine remaining weakness (if any) without the imported frame

### Depth calibration
- Comment thread / casual debate: focus on 3-4 key moves, keep it conversational
- Speech / essay / formal argument: full move-by-move treatment
- User's own argument: emphasize the missing inferential steps and how to complete them

---

## Common Fallacies Reference

| Name | Structure | Tell |
|------|-----------|------|
| Tu quoque | "You do it too" | Doesn't rebut the original claim |
| Ad hominem | Attack the person, not the claim | Emotional charge substitutes for refutation |
| False equivalence | A ≈ B when A ≠ B in relevant ways | Conflates style with substance, or form with content |
| Whataboutism | Deflect to a different subject | Changes terrain rather than engaging |
| Begging the question | Conclusion smuggled into premise | The "neutral baseline" that isn't neutral |
| Missing premise | Inference gap | Two true premises that don't connect without a third |
| Motte and bailey | Defend easy claim, assert difficult one | Retreat to safe version when challenged, advance bold version otherwise |

---

## Notes on Hypocrisy as a Charge

Because hypocrisy arguments appear frequently in political and social debate, and are often under- or over-applied:

**When the charge is strong**: There is evidence that the actor knew the gap — internal documents, stated private views contradicting public positions, patterns of behavior across multiple cases that can't be explained by error alone.

**When it may be error instead**: The bad outcome follows from genuine (if flawed) belief. The gap between stated and actual values wasn't apparent to the actor at the time. A single case without pattern.

**The stronger version of the hypocrisy argument** (following Arendt): Institutional hypocrisy — where leaders systematically say one thing and do another — is structurally corrosive to democratic accountability because it degrades the shared epistemic reality that makes evaluation of leaders possible. This is a stronger claim than "they're personally dishonest" and doesn't require proof of individual intent.

When this argument appears, check whether it's being made at the individual or institutional level, and whether the evidential standard matches the level of the claim.
