---
name: structural-humanizer
description: "Rewrite a text so that its sentence rhythm and the way it moves through its ideas match how human-written texts read, using the InfraNodus analyze_text_signature tool (sentence-length rhythm, topic-path fractal scaling, topic crossings, modularity) as editing targets rather than as a detector. Use when the user wants a draft to read as human, asks to humanize its structure, rhythm, or narrative movement, wants a text to dwell on ideas instead of alternating, or asks whether a rewrite moved the right structural metrics. Complements the writing-assistant skill (word-level tells) and Pangram (the actual AI verdict): this one edits pacing and topology. Requires the InfraNodus MCP server with analyze_text_signature (falls back to analyze_text with fractal_variability)."
metadata:
  homepage: https://infranodus.com
  openclaw:
    emoji: "🌀"
    requires:
      bins: ["mcporter"]
      env: ["INFRANODUS_API_KEY"]
    primaryEnv: INFRANODUS_API_KEY
    install:
      - id: mcporter
        kind: node
        package: mcporter
        bins: ["mcporter"]
        label: Install mcporter (node)
---

# Structural Humanizer

Lexical humanizers remove AI vocabulary. This skill works on two other layers: the rhythm of the sentences and the path a reader takes through the text's concept graph. It gives a rewrite a direction and a feedback dial. It is **not a detector** and must never be presented as one; see "What these measures are for" before doing anything else.

## The tool

Use `analyze_text_signature` (InfraNodus MCP server, 2026-09-11 or later) with `text` or `url`, `multifractal: true`, and **`maxNodes: 150`** (the default). Every band below was measured at 150 on 111 texts; the path exponents and amplitude measures change with the node cap (at 500 the path includes the peripheral words and most amplitude signals fade), so always measure before and after at the same setting and never compare a value with a band measured at another cap. It returns five blocks: `signature` (a named profile), `structure` (modularity and diversity), `rhythm` (fractal exponents of the topic path at statement, word, and n-gram level), `amplitude` (step sizes and topic crossings along the path), and `sentence_rhythm` (sentence-length statistics), plus an `ai_likeness` layer. Each number comes with a plain-language `reading`; quote those readings to the user rather than paraphrasing the numbers yourself.

**Do not use the `ai_likeness` block.** Its sentence-rhythm heuristics come from the general stylometry literature (uneven, short-sentence prose = human) and on the reference corpora they point the wrong way: it called 10 of 11 texts of known AI origin "leans human" and 21 of 75 human texts "leans generated". Ignore its verdict, score, and evidence list entirely; the evidence signals are reused below with the direction that the data supports. If the server is older and only `analyze_text` exists, use that with `multifractal: true`, `includeGraph: true` and the fractal targets in the fallback section.

## What these measures are for

Three studies (50 infranodus.com pages, 50 Nodus Labs posts, 11 texts of known AI origin; all 2026-09, one author, 107 texts with a full signature) tested whether InfraNodus structural and rhythmic measures separate AI-drafted text from human text. The result, stated once so the skill never overclaims:

- **They describe how a text moves.** A detector gives a probability and no explanation. These measures say what the text is doing: whether its sections form separate islands or share one vocabulary throughout, whether it dwells on an idea before shifting or alternates every sentence, whether an excursion is sustained or a one-off mention. These are editorial facts about the text regardless of who wrote it.
- **They give a rewrite something to aim at.** Pangram can say a text scores 90% AI but cannot say what to change, and re-scoring after every edit is a blind search. The measures give a direction and let the agent measure again after editing. That is the whole use of this skill.
- **They do not tell you who wrote a text.** On the 11 texts of known AI origin, the graph-structure profile called 1 clearly AI, 2 leaning, 6 ambiguous, and 2 human; Pangram caught 8 outright. The sentence-rhythm signals separate the groups far better (see below) but they are this author's habits against this author's prompting of models, not universal markers, and a model can be prompted into any sentence rhythm. For a verdict on authorship, use a detector such as Pangram and say so.
- **Speculative, and the reason the measures are interesting:** the fractal exponents are the same DFA statistics applied to heart-rate and movement series. "More momentum, less shuffling" in a text's reading path may be the textual form of the fractal variability state trained physically in EightOS and SelfSense. That is a hypothesis about meaning, not a result; mention it only if the user asks what the numbers mean.

## The measures and their targets

Bands are from the reference corpora (78 human texts, 33 AI-flagged of which 11 known AI), measured with `maxNodes: 150`. "Matched" means after restricting both groups to the same path-length range so text length does not drive the result. They are one author's; see the last limit below.

### Primary target: sentence rhythm (`sentence_rhythm`)

The strongest separation on every corpus, and the opposite of the folk rule. The author's human prose runs on long sentences with few short ones; the AI-drafted texts run on short, punchy sentences with many fragments, the "burstiness" that models are now prompted into. On the 11 texts of known AI origin against length-matched human texts the separation is complete (AUC 0.98 to 1.00).

| Field | Human mean | AI-drafted mean (known AI) | Target for a rewrite |
|---|---|---|---|
| `meanLength` (words per sentence) | 21 | 15 (11) | 18 or above |
| `shortShare` (sentences under 8 words) | 0.07 | 0.23 (0.40) | 0.10 or below |
| `longShare` (sentences over 30 words) | 0.17 | 0.07 (0.04) | 0.12 or above |
| `cvLength` (variability of length) | 0.48 | 0.62 (0.76) | 0.40 to 0.55 |

Quote the tool's `readings.cvLength` and `readings.shortShare` and then say what the numbers mean here: the text is chopped into short declaratives, or it is not.

### Secondary target: topic-path persistence (`rhythm`)

`rhythm.fractal_variability["ngrams.byRadialDistance"].alphaBounded`: how persistently the text's distance from its core theme carries over across scales, on the 4-word smoothed path. Human mean 0.90, AI-drafted 0.79 (known AI 0.75); matched AUC 0.73, known-AI against matched human 0.89. The same exponent on the raw word path (`words.byRadialDistance.alphaBounded`, human 0.75, AI 0.66) agrees at AUC 0.72. **Target: 0.85 or above on the n-gram radial series.** The n-gram step-length alpha1 (human 0.79, AI 0.71, matched AUC 0.65) points the same way and may be quoted as a second view. Use `readings.words.radialDistance` and `readings.words.scales` for the plain-language reading. Statement-level exponents and the `influence` series carry nothing.

### Tertiary target: movement amplitude (`amplitude.words`)

At 150 nodes the amplitude block separates the groups well, and it is the most editable layer after sentence rhythm because each field names one habit.

| Field | Human | AI-drafted (known) | Matched AUC | What it says |
|---|---|---|---|---|
| `crossClusterShare` | 0.35 | 0.45 (0.48) | 0.74 | AI text changes topic on nearly every other move |
| `crossClusterRunCV` | 0.98 | 0.91 (0.84) | 0.72 | AI topic changes come at regular intervals, like an outline |
| `cvStep` | 0.61 | 0.56 (0.57) | 0.73 | AI moves between ideas are more uniform in size |
| `meanStep` | 0.72 | 0.86 (0.86) | 0.75 | AI consecutive ideas sit further apart |
| `lag1Autocorrelation` | 0.14 | 0.12 (0.10) | 0.71 | human text has stretches of leaping and stretches of staying |

**Targets: cross-cluster share 0.38 or below, cross-cluster run CV 0.95 or above, step CV 0.60 or above.** Quote the tool's `readings.words` sentences for each. Together they describe the same habit from four sides: the AI-drafted text steps through its topics at an even pace with a shift on almost every other move; the human text dwells, then leaps, then dwells, at irregular intervals.

### Supporting measures (report, do not target)

- **Modularity** (`structure.modularity`): human mean 0.47, AI-drafted 0.39, matched AUC 0.67 but only 0.58 on the known-AI texts. Low on AI-drafted essays with one recurring vocabulary, normal on AI-drafted documentation with proper sections. It tracks how a text is organised, not who wrote it. Raise it only when the text visibly restates its whole keyword set in every paragraph.
- **Diversity label** (`structure.diversity_stats.diversity_score`) and the `structure.readings`: any of biased, focused, diversified is consistent with human text; never a reason to rewrite. Quote the readings as description.
- **Signature label** (`signature.label`: essay, report, digest, deep dive, boilerplate, notes): a genre name, not an authorship signal. Both groups spread across them; "report" and "digest" dominate on both sides. Use it to describe the text.
- **Radial multifractal source** on the word series: exists only for texts of roughly 1,800 words or more; when present and "distribution" or "both", mention it and apply the orphan-term move.

What carries no signal at 150 nodes: word-level step alphaBounded, n-gram step alpha2, statement-level exponents, cluster count, the "too focused" flags, the whole `structure.degree_distribution` block (node and edge counts and Gini track text length at 0.9 or more, the tail exponent is flat; quote its readings as description only), the `rhythm.fractal_variability.influence` series (alpha on betweenness, degree, and rank is the same for both groups), `sentence_rhythm.scaling` (DFA on sentence lengths; the plain sentence statistics carry the signal, the scaling does not), and the `ai_likeness` score in its own direction (it separates the groups at AUC 0.75, but inverted).

### Fallback when only `analyze_text` is available

`analyze_text` with `multifractal: true`, `includeGraph: true`, default `maxNodes` (150). No sentence rhythm or amplitude is returned; use `fractal_variability.ngrams.byRadialDistance.alphaBounded` (target 0.85 or above) and `fractal_variability.ngrams.byStepLength.alpha1` (human 0.79, AI 0.71, target 0.75 or above), and say that sentence rhythm and amplitude could not be checked.

## Procedure

1. **Measure the original.** `analyze_text_signature` with `text` (or `url`), `multifractal: true`, `maxNodes: 150`. Record the four sentence-rhythm fields, the n-gram radial alphaBounded, the amplitude fields, the supporting measures, and the word count. Under about 30 sentences or 500 words the rhythm measures are noisy; say so and describe qualitatively.
2. **Describe, then diagnose.** First say in plain words how the text reads, using the tool's own `readings` sentences: how its sentences are paced, whether it dwells on a theme or keeps crossing topics, whether its sections have their own vocabulary. Then compare the three targets to their bands and say which are off and by how much. If all three are in band, say so and stop; do not rewrite for its own sake. Never state or imply a verdict on authorship from these numbers and never quote the `ai_likeness` block; if the user wants a verdict, point to Pangram.
3. **Rewrite against the targets.** Apply the instruction below, keeping meaning, facts, and length within about 15% of the original unless the user allows trimming. Sentence rhythm first, then topic movement. Do not add lexical tells; if the writing-assistant or a lexical humanizer skill is installed, run it after this step, not before, since its edits change both the rhythm and the path.
4. **Re-measure.** Same call on the rewrite, same `maxNodes`. Present a before/after table: sentence rhythm, path persistence, and amplitude above a rule, the supporting measures below it. A rewrite is done when the sentence-rhythm fields are in band and at least two of the path and amplitude targets have moved toward their bands; otherwise revise the weakest passage and measure again. Treat differences under 0.05 on the exponents and under 0.03 on the shares as noise.
5. **Outcome check (optional).** If the Pangram MCP server is available, `detect_ai_text` on original and rewrite and report fraction_ai before and after. Say plainly that Pangram reads lexical surface and these measures read rhythm and topology, so the two move partly independently; a structural rewrite can leave the detector verdict unchanged, and that is expected.
6. **Report.** The description from step 2, the before/after table, the two or three edits that moved the measures most, and any measure that could not be moved without harming the text.

## The rewriting instruction

Restructure the text so that it reads at the pace of the author's own prose and moves through its ideas with momentum.

1) **Sentence rhythm.** Join the chopped declaratives. Where the draft strings together sentences of five to ten words, each carrying one point, fold two or three of them into one sentence with a subordinate clause, a colon, or a relative clause, so that the mean runs to 18 words or more and one sentence in eight runs past 30. Keep a few short sentences for emphasis, one in ten at most, and remove sentence fragments used as punchlines. Vary length by argument, not by pattern: a long sentence when a thought has parts, a short one when it does not.
2) **Topic momentum.** When the text drifts away from its main theme it keeps drifting for a while before it turns back, and the return is gradual, so the text wanders rather than jumps or sticks. This is the n-gram radial alphaBounded target.
3) **Fewer crossings.** Do one thing at a time for a stretch. When the text transitions, let it sweep across the related ideas in a few consecutive sentences rather than one; when it develops an idea, stay with it for several sentences before the next shift. Avoid the fine interleave of one shift, one sentence of development, one shift. This lowers the cross-cluster share.
4) Only where the text visibly restates its whole keyword set in every paragraph, give each sub-topic its own stretch with its own vocabulary so the graph forms distinct islands.

Two habits to apply when they fit the text, never as targets: let one or two main concepts recur across sections as the thread, and never leave a peripheral term as a one-off mention that connects to nothing else.

Concrete moves, in order of how much they move the targets:
- **Fold the short sentences.** Three consecutive sentences under ten words almost always want to be one sentence with two clauses. This is the single largest move on every corpus.
- **Cut the fragment punchlines.** "Not a replacement. A complementary projection." reads as generated; make it one sentence or drop it.
- **Let one sentence in eight run long.** A 35-word sentence with a subordinate clause and a qualification is normal in this author's prose and nearly absent from the drafts.
- **Group the transitions.** Where the draft alternates every sentence between introducing a new idea and elaborating the previous one, reorder so the introductions sit together and the elaborations sit together. This lowers topic crossings without changing what the text says.
- **Let digressions run.** When a side topic starts, give it three to five sentences and end with an explicit return to the thread, instead of a parenthetical mention.
- **Merge scattered mentions.** Collect one-line references to a side concept into the one paragraph where it is developed, or delete them.
- **Cut orphan terms.** A concept that appears once and links to nothing else is the distribution-source signature.
- **Thread a carrier concept.** Pick one or two concepts and let them recur across sections.
- **Separate vocabularies** only when sections blur.

## Reporting rules

Quote measures with their names and the direction of change, never as pass/fail alone, and prefer the tool's own `readings` sentences over paraphrase. Keep the three targets and the supporting measures visually separate. Never quote or mention the `ai_likeness` block. Say "hypothesis-level" once. Never claim a text "is now human" and never claim it "was AI": say how the text moved before and after, and which measures moved into the human band of the reference studies. If asked whether a text is AI-written, answer that these measures cannot say and name the detector that can.

## Errors and limits

- `analyze_text_signature` missing: the server predates it; use the fallback with `analyze_text` and say that sentence rhythm could not be checked.
- `rhythm` empty or `fractal_variability` absent: the server predates fractal support; report sentence rhythm and structure only.
- Texts under about 30 sentences or 500 words: the rhythm measures are noisy; describe the text qualitatively and skip the numeric targets. The n-gram series needs about 520 words of prose; the multifractal spectrum needs about 1,800.
- Changing `maxNodes` changes the topic path, every exponent on it, and the amplitude fields; the bands here are for 150, the default. At 500 most amplitude signals fade and the n-gram step alpha1 goes flat while the radial alphaBounded stays. Always measure before and after at the same setting.
- The n-gram exponents read higher than the word-level ones by construction (the smoothing adds persistence); compare a level only with the same level of another text, never across levels.
- Radial measures depend on the graph layout; re-running the same text can shift an exponent by a few hundredths.
- **The bands are one author's.** Long sentences with few short ones are this author's habit, and short punchy sentences are what this author's prompts produce from models; another writer's human band may sit elsewhere, and a model can be prompted into any rhythm. When a user has a corpus of their own human-written texts, measure five or six first and use their band instead of the one here. Say this whenever the user is not the author of the reference corpora.
- The reference studies are one author, three corpora, 32 AI-flagged texts of which 11 are of known origin.
