# InfraNodus Tool Examples

Condensed examples for each tool. All use the same sample text unless noted.

## Sample Text

```
God said, 'You shall not eat of the fruit of the tree which is in the midst of the garden,
neither shall you touch it, lest you die.'" But the serpent said to the woman, "You will not die.
For God knows that when you eat of it your eyes will be opened, and you will be like God,
knowing good and evil."
```

---

## generate_knowledge_graph

```bash
mcporter call infranodus.generate_knowledge_graph --args '{
  "text": "<sample text>",
  "includeGraph": true
}'
```

Response includes: `statistics` (modularity, diversity_stats), `contentGaps`, `mainTopicalClusters`, `mainConcepts`, `conceptualGateways`, `topRelations`, `topInfluentialNodes`, `knowledgeGraphByCluster`.

Diversity stats fields: `diversity_score` (biased/focused/diversified/dispersed), `modularity_score`, `too_focused_on_top_nodes`, `ratio_of_top_nodes_influence_by_betweenness`.

## create_knowledge_graph

Same as `generate_knowledge_graph` but adds `graphName` parameter and saves to InfraNodus. Response adds `graphName`, `graphUrl`.

```bash
mcporter call infranodus.create_knowledge_graph --args '{
  "graphName": "bible_genesis",
  "text": "<sample text>",
  "includeGraph": true
}'
```

## generate_topical_clusters

Returns only `topicalClusters` array. Format: `"Name: keywords (cluster_id | degree% | betweenness%)"`.

## generate_content_gaps

Returns only `contentGaps` array. Format: `"Gap N: Cluster A (keywords) -> Cluster B (keywords)"`.

## generate_research_questions

```json
{"text": "<sample>", "useSeveralGaps": true, "modelToUse": "gpt-4o"}
```
Returns `questions` array (3 questions bridging content gaps).

## generate_research_ideas

```json
{"text": "<sample>", "useSeveralGaps": true, "shouldTranscend": true, "modelToUse": "gpt-4o"}
```
Returns `responses` array with creative ideas.

## generate_contextual_hint

Returns `textOverview` — a structured XML-like summary with MainConcepts, MainTopics, TopicalGaps, ConceptualGateways, Relations, DiversityStatistics. Ideal for GraphRAG context injection.

## develop_latent_topics

```json
{"text": "<sample>", "requestMode": "transcend"}
```
Returns: `ideas`, `mainTopics`, `latentTopicsToDevelop`.

## develop_conceptual_bridges

```json
{"text": "<sample>", "requestMode": "transcend"}
```
Returns: `ideas`, `latentConceptsToDevelop`, `latentConceptsRelations`.

## develop_text_tool

Combined pipeline. Returns: `contentGapIdeas`, `latentTopicsIdeas`, `conceptualBridgesIdeas`, `contentGaps`, `conceptualBridges`, `latentTopics`, `mainTopics`.

```json
{"text": "<sample>", "transcendDiscourse": true}
```

## optimize_text_structure

Returns: `suggestions`, `diversity_stats`, `mainTopicalClusters`, `contentGaps`, `mainConcepts`, `topicsToDevelop`, `conceptualGateways`, `topRelations`, `topKeywordCombinations`.

```json
{"text": "<sample>", "responseType": "transcend"}
```

## analyze_text

Like `generate_knowledge_graph` but includes `statements` and focuses on analysis recommendations rather than graph structure.

## analyze_existing_graph_by_name

```json
{"text": "<graph_name>"}
```
Note: uses `text` field for the graph name.

---

## Memory Tools

### memory_add_relations

```json
{"graphName": "test_bible_entities", "text": "<sample>", "modifyAnalyzedText": "extractEntitiesOnly"}
```
Creates entity-based knowledge graph with `[[wikilinks]]`. Returns graph analysis of entities.

### memory_get_relations

```json
{"memoryContextName": "test_bible_memory", "entity": "[[god]]"}
```
Returns: `statements`, `graphNames`, `graphUrls`.

---

## Retrieval & Search

### retrieve_from_knowledge_base

```json
{"graphName": "test_bible", "prompt": "sin", "includeGraphSummary": true}
```
Returns `retrievedStatements` (with `similarityScore`) + optional `graphSummary`.

### list_graphs

```json
{"nameContains": "bible", "type": "memory"}
```
Returns: `totalGraphs`, `filters`, `graphs[]` (id, name, type, dates).

### search / fetch

Search: `{"query": "serpent"}` → returns `results[]` with `id`, `title`, `url`.
Fetch: `{"id": "user:graph:term"}` → returns full `text` of matched statements.

---

## Text Comparison

All take `contexts` array of `{text}`, `{url}`, or `{graphName}` objects.

### generate_difference_graph_from_text

Shows what's in contexts 2..N but NOT in context 1. Add `includeStatements: true` for source text.

### generate_overlap_from_texts

Shows only topics common to ALL contexts. No overlap = empty results.

### merged_graph_from_texts

Merges all contexts into one graph. Useful for discourse overview across multiple sources.

---

## SEO Tools

### analyze_google_search_results

```json
{"queries": ["bible", "forbidden fruit"], "showExtendedGraphInfo": true, "includeSearchResults": true}
```

### analyze_related_search_queries

```json
{"queries": ["heart rate variability"], "importLanguage": "EN", "importCountry": "US"}
```

### search_queries_vs_search_results

```json
{"queries": ["heart rate variability", "fitness trackers"], "includeSearchQueries": true, "importLanguage": "EN", "importCountry": "US"}
```

### generate_seo_report

```json
{"url": "https://example.com", "contentToExtract": "header tags"}
```
**Set timeout to 90s+.** Returns: `inSearchResultsNotInText`, `inSearchQueriesNotInText`, `inSearchQueriesNotInResults`, `topMissingQueries`.
