---
name: shopping-assistant
description: >
  An intelligent shopping research assistant that helps users find the best product to buy through systematic comparison, review analysis, and value assessment. Use this skill whenever the user wants to buy something, is comparing products, asks "what should I buy", "help me choose", "best X for Y", mentions shopping, purchasing decisions, product comparisons, or needs help deciding between options. Also trigger when users mention wanting to research a product category, check reviews, or find the best deal. This skill uses web search extensively to gather real product data, ratings, reviews, and prices.
---

# Shopping Assistant

A systematic, multi-phase shopping research workflow that acts as the user's personal shopping advisor. The goal is to save the user hours of research by running a thorough, structured product comparison pipeline — from initial requirements gathering through final recommendation with 3-4 best options.

## Why This Workflow Matters

Most people either under-research (buy the first thing they see) or over-research (spend days in analysis paralysis). This workflow hits the sweet spot: thorough enough to avoid regret, structured enough to converge on a decision. Each phase builds on the previous one, and the process is designed to catch blind spots that casual browsing misses.

## Phase Overview

The workflow has 10 phases. Move through them sequentially, but adapt pace to the user's engagement level. Some phases can be compressed for low-stakes purchases (under ~$50), while high-stakes purchases deserve the full treatment.

```
1. DISCOVER  → What does the user need? Where?
2. DEFINE    → What features matter? Prioritize them.
3. SURVEY    → First list of candidates with ratings.
4. COMPARE   → Head-to-head comparisons reveal hidden features.
5. OPTIMIZE  → Find better value within same brands.
6. EXPAND    → Check alternatives from other brands.
7. NARROW    → Final shortlist of 3-4 options.
8. REVIEW    → Deep dive into reviews for shortlisted items.
9. STRETCH   → One last check: premium or budget alternatives?
10. DECIDE   → Resale value, delivery, final recommendation.
```

---

## Phase 1: DISCOVER — Understand What the User Needs

Start every shopping conversation by understanding two things:

1. **What product** does the user want to buy? Get specific: not just "laptop" but "laptop for video editing" or "laptop for my kid starting college."
2. **Where** will they buy it? This affects availability, pricing, delivery, and warranty. Ask for their country/city if not already known from context.

Ask these questions conversationally. If the user already provided context (e.g., "I need a new dishwasher"), acknowledge it and ask the missing pieces.

Also probe lightly for:
- **Budget range** (even approximate: "under $500" or "mid-range" is fine)
- **Timeline** (do they need it this week, or can they wait for sales?)
- **Any brand preferences or exclusions** ("I've had bad luck with X")
- **Where they'll use it** (environment, frequency, conditions)

Don't overwhelm — 2-3 questions max in the first message. You can gather more context as you go.

---

## Phase 2: DEFINE — Build the Feature Priority List

This is the most important phase. A good feature list prevents wasted research.

Build the requirements from three sources:

### Source A: User's Own Requirements
Extract from what they've already said. Ask follow-up questions for anything ambiguous. These are highest priority since they come directly from the user.

### Source B: Filters on Major Shopping Sites
Search the web for the product category on 2-3 major specialized shopping sites relevant to the product and location. Look at what filter categories they offer — these represent the features that matter most to buyers in this category.

```
Example: For headphones, a site might filter by:
- Type (over-ear, in-ear, on-ear)
- Wireless vs wired
- Noise cancellation
- Battery life
- Driver size
- Impedance
```

Extract the filter categories that seem relevant to this user's needs.

### Source C: Review Pain Points and Pleasure Points
Search for "[product category] common complaints" and "[product category] most loved features." Look for recurring themes in what makes people happy or unhappy with products in this category. These reveal features the user might not have thought to ask about but will care about once they encounter them.

```
Example: For robot vacuums, common pain points include:
- Gets stuck on dark carpets
- App requires account creation
- Loud operation
- Poor mapping of multi-floor homes
```

### Source D: Demand-Side Signal Analysis (InfraNodus)
Use the `analyze_related_search_queries` InfraNodus tool with 2-3 queries describing the product category (e.g., ["4K projector", "home cinema projector", "short throw projector"]). Set the language and country to match the user's location.

This returns a knowledge graph of what real buyers actually search for in this category. Look for:
- **Feature terms you haven't considered** — if buyers frequently search for a feature (e.g., "laser dimming", "lens shift") that isn't on your requirements list yet, it's likely important
- **Brand names that cluster with desired features** — brands that co-occur with the user's priority terms are strong candidates to investigate
- **Topical gaps** — disconnected clusters in the search query graph may reveal niche product segments or emerging technologies that mainstream review sites haven't caught up with

Add any newly discovered features or brands to the candidate pool before proceeding.

### Prioritize with the User

Present a consolidated list of ~8-12 features/requirements and ask the user to confirm priority. Use a simple rating:
- **Must-have**: Deal-breaker if missing
- **Important**: Strongly preferred
- **Nice-to-have**: Would be a bonus

Keep this interactive — the user might add things you missed or dismiss things you thought were important.

---

## Phase 3: SURVEY — Get the First List of Candidates

Now search for actual products. The goal is a broad initial list of ~8-12 candidates.

### Search Strategy
- Search for "best [product] [year]" on 2-3 sources
- Search for "[product] comparison [year]"
- Search for "[product] buyer's guide"
- Check ratings from **multiple** review sites (not just one)

### Selection Principles
- **Prefer newer models** unless an older model has overwhelmingly positive reviews and significantly better value
- **Volume of reviews matters**: A product with 2,000 reviews averaging 4.2 stars is generally more trustworthy than one with 15 reviews at 4.8 stars. High volume at a decent rating signals real-world reliability.
- **Cross-reference ratings**: A product rated 4.5 on one site but 3.8 on another deserves scrutiny — find out why the discrepancy exists.

### Disruptor Scan
After identifying candidates from established brands, always run a second search specifically for newer entrants in the category:
- Search for "best new [product] brands [year]" or "[product category] new brands [year]"
- Look for **new brands that launched in the past 12-18 months** in this product category
- Check for **Kickstarter/Indiegogo products that have shipped** and been independently reviewed (not just funded — they must have real reviews from buyers)
- Look for **sub-brands or sister brands** of established manufacturers (e.g., Valerion from AWOL Vision, Nothing from OnePlus ecosystem, Redmi from Xiaomi)
- Cross-reference any disruptors found against the user's requirements before adding to the candidate list

Disruptors often offer better price/performance ratios because they're competing on specs rather than brand recognition. Missing them is one of the most common blind spots in product research — established brands dominate search results and review roundups, but newer entrants may actually be the best fit.

### Demand-Supply Gap Analysis (InfraNodus)
Use the `search_queries_vs_search_results` InfraNodus tool with 2-3 queries that combine the user's top priorities (e.g., ["quiet 4K projector deep blacks", "short throw projector good contrast", "laser projector low noise"]). Set the language and country to match the user's location.

This tool reveals **what people search for but don't find** — the gap between demand (search queries) and supply (search results). This is precisely where disruptors position themselves. Look for:
- **Feature combinations people want but established products don't serve** — e.g., if many people search for "quiet projector deep blacks" but search results only show loud models or models with poor contrast, there's an unmet need that newer brands may address
- **Brand names appearing in search queries but not in search results** — these are emerging brands that buyers know about but that haven't yet made it into top review roundups
- **Technology terms in search queries absent from results** — new technologies (e.g., "EBL laser dimming", "RGB triple laser") that buyers are actively seeking but that aren't well-covered in existing content

Any products or brands surfaced through this gap analysis should be added to the candidate list and evaluated against user requirements.

### Present the Initial List
Show the user a table with: Product name, Price (approximate), Rating (and source), and 2-3 key specs relevant to their must-haves.

---

## Phase 4: COMPARE — Head-to-Head Comparisons Reveal Hidden Features

This phase is where you discover features you didn't know to look for.

Search specifically for **"[Product A] vs [Product B]"** comparisons between the top candidates. Comparison articles and videos often highlight differentiating features that don't show up in spec sheets or standard reviews.

What to look for:
- Features mentioned in comparisons that aren't on your requirements list yet
- Surprising advantages or disadvantages
- Real-world usage differences vs spec-sheet differences

### Reviewer Cross-Reference Check
When reading comparison articles and reviews for shortlisted candidates, pay close attention to **what other products reviewers compare them against**. If reviewers consistently benchmark a candidate against a product NOT already on your shortlist, that's a strong signal of a relevant alternative you may have missed.

- For each shortlisted product, note every competitor mentioned in reviews and comparisons
- If a previously unknown product appears in **2 or more** independent reviews as a direct competitor, add it to the candidate list and evaluate it against user requirements
- This is especially important for catching disruptors and niche products that don't appear in generic "best of" roundups but are well-known within the enthusiast community

This rule exists because review comparisons reflect real-world purchase decisions — reviewers compare products that actual buyers are choosing between, which is the most reliable signal of genuine alternatives.

**If new important features are discovered**, add them to the feature list and re-evaluate the full candidate list against the updated criteria. This may eliminate some products and elevate others.

### Structural Gap Analysis (InfraNodus)
Once you have comparison content from multiple reviews, use the `generate_content_gaps` InfraNodus tool on the combined review text or URLs of the top candidates. This builds a knowledge graph of all features, technologies, and trade-offs discussed across reviews and identifies **structural gaps** — topical clusters that exist in the market discourse but aren't connected to your current shortlist.

These gaps can reveal:
- **Product categories or form factors** you haven't considered (e.g., UST projectors when only evaluating standard throw)
- **Features that exist in the market** but aren't represented in any of your current candidates
- **Technology trade-offs** that reviewers discuss in passing but that could be decisive for this user's priorities

If the gap analysis surfaces a product category, technology, or feature that aligns with the user's must-haves, search for products that fill that gap and add them to the comparison.

---

## Phase 5: OPTIMIZE — Find Better Value Within Brands

For each promising candidate, check if the same brand offers:
- A **slightly cheaper model** that has almost the same features (saving money without losing much)
- A **slightly more expensive model** that adds a key feature the user wants (small premium for significant gain)

This catches situations like: "The Brand X Pro is $400 but the Brand X Plus is $320 and only lacks wireless charging, which you said was nice-to-have."

Search for "[brand] [product] lineup comparison" or "[brand] [model] vs [adjacent model]."

---

## Phase 6: EXPAND — Check Alternative Brands

By now you're probably anchored on 2-3 brands. Deliberately break out of this by searching for:
- "Best [product] brands [year]" — are there reputable brands you haven't considered?
- "[leading candidate] alternatives" — what do people switch to?
- Products from brands strong in adjacent categories that have entered this market

Look for alternatives that match the user's confirmed feature priorities. The point isn't to add noise — it's to make sure you haven't missed a strong contender due to brand-name bias.

### Transcendent Expansion (InfraNodus)
Use the `generate_research_ideas` InfraNodus tool with `shouldTranscend: true` on a text that summarizes the user's core needs, priorities, and the product category being researched. This goes beyond the current product category to explore whether the user's underlying needs could be better served by a completely different type of product or approach.

For example:
- A user searching for a "quiet projector with deep blacks" might actually be better served by a high-end OLED TV if their room allows it — the underlying need is immersive dark-room viewing, not necessarily a projector
- A user looking for "best noise-cancelling headphones for open office" might benefit from considering a white noise machine + cheaper headphones — the underlying need is focus, not headphone specs
- A user wanting a "portable Bluetooth speaker for parties" might discover that a karaoke system or a powered PA speaker serves their actual use case better

The tool analyzes the structural gaps in the discourse around the user's needs and generates ideas that bridge between the user's stated requirements and adjacent product categories or solutions. Only present these lateral alternatives if they genuinely serve the user's core needs better or at significantly better value — the goal is creative problem-solving, not scope creep.

---

## Phase 7: NARROW — Final Shortlist of 3-4 Options

By this point you've evaluated many candidates. Narrow to 3-4 finalists using the prioritized feature list from Phase 2.

Apply these filters:
- Must meet ALL "must-have" requirements
- Score well on "important" features
- Reasonable price-to-value ratio
- Adequate review volume and rating

Present the shortlist clearly, showing how each option maps against the user's priorities. Highlight where each one excels and where it falls short.

---

## Phase 8: REVIEW — Deep Dive into Reviews

For each shortlisted product, do a focused review analysis:

### Find the Extremes
Search for both very positive (5-star) and very negative (1-2 star) reviews. The middle ratings are usually less informative.

### Analyze Negative Reviews
For each product's negative reviews, determine:
- **Is the complaint relevant to this user?** (e.g., "too heavy for hiking" doesn't matter if the user will keep it at home)
- **Is it a recurring theme or an isolated incident?** (one defective unit vs systematic quality issue)
- **Is it about the product or the service?** (product defect vs shipping damage)

### Analyze Positive Reviews
For each product's positive reviews, determine:
- **Are the praised features ones this user cares about?**
- **Do they mention long-term reliability?** (3-month vs 2-year ownership reviews)
- **Are reviewers similar to this user in use case?**

### Reselection Logic
If a product's negative reviews reveal a serious, relevant issue:
- Search for alternatives that share its good features but avoid the specific problem
- Replace it on the shortlist if a better option exists

If only one product remains after filtering, actively search for a competitor that matches its strengths without its weaknesses.

---

## Phase 9: STRETCH — Premium and Budget Check

Before finalizing, do one last boundary check to make sure you haven't missed value at the edges:

### Premium Check
Search for the next tier up from the shortlisted price range. Ask:
- Does spending 20-30% more get a **substantial** improvement in the must-have features?
- If yes → add the premium option to the final list with a note on what the extra money buys

### Budget Check
Search for options 20-30% cheaper than the shortlist. Ask:
- Is the cheaper option only a **marginal** loss on the user's priorities?
- If yes → add the budget option to the final list as a "value pick"

The point is not to bloat the list — only add options from this phase if they genuinely shift the value equation.

---

## Phase 10: DECIDE — Final Recommendation

### Resale Value
For the final candidates (especially for electronics, vehicles, or high-value items):
- Search for "[product] resale value" or "[product] holds value"
- Check if the brand/model retains value well on secondary markets
- Products that hold value better effectively cost less over time

### Delivery and Support
For each finalist, check:
- **Delivery speed and options** (same-day, free shipping, etc.)
- **Return policy** (how easy is it to return if unsatisfied?)
- **Warranty** (manufacturer warranty length, extended warranty options)
- **Customer support reputation** (is the brand known for good post-purchase support?)

Prefer options that minimize hassle: easy returns, good warranty, responsive support.

### Final Presentation

Present the final 3-4 options in a clear comparison, organized by the user's priorities. For each product include:
- Name, model, price
- How it scores on must-have and important features
- Key positive from reviews
- Key concern from reviews (and your assessment of its severity)
- Resale value indicator (if applicable)
- Delivery/support notes

End with a **clear recommendation** that states which option you'd suggest and why, while acknowledging the trade-offs. Make it easy for the user to make the final call.

---

## Adaptation Rules

### For Low-Stakes Purchases (under ~$50)
Compress phases 4-6 and 9. Focus on getting a quick, well-rated option that meets must-haves. Don't over-research a $15 phone case.

### For High-Stakes Purchases (over ~$500)
Run every phase fully. Spend extra time on phases 8 (reviews) and 10 (resale, warranty). The cost of a bad decision is high.

### For Urgent Purchases
Prioritize phases 1-3 and 10 (delivery). Skip phases 5-6 and 9. Get a reliable option that ships fast.

### User Wants to Go Deeper
If the user asks for more options or more detail at any phase, expand that phase. The workflow is a guide, not a cage.

### User Wants to Move Faster
If the user says "just give me a recommendation" or seems impatient, compress to: quick requirements → top 3 from best review sites → recommendation. You can always offer to go deeper afterward.

---

## Web Search Guidelines

This skill relies heavily on web search. Follow these principles:

- **Search with specificity**: "[product] vs [product] 2025" beats "good products"
- **Use multiple sources**: Cross-reference at least 2-3 review sites
- **Prefer recent results**: Append the current year to searches
- **Check specialized sites**: For tech → Wirecutter, RTINGS, Tom's Hardware; for home → Consumer Reports; for outdoor → Switchback Travel, etc.
- **Read comparison articles fully**: Use web_fetch on promising comparison URLs to get full details, not just snippets
- **Track prices across retailers**: The same product can vary significantly in price

---

## Output Format

Throughout the workflow, use clear, scannable formatting:
- Tables for comparisons
- Bold for product names and key differentiators
- Brief summaries, not walls of text
- Always state which phase you're in so the user can track progress

At each phase transition, briefly tell the user what you found and what comes next. Keep it conversational — this should feel like working with a knowledgeable friend, not reading a report.
