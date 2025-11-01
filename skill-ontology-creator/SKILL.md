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
