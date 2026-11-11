# Research plan

The code in this repository is the instrument. This file describes the study
it is meant for, and what still has to be done before anything can be claimed
in a paper.

## The question

> When a person searches in Roman Urdu and spells a word differently from the
> documents, how much worse do retrieval systems get, which kinds of spelling
> difference cause the damage, and what is the cheapest fix that works?

## Why it matters

Roman Urdu has no standard spelling. The same writer may type "nahi", "nhi"
and "nahin" in one conversation. Search engines and RAG systems are built and
tested on text where each word has one spelling. If retrieval silently fails
on respelled queries, every RAG product for Roman Urdu users returns worse
answers to the people who type most informally, and nobody sees it, because
the test sets do not contain the problem.

## Research questions

| | Question | An answer looks like |
|---|---|---|
| RQ1 | How much do lexical and dense retrievers degrade under realistic respelling? | nDCG@10 and Recall@10 on clean vs respelled queries, per retriever, with confidence intervals |
| RQ2 | Which kinds of variation hurt which retrievers? | Per-rule change in nDCG (the "Which kind of respelling hurts" table) |
| RQ3 | Does phonetic normalisation close the gap, and at what level do false merges start to cost more than they save? | bm25-l1/l2/l3 on a large corpus, clean and respelled, plus false-merge counts |
| RQ4 | Is fine-tuning a small dense retriever on respelled queries better than normalisation? | Same table with a fine-tuned model added; training on a free T4 GPU |
| RQ5 | Do synthetic respellings predict what happens with human respellings? | Correlation between the synthetic drop and the human drop across retrievers |

RQ5 decides whether the synthetic generator is a valid research tool. If the
answer is no, the human-written set alone becomes the contribution.

## What would be new, and what would not

Checked on 11 November 2026 with a small number of searches; see
`RELATED_WORK.md`. A full literature review is still required.

Not new: that typos hurt dense retrievers (English); that romanised queries
hurt neural retrieval (Chinese, Russian, standard romanisation); that Roman
Urdu spelling varies; phonetic keys for Roman Urdu; RAG for Urdu script.

Appears to be open: a retrieval benchmark for Roman Urdu whose queries carry
**human-written, non-standard spelling variation**; a per-variation-type
analysis; and a measurement of the normalisation trade-off for retrieval.

The human-written data is the part that is hard for others to produce and
that you can produce for free. Protect time for it.

## Data plan

### Corpus

The 48-passage seed set is only a pipeline check. The study needs thousands of
passages, otherwise false merges cannot hurt and level 3 will always look
perfect.

Candidates to investigate (availability and licence **not yet verified**):

- Roman-Urdu-Parl, a parallel Urdu / Roman Urdu corpus. The LoResMT 2025
  transliteration paper reports using 6.3 million sentence pairs from it.
- Urdu question-answering or passage-ranking datasets (for example the UQA
  dataset used by DR-RAG), romanised by a transliteration model and then
  spot-checked by hand.
- Roman Urdu text you collect yourself from public pages whose terms allow it.

Decision rule: prefer a source with an explicit licence that permits
redistribution, because a benchmark that cannot be shared cannot be cited.

### Queries and relevance labels

Target for a first paper: 300–500 queries with at least one labelled relevant
passage each. Write the labelling guideline down before labelling. Have a
second person label 100 of them and report the agreement.

### Human-written spelling variants

This is the core contribution.

1. Give each writer the query in **Urdu script or as audio**, never in Roman
   letters. Seeing a Roman spelling would copy that spelling into their answer.
2. Ask them to type it in Roman Urdu "the way you would in a WhatsApp message".
3. At least 5 writers per query; more writers matter more than more queries.
4. Record an anonymous writer ID, age band and city. Record nothing else.
5. Tell writers what the text is for and that it will be published; keep their
   consent. Do not collect names or phone numbers in the data file.

A free form tool is enough for this.

## Systems compared

| System | Why it is in the comparison |
|---|---|
| bm25 | Standard lexical baseline; exact matching is what respelling breaks |
| char | Character n-grams: spelling-tolerant with zero language knowledge |
| bm25-l1 / l2 / l3 | Language knowledge as rules, at three strengths |
| fusion | Whether combining views beats the best single view |
| multilingual-e5 (small, base), bge-m3, LaBSE | What RAG systems actually deploy |
| fine-tuned small dense model | The learned alternative to rules (RQ4) |
| transliterate-to-Urdu-script then retrieve | The obvious alternative pipeline; needs a transliteration model |

## Metrics and statistics

- nDCG@10 is the primary metric (comparable with BEIR-style work).
  Recall@10 is reported because in RAG a passage outside the top-k is simply
  not seen by the generator.
- Worst-variant nDCG: the lowest score among a query's respellings. A user
  types one spelling, not the average of five.
- Stability: overlap of the clean and respelled top-k.
- 95% bootstrap confidence intervals over queries; paired bootstrap for
  differences between systems.
- Fix the seed, the code version and the rule version in every reported table.

## Threats to validity

1. **Circularity.** The normaliser and the generator were written by the same
   hand from the same knowledge of Roman Urdu. Good results for normalisation
   on synthetic variants are partly true by construction. Only the human set
   can show a real effect. The normaliser deliberately uses no word list so
   that it at least cannot memorise the generator's lexicon.
2. **Corpus size.** False merges are harmless among 48 passages and may be
   costly among 100,000. Conclusions about level 2 vs level 3 need the large
   corpus.
3. **Clean is an upper bound.** "Clean" queries follow the same spelling
   convention as the documents. Real documents are inconsistent too. A later
   experiment should respell documents as well.
4. **Unvalidated rules.** See `VARIATION_RULES.md`.
5. **Loanwords.** English words are protected by a hand-made list.
6. **One language community.** Results may not transfer to romanised Hindi or
   to other regions' Roman Urdu.

## Compute budget (everything free)

| Work | Where | Note |
|---|---|---|
| All lexical experiments | Laptop CPU | Seconds on the seed set |
| Encoding a corpus with a dense model | Kaggle or Colab GPU | One-off per model; save embeddings to disk |
| Fine-tuning a small dense model | Kaggle or Colab GPU | Use a small model; checkpoint often, sessions are time-limited |

Free GPU quotas change. Check the current limits before planning a long run.

## Milestones

Each one ends with something that exists, not with time spent.

| | Milestone | Done when |
|---|---|---|
| M0 | Instrument | Tests pass; seed run reproduces `results/seed/summary.md` (done) |
| M1 | Rules reviewed | `review-stats` table filled by two native speakers; rules revised |
| M2 | Dense baselines on seed | `notebooks/dense_baselines.ipynb` run; table added to README |
| M3 | Literature review | 20–30 papers summarised in `RELATED_WORK.md`; gap statement rewritten |
| M4 | Real corpus | Thousands of passages with a clear licence, loaded in BEIR format |
| M5 | Queries and labels | 300+ queries, labelling guideline, agreement on a 100-query sample |
| M6 | Human variants | 5+ writers per query collected with the protocol above |
| M7 | Experiments | All systems, all metrics, synthetic and human, on the real corpus |
| M8 | Paper | Draft reviewed by someone who has published before |

Ask for academic feedback at M3, before the expensive data work, not at M8.

## Publication route and cost

Not verified today; check each item on its official page.

- Preprint servers and data repositories let you make the work public without
  a fee. arXiv may require an endorsement for first-time authors.
- The closest related papers found on 11 November 2026 appeared in workshops
  on low-resource and South Asian language processing (CHiPSAL, LoResMT,
  LowResNLP). Workshops are a realistic first target. Check whether a venue
  charges a registration fee for the presenting author and whether it offers
  waivers.
- Avoid any journal that promises fast or guaranteed acceptance for a fee.

## Use of AI assistance

The first version of this code, the rules and the seed passages were drafted
with an AI assistant. Most venues require this to be disclosed and hold the
authors responsible for everything submitted. Review all of it yourself, and
do not present the seed passages as human-written data.
