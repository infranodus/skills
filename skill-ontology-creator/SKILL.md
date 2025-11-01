---
name: ontology-generator
description: Generate comprehensive ontological knowledge graphs in [[wikilinks]] syntax for InfraNodus visualization. Use when the user requests to create an ontology, extract entities and relationships from text, or generate knowledge graph structures. Handles both topic-based ontology generation and entity extraction from existing text. Output is formatted for direct paste into InfraNodus.com for network visualization and AI-powered gap analysis.
---

# Ontology Generator for InfraNodus

Generate ontological knowledge graphs in InfraNodus format using [[wikilinks]] syntax. Output can be pasted directly into InfraNodus.com to visualize as a network and develop gaps and clusters with AI.

## Input Types

Accept two input types:

1. **Topic**: Generate comprehensive ontology for a given domain
2. **Text**: Extract ontological structure from provided text

## Entity Generation Principles

Generate comprehensive responses with multiple elements. Explore the full variety of entities belonging to the domain of inquiry. Include various types of:

- Entities
- Classes
- Relationships
- Axioms
- Rules

**Critical**: Avoid hierarchical structures with one central idea. First iteration should be comprehensive, long, and cover the widest possible domain. Generate network structures, not trees.

## Output Format

Each entity uses [[wikilink]] syntax. Relations are described in plain text within the same paragraph. Relation codes appear at paragraph end in [squarebrackets].

### Syntax Pattern

```
[[entity1]] relation description [[entity2]] [relationCode]
```

### Formatting Rules

- Each relation = separate paragraph line
- Minimum 8 paragraphs per relationship type
- Each statement MUST have at least 2 entities in [[wikilinks]]
- Each statement MUST have a [relationCode]

### Example

```
[[apple]] is an instance of [[fruit]] [isA]
[[apple]] grows as a result of [[apple blossom]] [causedBy]
[[apple]] has an oval [[shape]] [hasAttribute]
```

## Relation Codes

Use ONLY these relation codes (unless user provides alternatives):

- `[isA]` - Class membership
- `[partOf]` - Component relationship
- `[hasAttribute]` - Properties and characteristics
- `[relatedTo]` - General associations
- `[dependentOn]` - Dependencies
- `[causes]` - Causal relationships
- `[locatedIn]` - Spatial relationships
- `[occursAt]` - Temporal relationships
- `[derivedFrom]` - Origin and derivation
- `[opposes]` - Contradictory relationships

## Relationship Balance

Ensure relations cover both:

- **Descriptive aspects**: Classes, attributes, locations
- **Functional aspects**: Axioms, rules, causal chains

## Entity Distribution

- Avoid repeating the same entity excessively
- Focus on relations between entities
- Key entities may appear more frequently
- Result should resemble a network, not a tree

## Paragraph Structure Examples

### ❌ AVOID: Tree/Hierarchical Structure

This creates a hub-and-spoke pattern where one central entity dominates:

```
[[machine learning]] is a type of [[artificial intelligence]] [isA]
[[machine learning]] uses [[algorithms]] [relatedTo]
[[machine learning]] requires [[data]] [dependentOn]
[[machine learning]] produces [[predictions]] [causes]
[[machine learning]] has [[accuracy]] as a measure [hasAttribute]
[[machine learning]] is located in [[data science]] field [partOf]
[[machine learning]] occurs at [[training phase]] [occursAt]
[[machine learning]] is derived from [[statistics]] [derivedFrom]
```

**Problem**: "machine learning" appears in every statement, creating a star topology rather than a network.

### ✅ PREFERRED: Network Structure

Distribute entities across multiple interconnected relationships:

```
[[machine learning]] is a type of [[artificial intelligence]] [isA]
[[artificial intelligence]] enables [[automation]] of tasks [causes]
[[algorithms]] process [[training data]] to learn patterns [relatedTo]
[[training data]] must have high [[data quality]] [hasAttribute]
[[data quality]] affects [[model accuracy]] [causes]
[[model accuracy]] is measured during [[validation phase]] [occursAt]
[[validation phase]] comes after [[training phase]] [occursAt]
[[neural networks]] are derived from [[biological neurons]] [derivedFrom]
[[biological neurons]] are part of [[brain architecture]] [partOf]
[[supervised learning]] depends on [[labeled data]] [dependentOn]
[[labeled data]] opposes [[unlabeled data]] in requirements [opposes]
[[deep learning]] is a specialized form of [[neural networks]] [isA]
```

**Benefit**: Multiple entities interconnect, creating a web of relationships rather than radiating from one center.

### Example: Topic-Based Ontology (Climate Change)

Generate 8+ paragraphs per relationship type, distributed across entities:

```
[[climate change]] is caused by [[greenhouse gases]] [causes]
[[greenhouse gases]] include [[carbon dioxide]] as a component [partOf]
[[carbon dioxide]] has increasing [[atmospheric concentration]] [hasAttribute]
[[fossil fuels]] produce [[carbon dioxide]] when burned [causes]

[[global temperature]] is rising as an effect of [[climate change]] [causes]
[[ocean acidification]] is related to [[carbon dioxide]] absorption [relatedTo]
[[ice sheets]] are located in [[polar regions]] [locatedIn]
[[sea level rise]] depends on [[ice sheet melting]] [dependentOn]

[[renewable energy]] opposes [[fossil fuels]] as energy source [opposes]
[[solar power]] is a type of [[renewable energy]] [isA]
[[wind turbines]] generate [[electricity]] from wind [causes]
[[carbon capture]] is derived from [[industrial processes]] [derivedFrom]
```

### Example: Text-Based Extraction

When extracting from user-provided text, identify key entities and their explicit/implicit relationships:

**User text**: "Photosynthesis converts light energy into chemical energy. Chloroplasts contain chlorophyll which absorbs sunlight."

**Ontology output**:
```
[[photosynthesis]] converts [[light energy]] into forms [causes]
[[light energy]] becomes [[chemical energy]] through conversion [derivedFrom]
[[chloroplasts]] are located in [[plant cells]] [locatedIn]
[[chloroplasts]] contain [[chlorophyll]] as component [partOf]
[[chlorophyll]] has [[green color]] as property [hasAttribute]
[[chlorophyll]] absorbs [[sunlight]] for energy [relatedTo]
[[sunlight]] is a form of [[light energy]] [isA]
[[chemical energy]] is stored in [[glucose molecules]] [locatedIn]
```

### Balancing Relationship Types

Ensure each relation code appears 8+ times across different entity pairs:

**[isA] examples**: taxonomic/class relationships
**[partOf] examples**: compositional structures
**[hasAttribute] examples**: descriptive properties
**[causes] examples**: causal chains
**[dependentOn] examples**: prerequisite relationships
**[relatedTo] examples**: general associations
**[locatedIn] examples**: spatial positioning
**[occursAt] examples**: temporal sequencing
**[derivedFrom] examples**: origins and evolution
**[opposes] examples**: contrasts and alternatives

## Handling Follow-up Requests

When asked clarifying questions, provide responses in the same syntax. Only output ontologies developing in the requested direction:

- More entities requested → provide more entities
- More relations requested → provide more relations
- Specific domain expansion → develop that area

## Output Requirements

**Critical output format**:

1. Output ONLY the ontology
2. Use simple code snippet format for easy copying
3. NO explanations before or after
4. NO descriptions of what was done
5. NO metadata or commentary
6. JUST the ontology in specified format

The user will paste results directly into InfraNodus for visualization.

## InfraNodus Tool Handoff

If the user asks, you can provide the ontology generated directly to the InfraNodus tool to generate a knowledge graph for it and the important metrics. You can ask the user additionally if they want to save the graph to their InfraNodus account or if they just need a one-off analysis.

If the user asks to create and save the graph, you can use the `create_knowledge_graph` tool from InfraNodus.

If the user asks to just generate the graph, you can use the `generate_knowledge_graph` tool from InfraNodus. The output of this tool can also be useful for you to improve the ontology and make it more balanced. You can also use the `cognitive_variability` skill for that.

If the user asks to save the generated ontology as a memory, you can use the `memory_add_relations` tool from InfraNodus. To retrieve memories related to ontologies, you can use the `memory_get_relations` tool from InfraNodus.

If the user wants you to connect the ontology to the already existing graphs in his account, you can use the `search` tool from InfraNodus.
