# Candidate datasets

Status on 12 November 2026. "Checked" means the dataset's page or paper was
read that day. **None of these has been downloaded or opened yet**: the
machine this project was drafted on cannot reach the hosts. Sizes and licences
below are what the pages say, not what was measured.

## Summary

| Dataset | What it gives this project | Licence | Main doubt |
|---|---|---|---|
| **Dakshina** (Urdu part) | Spellings of 30,000 Urdu words written by native speakers, and 9,759 Urdu sentences written out in Roman letters by native speakers | CC BY-SA 4.0 | Annotators' country is not stated; careful writing, not chat style |
| **Roman-Urdu-Parl** | 6.37 million Urdu / Roman Urdu sentence pairs; some sentences come with 2 to 10 Roman spellings | Apache-2.0 on a third-party copy | Licence of the original not confirmed; how the Roman side was written is not stated |
| **Urdu MS MARCO** | A large search benchmark in Urdu script with relevance labels | Not stated | Machine-translated; MS MARCO's own terms apply |
| **UQA** | Urdu paragraphs with questions, usable as passages and queries | Not stated | No licence file in the repository |

**Start with Dakshina.** It is the only one with a clear licence that also
contains what this project needs most: Roman Urdu spellings that people wrote
without being told how to spell.

## Dakshina (Google Research, 2020)

- Page: <https://github.com/google-research-datasets/dakshina> (checked; the
  repository was archived as read-only in April 2026, the data link is still
  listed).
- Paper: Roark et al., "Processing South Asian Languages Written in the Latin
  Script: the Dakshina Dataset" (<https://arxiv.org/abs/2007.01176>, checked).
- Licence: CC BY-SA 4.0, stated in the repository README. Anything built from
  it must credit it and be shared under the same licence.
- **Lexicon.** 30,000 Urdu words (25,000 train, 2,500 dev, 2,500 test). The
  paper reports 4.2 Roman spellings per Urdu word on average, the highest of
  the twelve languages together with Gujarati. Files:
  `ur/lexicons/ur.translit.sampled.{train,dev,test}.tsv`, one line per
  (Urdu word, Roman spelling, count).
- **The count is not how often people use a spelling.** The paper says it is
  the number of times a spelling was given by annotators, "not a frequency of
  usage".
- **Sentences.** 9,759 Urdu Wikipedia sentences written out in Roman letters
  by native speakers. The paper says annotators were given "no specific
  guidance on romanization strategy" and were asked to write as they would
  when writing in the Latin script. A word-by-word aligned version is
  included: `ur/romanized/ur.romanized.rejoined.aligned.cased_nopunct.tsv`.
- **Limits.** The paper does not say which country the Urdu annotators were
  from, so spellings common in India may be mixed in. The text is Wikipedia
  vocabulary written carefully, so chat short forms ("hy", "kr", "q") are
  unlikely to appear.

How it is used here:

1. **Now:** `notebooks/dakshina_check.ipynb` runs `hijje attested` on it. That
   shows how people's spellings of one word really differ, and for each rule
   what share of its respellings a person also wrote.
2. **Next:** replace the hand-made rule weights with what the data shows, and
   add a second generator that only uses spellings people wrote.
3. **Later:** the 9,759 human-written Roman Urdu sentences can serve as real
   passages.

## Roman-Urdu-Parl (Alam and Hussain, 2022)

- Copy checked: <https://huggingface.co/datasets/Mavkif/Roman-Urdu-Parl-split>.
  The uploader states he is not the original author and only made the splits.
- Size on the card: 6,365,808 rows. The validation and test splits each hold
  1,000 unique sentences plus 2,000 sentences that have 2 to 10 variations.
- Licence on the card: Apache-2.0. **Confirm against the original paper or
  with its authors before redistributing anything derived from it.**
- Not stated on the card: how the Roman Urdu side was produced (people or a
  program), and the column names.
- Possible use: sentences with several Roman spellings are a direct test of
  whether a retriever treats two spellings of one sentence alike.

## Urdu MS MARCO (2024)

- Paper: "Enabling Low-Resource Language Retrieval: Establishing Baselines for
  Urdu MS MARCO" (<https://arxiv.org/abs/2412.12997>, checked). Data:
  `Mavkif/urdu-msmarco-dataset` on Hugging Face (not opened).
- What it is: the MS MARCO passage-ranking dataset machine-translated into
  Urdu script with IndicTrans2. The source has over 8.8 million passages and
  more than 500,000 queries; the development set has 6,980 queries.
- Baselines in the paper (MRR@10): BM25 0.121, zero-shot multilingual reranker
  0.204, fine-tuned 0.248.
- Roman Urdu is not mentioned anywhere in the paper.
- Licence: not stated in the paper. MS MARCO has its own terms of use, which
  need to be read before building on a translation of it.
- Possible use: once queries are written in Roman Urdu, this gives thousands
  of queries with relevance labels over a corpus large enough for false merges
  to matter.

## UQA (LREC-COLING 2024)

- Paper: "UQA: Corpus for Urdu Question Answering"
  (<https://aclanthology.org/2024.lrec-main.1497>, checked). Repository:
  <https://github.com/sameearif/UQA> (checked; no licence file).
- What it is: SQuAD 2.0 translated into Urdu with a method that keeps answer
  spans intact.
- Licence: not stated. SQuAD 2.0 itself is, as recalled and not re-checked,
  CC BY-SA 4.0, which would carry over to a translation.
- Possible use: paragraphs as passages and questions as queries.

## How Hijje uses Dakshina (v0.3.0)

- `hijje attested` compares the rules with its spellings (lexicon and
  sentences). The summaries are in `results/dakshina_lexicon` and
  `results/dakshina_sentences`. The full tables are not committed.
- `hijje build-dakshina` turns `ur.romanized.rejoined.tsv` (9,759 sentences)
  into a BEIR-format collection: every sentence is a passage; for 1,000
  sentences the four most distinctive words (document frequency between 2 and
  2% of sentences, at least 3 letters, ASCII letters only) are the query.
- `--variation attested:<lexicon file>` respells query words with other
  spellings people wrote for the same word, weighted by count. The lexicon
  *train* file is used, not the sentences, so a query is never respelled with
  its own passage's spelling.
- Counts in the lexicon are how many annotators gave a spelling. They are not
  usage frequencies. Counts in the sentences are real usage.
- Not committed: the built collection (`data/dakshina_ur/` is in
  `.gitignore`) and the full tables. Committed: aggregate results with a few
  example words, under the same CC BY-SA 4.0 terms.

Known doubts: the lexicon contains English words and names written in Roman
letters (einstein, idea), which are not Urdu spelling variation in the
usual sense; the annotators' country is not stated; the sentences are
Wikipedia-style writing, not chat.

## Licences, in plain words

- A benchmark that mixes these sources can only be shared under terms that
  satisfy all of them. Dakshina's CC BY-SA 4.0 requires the result to be
  shared under CC BY-SA 4.0 as well.
- "Not stated" does not mean "free to use". Write to the authors and keep the
  reply.
- Reporting numbers measured on a dataset is different from redistributing
  the dataset. The first is normal research use; the second needs the licence.

## Still to check

- Whether anyone has already used Dakshina's Urdu spellings to test search
  systems. This is the closest possible prior work and decides how the paper
  is framed.
- MS MARCO's terms of use, and the licences of UQA and Urdu MS MARCO.
- The original Roman-Urdu-Parl paper: licence and how the Roman side was made.
- Roman Urdu text written in chat style, which none of the above contains.
