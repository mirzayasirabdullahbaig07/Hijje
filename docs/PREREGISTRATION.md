# Analysis plan, written before the volunteer data exists

Status: written 15 November 2026. At this date **no volunteer answer has been
looked at for analysis** (only the author's own test answers, which are
excluded, see "Exclusions"). Everything in `results/` so far comes from the
Dakshina word lexicon and constructed queries. That work is **exploratory /
development**: the normaliser levels were designed and chosen on it. The
volunteer data is the **confirmatory test**. A reader can check the date of this
file in the git history; the commit that adds it is tagged `prereg-v1`.

## Question

When people write Roman Urdu search queries in their own spelling, how much
retrieval quality is lost by a word-matching retriever, and do spelling
normalisers get it back?

## Data

- Collection: the 9,759 Dakshina Urdu sentences as passages (`hijje collect-build`).
- Queries: written by volunteers through the pool form (v0.7): 12 Urdu-script
  sentences per visit, 6 from the core set (set A, 40 sentences), 6 from the others.
  The query is what the person would type to find that sentence.
- Relevance (primary): the source sentence is relevant (grade 2); any other
  sentence containing all the query's words is not counted, because a volunteer's
  spelling may differ from the passage's. Grade 1 is only used in the sensitivity
  analysis below.
- Stopping rule: collect until **50 completed forms** or **8 weeks** after the
  first public link, whichever comes first. No retrieval result is computed
  before collection stops. (Counting rows in the sheet is allowed.)

## Exclusions (fixed now)

1. The author's own test answers.
2. Rows marked skipped, empty, typed in Urdu script, or longer than 200 characters
   (the rules in `collect.load_responses`).
3. Writers with fewer than 4 usable answers (`hijje collect-build --min-answers 4`).
4. Any exclusion decided after seeing results must be listed in
   `docs/DEVIATIONS.md` with the reason, and the results shown both ways.

## Systems

`bm25` (no normalisation), `bm25-l1` to `bm25-l4` (normaliser levels), `char`
(character n-gram TF-IDF), fusion of bm25 and char, and the dense retrievers from
`notebooks/dense_baselines.ipynb` if the notebook is run on this data. Code
version: the commit tagged `prereg-v1` (any later bug fix is listed in
DEVIATIONS).

## Unit and metric

- Metric: nDCG@10. Also reported: Recall@10, MRR.
- Unit of analysis: the **prompt**. For each prompt the scores of all its writers
  are averaged first, so that popular prompts do not weigh more.
- Primary set: core prompts with at least **3 writers**. Secondary: all prompts.
- Intervals: 95% bootstrap over prompts, 2,000 resamples, seed 13. Differences
  between systems use a paired bootstrap on the same prompts.

## Primary hypotheses

Three confirmatory tests, Holm-corrected together (family-wise alpha 0.05).

- **H1.** On volunteer-written queries, plain BM25 scores lower nDCG@10 than on
  the constructed queries for the same prompts (the exact words of the passage).
  We expect a relative loss of at least 25%. (On Dakshina, with spellings sampled
  from other writers, it was 46.3% at full respelling; volunteers are the real
  test of whether that transfers.)
- **H2.** `bm25-l3` (phonetic normaliser) has higher nDCG@10 than plain `bm25` on
  volunteer queries: the paired difference is positive with a confidence interval
  that excludes zero.
- **H3.** `bm25-l4` (vowel-class normaliser) differs from `bm25-l3`. Two-sided; no
  direction is claimed. Level 4 was chosen on the Dakshina data, so this is its
  first honest test.

If H1 fails (loss under 25%), that is reported as the finding: spelling variation
matters less than assumed for this kind of query.

## Secondary and descriptive (no hypothesis tests)

- Worst-writer nDCG and writer-to-writer agreement (Jaccard of top-10) per system.
- Differences by group (age group, province, mother tongue, device, frequency).
  Groups with fewer than 5 writers are not reported. City and e-mail are never
  used or published.
- Sensitivity: relevance with grade 1 (sentences containing all query words) added;
  relevance from pooled human judging if done (`judge-sheet`, two judges, with
  Cohen's kappa on a 100-query sample reported).
- Query length and share of words with a known alternative spelling.

## What the paper may not claim

- Results are for **single-sentence passages** and queries written from a shown
  sentence, not for real information needs over long documents.
- Volunteers are a convenience sample, recruited online; they are not
  representative of all Roman Urdu writers.
- Normaliser levels were designed on Dakshina; only H3 is a fresh test of level 4.

## Deviations

Everything done differently from this plan is listed in `docs/DEVIATIONS.md`
(create it when the first deviation happens; the file's absence in the final
repository means there were none).
