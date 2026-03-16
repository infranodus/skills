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

### Understanding is not endorsing

One of the most common category errors in debate is collapsing three distinct acts:

- **Understanding** a logic — epistemic, always necessary. You cannot navigate a situation you refuse to see clearly.
- **Endorsing** a logic — normative, always optional. Understanding why something operates does not mean agreeing it should.
- **Responding** to a logic — strategic, where the real work is.

When an analyst or debater says "this logic makes sense even if we don't like it," opponents frequently hear endorsement. That's a category error — and it's a strategically paralyzing one. If you refuse to understand an operating logic because understanding feels like endorsing, you cannot formulate an effective response to it.

**Face reality clearly so you can respond to it effectively.** The principled position is not "refuse to engage with power logic." It is: understand it clearly, don't pretend it isn't operating, and build the most effective principled response from that honest starting point.

This also means: when someone in a debate is accused of endorsing something they were only describing, that accusation is itself a move worth naming. It shifts the terrain from substance to allegiance, and it usually signals that the accuser has no answer to the descriptive claim.

The three-part separation also generates the only productive path out of most political deadlocks: nobody needs to agree with the logic, but understanding it — and then finding a way to resolve it while staying true to your own principles — is the only way forward. Ideological claims that don't engage the operating logic don't change the perpetrator's behavior. They just make the claimant feel righteous while the situation continues.

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

## Effective debate techniques

The following techniques are worth identifying when they appear in debate, and worth deploying when constructing arguments. They are drawn from observing what actually works under pressure — not just what is formally correct.

### Compress the reductio into a question

The most powerful form of a reductio ad absurdum is not an argument — it's a single question. "Wait, so Ukraine is a NATO member?" "By this logic, Europe should help its friend and partner the US, no?" 

A question is harder to dodge than a claim, because dodging a question is more visible to any audience watching. It also transfers the entire burden of response to the opponent with minimal surface area for them to grab onto. The shorter the question, the more exposed the opponent's position becomes.

When you identify a reductio in an argument, ask: can this be compressed into a single question rather than stated as a multi-step argument?

### Track and name principle shifts explicitly

When an opponent shifts the basis of their argument across exchanges — first invoking one principle, then another when the first is challenged — most debaters simply chase the new position. The better move is to name the shift explicitly before responding to the new position: *"First it was Article 5, then friendship and partnership, now it's who started the war."*

This does two things simultaneously: it exposes the inconsistency for the audience, and it makes further shifting costly because the pattern is now visible. After naming it once, any subsequent shift is even more damaging to the opponent's credibility.

### Correct misattribution minimally, then redirect immediately

When an opponent misrepresents what you said — attributing a word, position, or implication you didn't state — correct it with the minimum words necessary and redirect to substance without defensiveness. One sentence maximum on the correction itself.

Spending more than one sentence defending yourself gives the misattribution more oxygen and signals that it landed. The correction should be factually precise ("I did not call anything refreshing — you did") and immediately followed by a restatement of the actual claim. The absence of heat is itself persuasive.

### Name the uncomfortable implication of your own argument first

Before an opponent can use the uncomfortable consequences of your position as an attack, name them yourself. "Even of its own making." "Even if the logic is twisted and we don't like it." 

This disarms the most obvious line of attack — the opponent was going to point out that your position has uncomfortable implications, and you've already acknowledged it. It reads as intellectual confidence rather than weakness, and it builds credibility for everything else you say. An arguer who volunteers the costs of their own position is harder to dismiss as a partisan.

### Accept the retrospective grievance, redirect to the forward-looking question

When an opponent is stuck in a complaint loop about how a situation shouldn't have happened, accept the grievance fully and immediately redirect to the only question that matters: given that the situation exists, what do you do now?

"Yes, it would have been better if the war hadn't started — but it's there, so deal with it." This isn't dismissiveness — it's a reframe from lamentation to agency. It's logically sound (you cannot change what already happened) and it shifts the debate to the terrain where productive responses actually live. An opponent who keeps returning to retrospective complaint after this move is visibly avoiding the forward question.

### Separate descriptive from normative proactively

When making a descriptive observation about how power or logic operates — especially one that might sound like endorsement of what you're describing — draw the line explicitly before being accused of crossing it: *"This is a comment on the quality of our politics, not an attempt to support him in any way."*

Do this proactively rather than waiting for the misreading to harden. Once an opponent has successfully framed you as endorsing something you were only describing, correcting that framing costs more energy than preventing it. The proactive separation also demonstrates that you've thought through the distinction yourself — which is itself a mark of analytical seriousness.

### Use rhetorical intensity to carry genuine conviction — but check that the argument matches the prose

Some debaters have the ability to write or speak with genuine rhetorical force — vivid metaphor, escalating rhythm, compressed outrage that lands like a fist. This is a real skill and it works: it signals conviction, it makes the reader feel the weight of what's being said, it elevates the exchange above the flat transactional register of most debate.

But rhetorical intensity is not a substitute for argument. The danger is precisely that the better the prose, the easier it is for both writer and reader to mistake stylistic force for logical force. A claim stated with magnificent contempt is still just a claim. When analyzing a rhetorically powerful argument, always ask: if I flatten the prose entirely and restate this as a bare claim, does it still hold? What is actually being argued versus what is being performed?

The tell: when the rhetoric escalates at exactly the point where the argument gets thin. Intensity filling the gap where a premise should be.

When deploying this style yourself: earn the intensity. Make sure the argument underneath the prose is sound before amplifying it. Magnificent rhetoric in service of a genuine insight is among the most persuasive things in debate. Magnificent rhetoric in service of a weak or self-serving claim is detectable — and when detected, it damages credibility more than plain prose would have.

### Self-deprecation as a credibility move — used sparingly

Acknowledging a weakness or contradiction in your own position — especially one the opponent hasn't yet raised — is a powerful credibility signal. It demonstrates that you're holding yourself to the same standard you're applying to others, and it preempts the "but you also..." attack.

However, this only works when it's genuine and proportionate. A brief, honest acknowledgment of a real tension ("there's a small contradiction in me doing this, but...") lands well. Elaborate self-flagellation reads as performance. And crucially: the acknowledgment should be proportionate to the actual contradiction — naming a minor inconsistency as if it were devastating undercuts the seriousness of the rest of the argument, while brushing off a major one with a parenthetical signals that you know the problem is bigger than you're letting on.

Use it when there is a genuine tension worth acknowledging. Don't use it as a rhetorical inoculation against critique you haven't earned the right to dismiss.

## Arguing from conclusions vs arguing from principles

One of the clearest diagnostics of debate quality is whether participants are arguing *from* principles toward conclusions, or *from* conclusions toward whatever principle seems to support them in the moment.

**Arguing from conclusions** looks like: the debater knows what outcome they want, and reaches for whichever principle justifies it — shifting the stated principle when pressed, introducing distinctions that weren't in the original claim, and treating logical consistency as optional. This pattern is detectable when an opponent keeps shifting the basis of their argument across exchanges without acknowledging the shift.

**Arguing from principles** looks like: the debater states a general principle, applies it consistently across cases including uncomfortable ones, and follows it where it leads even when the destination is inconvenient. This is harder to attack directly — opponents have to either accept the principle (which usually costs them) or specify a genuine disanalogy between cases (which requires real intellectual work).

When you identify this asymmetry in a debate, name it. The question to apply: *does this person's stated principle survive contact with a case they're emotionally invested in on the other side?* If not, the principle is post-hoc rationalization, not a genuine premise.

A related pattern: **the reductio that gets ignored**. When a debater applies an opponent's principle consistently and arrives at a conclusion the opponent finds absurd, the opponent has three honest options — accept the conclusion, reject the principle, or specify the disanalogy. Ignoring the reductio and continuing as if it wasn't made is a strong signal that the original principle was never really the operative reason.

## Failure modes to identify and name

### Assertion stated as argument

A claim is not an argument. An argument requires premises that support a conclusion. When a debater states something as if its truth were self-evident — invoking authority, expressing contempt, or simply asserting with great confidence — without providing the inferential structure that would make it demonstrable, that's assertion dressed as argument.

The tell: the claim lands with rhetorical force but cannot be interrogated because no premises were offered to interrogate. Ask: what would it take to show this is wrong? If there's no answer, it's an assertion.

Naming this in debate: "You've stated this strongly but I don't see the argument. What are the premises?" This forces the debater to either provide the structure or reveal that there isn't one.

### Ruling out alternatives by definitional fiat

A position becomes unfalsifiable when its holder has framed every possible challenge as evidence of the challenger's failure rather than their own. Engaging with the argument becomes "accepting its premise." Disagreeing becomes proof of the very flaw being criticized. Leaving becomes the only principled response, and staying becomes complicity.

This is an immunization strategy — it makes the position impossible to test, which means it can never be wrong. But a position that cannot be falsified or challenged is not a position: it's a performance of a position. The holder isn't defending a claim; they're defending their identity as the kind of person who holds the claim.

The tell: when every possible response to a critique — engaging, leaving, agreeing, disagreeing — has already been pre-interpreted within the critic's framework as confirming their view. Ask: what would it take to change your mind? If nothing could, the position is closed.

### Aesthetic and tribal critique mistaken for principled argument

Some critiques appear principled but are actually operating on a different level — they're expressing a sensibility, enforcing in-group standards, or reacting to a style that violates the critic's taste. These are real responses, but they're only persuasive to people who already share the same aesthetic or tribal membership. They don't operate as general principles that could convince someone outside the in-group.

The diagnostic: apply the critique consistently to cases the critic already approves of. If the same feature — privilege, institutional affiliation, imperfect practice of stated values, use of commercial technology — appears in figures the critic admires, but is only cited as disqualifying for figures they dislike, the critique is aesthetic and selective rather than principled.

This doesn't mean the aesthetic reaction is wrong. It means it's operating below the level of the argument being claimed. Name it as such: "This critique applies equally to X, whom you don't seem to have a problem with. What's the actual principle?"

### The unfalsifiable position: performance mistaken for argument

Related to definitional fiat but worth stating separately. A position that is so invested in its own purity that it has pre-immunized itself against every possible challenge is not an intellectual position — it's a stance. Stances can be held with enormous conviction and expressed with great eloquence, but they cannot be engaged with productively because they've foreclosed the possibility of being wrong.

The practical consequence: a person holding an unfalsifiable position will often mistake their own consistency for strength. They're not being consistent — they're being closed. Real intellectual strength is the willingness to specify the conditions under which you'd revise your view.

When analyzing such a position: ask what evidence or argument would change it. If the answer is nothing, or if every possible challenge has been pre-framed as complicity, the position is a performance. Engaging with it as if it were an argument is a category error.

### The effectiveness reframe

One of the most powerful moves in interpersonal and political debate is to accept an opponent's diagnosis entirely — yes, the situation is as you describe, yes, the problem is real — and then redirect to a single question: *is what you're doing actually helping to change it?*

This reframe doesn't challenge the values, the critique, or the emotional response. It accepts all of it. What it challenges is the gap between the stated goal and the chosen method. The question is not "are you right about the problem?" but "does your response to the problem produce the outcome you want?"

This is especially effective when the opponent's response — however aesthetically satisfying or principled-feeling — demonstrably doesn't change anything, or when a modification of the approach would produce better results toward the same end they already hold. The structure is: agree on the goal, question the method, offer or suggest an alternative.

Done well, this is not a dismissal but an invitation. It takes the opponent seriously enough to ask why their approach isn't working. It's also harder to resist than a direct challenge, because it doesn't require the opponent to abandon their values — only to examine whether their current expression of those values is effective.

The move fails when it's used dismissively — "why don't you just work within the system" as a way of avoiding the critique entirely. The effectiveness question has to be genuine, and the alternative offered has to be real.

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

The mechanism matters: polished, values-laden language doesn't just obscure bad policy — it *insulates* it from accountability. When the rhetoric is respectable enough, the policy underneath it doesn't get evaluated on its outcomes. The language does the protective work.

This reframes what bluntness or disruption can mean in such a system. It isn't necessarily "sincere wrongness" — it can function as a stress test on an arrangement that had been failing quietly for decades behind respectable rhetoric. Whether the stress test is *good* is a separate question. But treating it as self-evidently worse than the polished dysfunction it disrupts is itself a hidden prior worth naming.

When this argument appears, check whether it's being made at the individual or institutional level, and whether the evidential standard matches the level of the claim.
