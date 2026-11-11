# Seed dataset

A small Roman Urdu retrieval set for checking that the pipeline works.
**It is not a benchmark and its numbers are not research results.**

| | |
|---|---|
| Passages | 48 (12 everyday topics, 4 passages each) |
| Queries | 48, one written for each passage |
| Relevance labels | 51: grade 2 for the passage a query was written for, grade 1 for three partly relevant passages |
| Protected terms | 72 English loanwords that the variation model must not respell |
| Format | BEIR (`corpus.jsonl`, `queries.jsonl`, `qrels.tsv`) |

## How it was made

The passages and queries were drafted with an AI assistant in one consistent
spelling style. They have **not yet been reviewed by a native speaker**. Fix
anything unnatural and note the change in the git history.

The passages are test fixtures written to have distinctive vocabulary. They
are not advice: do not rely on them for health, safety, money or travel
decisions.

## Known limits

- Too small and too easy. Exact-match BM25 scores about 0.99 nDCG@10 on the
  clean queries, so there is no room to show an improvement on clean text.
- With 48 passages, merging different words rarely causes a wrong match. The
  strongest normalisation therefore looks better here than it will on a real
  corpus.
- Queries share words with their passage by construction. Real users
  paraphrase more.
- One spelling convention, chosen by the drafter.

## Licence

Same licence as the code (MIT) unless the repository owner decides otherwise.
