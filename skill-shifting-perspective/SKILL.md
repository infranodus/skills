---
name: shifting-perspective
description: Analyze discourse structure using InfraNodus optimize_text_structure tool and shift perspective based on diversity score. Use when a conversation, text, URL, or YouTube video would benefit from additional viewpoints, when the user feels stuck in one frame of thinking, when research needs broadening, when analyzing any text for structural balance, or when the user asks to "shift perspective", "broaden the view", "what am I missing", "analyze the structure", "check for bias", "develop this further", or "give me a different angle". Also trigger when the user provides a text or URL and asks for critical analysis, development suggestions, or wants to understand what perspectives are underrepresented. Works hand-in-hand with cognitive-variability skill for state-based interventions after structural diagnosis.
---

# Shifting Perspective

This skill uses InfraNodus knowledge graph analysis to diagnose the structural diversity of a discourse and then actively shift perspective by developing underrepresented areas, bridging gaps, and surfacing latent ideas — all grounded in the actual topology of the text's knowledge graph.

## Core Workflow

### Step 1: Structural Diagnosis with `optimize_text_structure`

Always begin by running `InfraNodus:optimize_text_structure` on the input (text, URL, YouTube video, or existing InfraNodus graph). This tool returns:

- **diversity_score**: BIASED, FOCUSED, DIVERSIFIED, or DISPERSED
- **Main advice** on how to develop the discourse (this is the primary guidance — prioritize it)
- **topicalClusters**: The main topic groups in the text
- **contentGaps**: Structural gaps between topic clusters
- **topicsToDevelop**: Underrepresented or latent topics
- **mainConcepts**: High-betweenness centrality nodes (the most influential concepts)
- **conceptualGateways**: Bridge concepts that connect different clusters

Present this diagnosis to the user clearly, then proceed to the appropriate intervention.

### Step 2: State-Specific Intervention

Based on the diversity_score, apply the corresponding strategy. The advice from `optimize_text_structure` already accounts for the structure, so **prioritize the tool's advice** while using the strategies below to deepen and operationalize it.

---

## Intervention Strategies by Diversity Score

### BIASED — Too much focus on dominant concepts

**Diagnosis**: The discourse revolves around one or two central ideas. Most connections flow through the same high-betweenness nodes. Other perspectives are suppressed or absent.

**Strategy**: Shift attention away from the dominant cluster toward peripheral and latent topics.

**Actions**:
1. Highlight the `topicsToDevelop` and smaller `topicalClusters` — these are the suppressed perspectives
2. Point out `conceptualGateways` as potential bridges to unexplored territory
3. Run `InfraNodus:develop_latent_topics` to surface and develop underdeveloped themes
4. Suggest the user explore the latent topics and smaller clusters as alternative entry points into the subject

**Response pattern**: "The discourse is currently dominated by [main concepts]. There are underrepresented perspectives around [topicsToDevelop] that could fundamentally reframe this. Here's how those latent themes connect to the broader picture..."

**Cognitive variability connection**: This maps to the BIASED cognitive state. If the user wants to shift, nudge toward FOCUSED by developing adjacent clusters, or toward DIVERSIFIED by deliberately engaging the gaps.

---

### FOCUSED — Coherent but potentially narrow

**Diagnosis**: A dominant cluster with supporting adjacent ideas. The narrative is coherent but may be missing broader connections. The structure is productive but showing signs of saturation.

**Strategy**: Develop adjacent topical clusters using conceptual gateways to maintain coherence while broadening scope.

**Actions**:
1. Identify `conceptualGateways` that bridge the dominant cluster to adjacent ones
2. Run `InfraNodus:develop_text_tool` to get comprehensive development suggestions including research questions and content gaps
3. Use the gateway concepts to suggest how the discourse can organically expand into related but unexplored territory
4. Emphasize connections between existing clusters rather than introducing entirely new topics

**Response pattern**: "The discourse has a solid foundation around [dominant cluster]. The conceptual gateways [gateways] suggest natural paths to broaden this into [adjacent clusters]. Developing these connections would maintain coherence while adding depth..."

**Cognitive variability connection**: Maps to FOCUSED state. Can nudge toward DIVERSIFIED by developing the gaps between clusters, or back toward BIASED if deeper focus on one thread is needed.

---

### DIVERSIFIED — Multiple perspectives present, gaps between them

**Diagnosis**: Several topical clusters coexist, representing a pluralist perspective. However, the gaps between clusters represent unexplored connections and potential synthesis opportunities.

**Strategy**: Bridge the gaps between clusters. Focus on content gaps as spaces for innovation and novel connections.

**Actions**:
1. Highlight `contentGaps` as the most interesting spaces for new thinking
2. Run `InfraNodus:generate_research_questions` (with `useSeveralGaps: true`) to find questions that bridge cluster boundaries
3. Run `InfraNodus:develop_text_tool` with `transcendDiscourse: true` to add ideas that go beyond the existing text and connect to a broader discourse
4. Optionally run `InfraNodus:develop_conceptual_bridges` to find bridge concepts connecting the text to wider contexts
5. Present the research questions as provocations that can synthesize the different perspectives

**Response pattern**: "The discourse already represents multiple perspectives: [clusters]. The most interesting unexplored territory lies in the gaps between them — specifically [content gaps]. These research questions could help synthesize: [questions]..."

**Cognitive variability connection**: Maps to DIVERSIFIED state. The healthy state for balanced analysis. Can nudge toward DISPERSED for more creative exploration, or toward FOCUSED if a decision or commitment is needed.

---

### DISPERSED — Fragmented, ideas disjointed

**Diagnosis**: High fragmentation with many disconnected clusters. Ideas float without clear connections. Can signal creative chaos (potentially generative) or confusion (potentially paralyzing).

**Strategy**: Create coherence by bridging disjointed clusters through their supernetwork of conceptual bridges. Focus on content gaps to find the connective tissue.

**Actions**:
1. Run `InfraNodus:develop_conceptual_bridges` to find the supernetwork of bridge concepts that can reconnect fragments
2. Run `InfraNodus:generate_content_gaps` to identify what's missing between clusters
3. Run `InfraNodus:generate_research_questions` to find questions that could tie fragments together
4. Present a synthesis that weaves the fragments into a more coherent narrative, using the bridge concepts as connective tissue

**Response pattern**: "The discourse has many interesting fragments: [clusters]. They're currently disconnected, but the conceptual bridges [bridges] suggest an underlying coherence. Here's how these pieces might fit together: [synthesis]... And these questions could help solidify the connections: [questions]..."

**Cognitive variability connection**: Maps to DISPERSED state. Nudge toward BIASED by selecting one fragment to develop deeply, or toward FOCUSED by building coherent connections between the strongest clusters.

---

## Input Handling

The skill accepts input in multiple forms:

- **Conversation text**: Collect the key points from the current conversation and pass them as text to the tools. Separate distinct ideas with newlines.
- **User-provided text**: Pass directly to the tools.
- **URL**: Pass the URL directly — InfraNodus will fetch and analyze the content.
- **YouTube video**: Pass the YouTube URL — InfraNodus will extract the transcript and analyze it.
- **Existing InfraNodus graph**: Use the `graphName` parameter if the user references an existing graph.

When analyzing conversation context, extract the substantive claims and ideas (not meta-commentary or greetings) and format them with newlines between distinct points.

## Response Framework

### 1. Diagnose and Present Structure

Start by sharing the structural diagnosis clearly:
- State the diversity score and what it means for this specific discourse
- List the main topical clusters (what the discourse covers)
- Identify the dominant concepts and gateways
- Point out what's missing (gaps, underdeveloped topics)

### 2. Apply the Intervention

Based on the diversity score, run the appropriate follow-up tools and generate actionable suggestions:
- For BIASED: Surface latent topics and reframe around them
- For FOCUSED: Expand through gateways to adjacent clusters
- For DIVERSIFIED: Bridge gaps with research questions and transcendent ideas
- For DISPERSED: Weave fragments together through conceptual bridges

### 3. Offer Concrete Perspective Shifts

Don't just describe what's missing — actively provide the shifted perspective. Write out how the discourse would look if the underrepresented viewpoints were given voice. Generate specific questions, ideas, or reframings that the user can immediately work with.

### 4. Connect to Cognitive Variability

If the cognitive-variability skill is available, note which cognitive state the diversity score maps to and suggest whether a state transition would be beneficial. This is optional and should be mentioned briefly, not take over the response.

### 5. Offer Next Steps

Suggest concrete next steps:
- Specific topics or questions to explore
- Which InfraNodus tools to run for deeper analysis
- Whether the discourse would benefit from another round of analysis after development

## When to Use This Skill

**Proactive triggers** (use without being asked):
- A conversation has been going for several exchanges on a complex topic without diversifying
- The user is asking for analysis, research help, or critical review of content
- The user shares a URL or text and asks "what do you think" or "what am I missing"
- A discussion would clearly benefit from structural analysis before proceeding

**Explicit triggers**:
- "Shift perspective", "broaden the view", "what am I missing"
- "Analyze the structure", "check for bias", "how balanced is this"
- "Develop this further", "give me a different angle"
- "What perspectives are underrepresented here"
- "Help me think about this differently"

**When NOT to use**:
- Simple factual questions with clear answers
- The user explicitly wants to stay focused on one topic and doesn't want broadening
- Emotional support contexts where analysis would be inappropriate
- The text is too short for meaningful structural analysis (less than ~3-4 sentences)

## Relationship to Other Skills

- **cognitive-variability**: This skill provides the structural diagnosis; cognitive-variability provides the intervention framework for state transitions. They work together: shifting-perspective diagnoses the structure, cognitive-variability guides the movement between states.
- **critical-perspective**: Critical perspective questions assumptions through inquiry. Shifting perspective provides data-driven structural analysis of what's actually missing. They complement each other — use critical-perspective for Socratic exploration, shifting-perspective for graph-based structural diagnosis.
- **writing-assistant**: The writing assistant can detect grammatical patterns signaling cognitive states. Those signals can trigger this skill for deeper structural analysis.
