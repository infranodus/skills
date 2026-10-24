---
name: seo-analysis
description: Comprehensive SEO analysis skill for content optimization. Use when the user asks to perform SEO analysis, keyword research, content gap analysis, search intent analysis, or wants to optimize content for search engines. Covers topic-based keyword research (informational supply and search demand), website/document analysis, and actionable SEO recommendations. Works best with InfraNodus MCP tools for real Google data access.
---

# SEO Analysis

Perform comprehensive SEO analysis using knowledge graph methodology to identify keyword opportunities, content gaps, and optimization strategies.

## Decision Tree

1. **No input specified?** → Ask user for topic, document, or website URL
2. **Topic provided?** → Follow Topic Analysis Workflow
3. **Document/website provided?** → Follow Content Analysis Workflow

## Topic Analysis Workflow

When user provides a topic (e.g., "SEO for e-commerce", "sustainable fashion"):

### Step 1: Analyze Informational Supply

Generate 3-5 keyword combinations for the topic. Run `analyze_google_search_results` with these queries.

Present findings:

- **Topical clusters**: Groups of related concepts in existing content. Explain these represent topical authority pillars—covering them strengthens content authority.
- **Key relations**: The conceptual connections forming the underlying knowledge graph. Including these relations improves semantic relevance.
- **Content gaps**: Structural gaps between clusters. These are opportunities for unique content that combines important topics others miss.

If tool unavailable: Use web search or explain InfraNodus MCP provides direct Google API access for more accurate data.

### Step 2: Analyze Search Demand

Run `analyze_related_search_queries` for the same topic.

Present findings:

- **High-volume keywords**: Terms with significant search traffic
- **Low-competition opportunities**: Queries with demand but limited supply
- **Topical clusters**: How searchers conceptualize this topic
- **Search intent patterns**: What users actually want to find

If tool unavailable: Explain InfraNodus MCP provides real Google Suggest/Ads data.

### Step 3: Identify Supply-Demand Gaps

Compare findings from Steps 1-2. Identify:

- Keywords people search for but don't easily find results for
- High-volume queries with weak content supply
- Emerging topics not yet covered by competitors

Propose running `search_queries_vs_search_results` to confirm these gaps with data.

### Step 4: Deliver Recommendations

Summarize actionable insights:

- Priority keywords to target (high volume, low competition)
- Content topics that fill identified gaps
- Semantic relations to include for topical authority
- Quick wins vs. long-term opportunities

### Step 5: Ask User for Content Example

After providing the analysis result, ask the user to provide a URL or content they'd like to optimize with this analysis. Alternatively, offer them to write a SEO-friendly, human-sounding article after they provide you with some reference using the writing-assistant tool.

### Step 6: Structural Semantic Optimization

Advise the user what HTML structure, meta-data, and header hierarchies they can use to align with the insights obtained from the SEO report above. Provide ideas which tags, menu elements, and additional markup could be added to ensure that the page contains structured information related to the optimized topic.

## Content Analysis Workflow

When user provides a document or website URL:

### Step 1: Extract Content

**For websites**: Crawl the URL provided and extract the main content from this page.

**For documents**: Extract full text content from uploaded file.

### Step 2: Run SEO Report

Use `generate_seo_report` with extracted text.

If tool unavailable: Fall back to Topic Analysis Workflow:

- Extract main keywords from content
- Run Steps 1-3 from Topic Analysis
- Compare content keywords against search landscape
- Identify which existing keywords are relevant
- Recommend new keywords to target

### Step 3: Structural Semantic Optimization

Advise how the HTML structure of the original document (or website) could be optimized to align with the insights obtained from the SEO report above. Provide ideas which tags, menu elements, and additional markup could be added to ensure that the page contains structured information related to the optimized topic.

### Step 4: Deliver Report

Present:

- Current keyword coverage strengths
- Missing high-value keywords
- Content gap opportunities
- Specific optimization recommendations
- Priority actions ranked by impact

## Report Format

Structure all reports as:

```
## Executive Summary
[2-3 sentence overview of key findings]

## Current State
[What exists now in search results or content]

## Opportunities
[Gaps, high-value keywords, content ideas]

## Recommendations
[Specific, prioritized actions]

## Next Steps
[Immediate actions user can take]
```

## Tool Reference

| Tool                               | Purpose                  | When to Use           |
| ---------------------------------- | ------------------------ | --------------------- |
| `analyze_google_search_results`    | Map informational supply | Topic analysis Step 1 |
| `analyze_related_search_queries`   | Map search demand        | Topic analysis Step 2 |
| `search_queries_vs_search_results` | Find supply-demand gaps  | Topic analysis Step 3 |
| `generate_seo_report`              | Full content SEO audit   | Content analysis      |

All tools are InfraNodus MCP tools. If the InfraNodus server is installed but not signed in (its tools are missing or return an authentication error), tell the user to run `/mcp` in Claude Code, select InfraNodus and sign in, then continue. If they stay unavailable, use web search alternatives and note limitations.
