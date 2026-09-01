# Graph-to-Script Pipeline (InfraNodus MCP)

A knowledge graph of your topic is the **source material** for your script's tension architecture. Instead of inventing curiosity loops from intuition, extract them directly from the graph's structure.

### Why This Matters

A knowledge graph of any topic reveals clusters (what's well-covered) and structural gaps (what's missing between clusters). These gaps are not just SEO opportunities — they are **ready-made curiosity loops**. When a viewer senses a gap between two things they thought were connected, that's inherent tension. The graph gives you this for free.

### The Process: Topic Graph → Script Stages

#### Step 1: Build the Topic Graph

Before scripting, analyze your video's topic using InfraNodus to map its knowledge structure.

```
Tool: InfraNodus:analyze_text
- Input: your draft notes, transcript, or topic description
- Output: topical clusters and structural gaps in your topic
```

Or if working from existing content:
```
Tool: InfraNodus:analyze_text (with url parameter)
- Input: a key reference URL or YouTube video on the topic
- Output: how the existing discourse is structured
```

#### Step 2: Extract Structural Gaps

```
Tool: InfraNodus:generate_content_gaps
- Input: the same text or URL
- Output: gaps between topical clusters — these are the missing connections
```

Each gap is a pair of clusters that should be connected but aren't. These are your script's raw material.

#### Step 3: Generate Curiosity Loops from Gaps

```
Tool: InfraNodus:generate_research_questions
- Input: same text/URL
- Output: questions that bridge the structural gaps
```

These research questions are **pre-built curiosity loops**. Each one identifies something the audience senses should be explained but hasn't been.

#### Step 4: Transcend the Topic for Escalation

```
Tool: InfraNodus:develop_conceptual_bridges
- Input: same text/URL
- requestMode: "transcend"
- Output: ideas that go beyond the text and connect to broader discourse
```

The transcend output gives you **escalation material** — it shows how your niche topic connects to bigger, universal themes. This is what turns "here's a feature" into "here's why this changes everything."

#### Step 5: Develop Latent Topics for the Payoff

```
Tool: InfraNodus:develop_latent_topics
- Input: same text/URL
- requestMode: "transcend"
- Output: underdeveloped topics that deserve deeper exploration
```

Latent topics are insights hiding beneath the surface of your topic. These become your **payoff** — the moment the viewer gets something they couldn't get anywhere else.

### Mapping Graph Output → Script Stages

| Graph Analysis Output | Script Stage It Feeds |
|---|---|
| **Main topical clusters** | Framing — what the topic is about at a high level |
| **Structural gaps between clusters** | Curiosity Loop — "There's a hidden connection between X and Y that nobody talks about" |
| **Research questions from gaps** | Hook — frame as a compelling question the viewer needs answered |
| **Transcend / conceptual bridges** | Escalation — "This isn't just about [niche] — it's about [universal theme]" |
| **Latent / underdeveloped topics** | Payoff — the original insight that resolves the loop |
| **Overlap between your topic and trending discourse** | Pattern Interrupt — unexpected connection that stops scrolling |

### Example: Graph-to-Script for a Fitness Channel

**Topic**: "Why people plateau after 3 months of training"

**Step 1-2**: Analyze training plateau content → Graph shows clusters: {progressive overload, rep ranges, nutrition} and {recovery, sleep, stress management} with a **structural gap** between them.

**Step 3**: Research questions from gap → "Why does the same program that builds initial strength become the barrier to further progress?"

**Step 4**: Transcend → connects to broader discourse about adaptation, diminishing returns in any skill domain, and the psychology of habit vs growth.

**Step 5**: Latent topics → "neurological adaptation plateaus vs muscular — the hidden bottleneck most trainers ignore."

**Resulting script mapping**:
- **Pattern Interrupt**: "Your workout is working against you. And you can't feel it happening."
- **Hook**: "What if the thing that got you here is exactly what's holding you back?"
- **Framing**: "If you train consistently but stopped seeing results — this explains everything."
- **Curiosity Loop**: "There's a structural reason your body stops responding after 3 months." ← from the gap
- **Escalation**: "It's the same pattern behind every plateau in every skill — not just fitness." ← from transcend
- **Payoff**: "Your muscles adapted weeks ago. It's your nervous system that's stuck. And no amount of 'more reps' fixes that." ← from latent topics
- **Relevance Bridge**: "So you need to train the signal, not just the muscle. Here's how to restructure your program."

## SEO-to-Script Mapping

The SEO research phase (search intent, content gaps, demand vs supply) should directly feed the script structure — not just the title and thumbnail.

### Connecting SEO Findings to Script Stages

When you run the SEO workflow (Steps 1-4 from the SEO-Driven Title Strategy), capture the outputs and map them:

| SEO Finding | Script Stage |
|---|---|
| **High-demand search cluster** (what people want) | Hook — promise value in the exact language searchers use |
| **Content gap** (demand exists, supply is thin) | Curiosity Loop — "Nobody's explaining why [gap topic] actually works" |
| **Saturated topic** (what already exists everywhere) | Pattern Interrupt — "Everyone says [saturated take]. They're wrong." |
| **Demand vs supply difference** (what's searched but not answered) | Payoff — deliver the answer that doesn't exist yet |
| **Related queries people also search** | Escalation — "And it gets bigger: [related query] is the same problem" |
| **Underserved keyword with high intent** | Relevance Bridge — "If you've been searching for [keyword], here's what you actually need" |

### SEO-to-Script Workflow

```
1. Run InfraNodus:analyze_related_search_queries → capture demand clusters
2. Run InfraNodus:analyze_google_search_results → capture supply clusters
3. Run InfraNodus:search_queries_vs_search_results → capture the gaps
4. For each gap:
   a. The gap topic becomes the CURIOSITY LOOP
   b. The demand language becomes the HOOK phrasing
   c. The saturated existing content becomes the PATTERN INTERRUPT target ("everyone says X...")
   d. Your unique answer to the gap becomes the PAYOFF
   e. Related unfilled queries become ESCALATION material
```

### Example: SEO-to-Script for "Home Coffee Brewing"

**SEO research reveals**:
- Demand cluster: "how to make coffee taste better at home", "coffee shop quality at home", "why does my coffee taste bitter"
- Supply: Hundreds of "pour-over tutorial" and "best coffee maker" videos
- Gap: "diagnosing why your coffee tastes bad" — high demand, almost no supply
- Related queries: "coffee grind size chart", "water temperature for coffee", "coffee to water ratio"

**Script mapping**:
- **Pattern Interrupt**: "You don't need a better coffee maker. You need to fix this one mistake." ← attacks the saturated supply
- **Hook**: "The reason your coffee tastes bitter has nothing to do with the beans." ← uses demand language
- **Curiosity Loop**: "There's a simple chemistry reason nobody explains — and it's not the water temperature." ← gap topic
- **Escalation**: "The same mistake ruins pour-over, French press, and espresso." ← related queries
- **Payoff**: "It's extraction time. Too long = bitter. Too short = sour. And your grind size is the control dial." ← your unique answer
- **Relevance Bridge**: "Whether you use a $20 French press or a $500 machine — mastering extraction is what separates good coffee from great."

## Differentiator-Informed Keyword Strategy

Don't just pick popular keywords. Use your channel's unique angle to **select which keywords to pursue** in the first place.

### The Principle

Traditional keyword selection optimizes for volume and competition. Differentiator-informed selection adds a third dimension: **structural novelty potential**. A keyword is worth pursuing when:
1. There's search demand (volume)
2. Competition is manageable
3. **Your unique expertise or angle can fill a gap that generic competitors can't**

### The Process

#### Step 1: Graph the Keyword Landscape

```
Tool: InfraNodus:analyze_related_search_queries
- Input: your broad topic area (e.g., "home fitness equipment")
- Output: graph of search demand with topical clusters
```

#### Step 2: Graph the Supply Landscape

```
Tool: InfraNodus:analyze_google_search_results
- Input: same keywords
- Output: graph of what exists in search results
```

#### Step 3: Find Structural Novelty Gaps

```
Tool: InfraNodus:search_queries_vs_search_results
- Input: same keywords
- Output: gaps between what people want and what exists
```

Now look at the gaps through your differentiator lens:
- **Which gaps align with your unique expertise?** → These are your strongest opportunities
- **Which gaps are about generic information anyone can provide?** → These are weaker — no differentiation

#### Step 4: Validate with Topic Graph Analysis

For your top candidate keywords, run:
```
Tool: InfraNodus:generate_content_gaps
- Input: text from top-ranking content for that keyword
- Output: what even the best existing content is missing
```

If the gap in existing content aligns with **your differentiator** (your unique perspective, method, or expertise), this is a high-value keyword. If the gap is just missing facts anyone could provide, it's lower value.

### Keyword Scoring

Rate each keyword opportunity:

| Factor | Score | Meaning |
|---|---|---|
| Search demand | High/Med/Low | Do people search for this? |
| Competition | High/Med/Low | How saturated is the supply? |
| **Structural gap potential** | High/Med/Low | Does the existing content miss something your angle reveals? |
| **Differentiator fit** | High/Med/Low | Can you uniquely fill this gap with your expertise? |

**Prioritize keywords where structural gap potential AND differentiator fit are both High** — these are topics where your content will be genuinely different, not just another take.

### Example: Keyword Selection for a Personal Finance Channel

Differentiator: "Behavioral psychology behind money decisions"

| Keyword | Demand | Competition | Structural Gap | Differentiator Fit | **Priority** |
|---|---|---|---|---|---|
| "best savings accounts" | High | High | Low (just rate lists) | Low | **Skip** |
| "how to budget" | High | High | Med (process gaps) | Med | **Maybe** |
| "why I can't save money" | Med | Low | High (no one explains the psychology) | High | **Top pick** |
| "investment apps review" | High | High | Low (comparison content) | Low | **Skip** |

"Why I can't save money" wins not because it has the highest volume, but because the structural gap is exactly what the behavioral psychology differentiator fills.
