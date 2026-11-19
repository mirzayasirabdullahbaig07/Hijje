# Deviations from the analysis plan

Plan: [PREREGISTRATION.md](PREREGISTRATION.md), tag `prereg-v1`. Data: the Google
Sheet export of 19 November 2026 (1,912 rows, 122 writers). Everything below was
decided **after looking at the answers' text and before running any retrieval
system on them**. The first retrieval run on volunteer data was made after
D1 to D4 were fixed in code (`src/hijje/clean.py`, `src/hijje/confirm.py`).

## D1. What the volunteers wrote is mostly not a search

The form asked people to type "the search you would use". About **72% of the
cleaned answers are the whole Urdu sentence written out in Roman Urdu**, 4% are
short keyword searches, 13% are other, long or mixed answers. The plan's H1 compared
"volunteer queries" with 4-word constructed queries; with whole sentences as
queries that comparison is not meaningful (long queries are easy).

Change: the primary condition (**B**) keeps the plan's 4 constructed words but
takes them in **the volunteer's own spelling**, read from the volunteer's whole-sentence
answer by a fuzzy word alignment. Answers exactly as typed (**C**) are reported as a
descriptive extra. Condition A (constructed words) is unchanged.

Consequence for the paper: the results describe **spelling variation of the same
words written by different people**, not what people type when searching. A
keyword-search collection still needs to be made (D7).

## D2. Answers unrelated to the sentence are dropped

169 answers (11%) share no word of four or more letters with their sentence
("yes", "hah", "nothing", random keys, a different sentence). Rule:
`clean.classify` returns `unrelated`. Condition B uses only answers that wrote out
the sentence, so this rule does not change B; it changes C and the counts.

## D3. Word-matching threshold

Two words count as the same word at string similarity 0.7 (`MATCH_SIM`), chosen
before the first retrieval run. A stricter 0.8, run afterwards as a check
(`results/volunteers_primary/sensitivity_match_sim_0.8.md`), leaves 27 prompts
instead of 35; H1 loss 20.1% (11.2 to 30.0%), H2 unchanged, **H3 becomes not
significant** (difference −0.023, interval −0.056 to +0.002). So the H3 result
depends on the threshold; see "Results".

## D4. The primary set

Plan: core prompts with at least 3 writers. Here "writer" means a writer whose
answer wrote all 4 constructed words, so that B exists for them: **35 of the 40
core prompts**. All prompts with at least 3 such writers (57) are in
`results/volunteers_all_prompts/`.

## D5. Exclusions

Author's own test answers (two writer codes, 40 answers) removed, as planned.
Beyond the plan: nothing except D2. The three rows in which an answer belongs to a
different sentence than the prompt it was sent under were found by D2.

## D6. Profile questions were not recorded

The export has device, province and frequency but none of age group, city, mother
tongue or education, and no contact list. The form sent them, but the script
version running at the time did not store them. Analyses by those groups are not
possible for these rows.

## D7. Elicitation design error (ours)

The instruction led most people to copy the sentence. For a keyword-search
condition a second collection is needed, with an instruction such as "write 3 to
6 words you would type to find this sentence" and an example. This is a new
condition and will be reported as such, not mixed with this data.

## Results against the plan (one-line each)

- **H1** (loss at least 25%): loss 23.1% (95% CI 16.1 to 30.7%). The loss is
  significant (Holm p < 0.001) but the estimate is below the 25% expected in the
  plan and the interval contains 25%: the size is not settled.
- **H2** (level 3 beats plain BM25): supported, +0.226 nDCG@10 (CI +0.161 to +0.301).
- **H3** (level 4 differs from level 3): level 4 is lower, −0.033 (CI −0.069 to
  −0.005), Holm p = 0.007; not significant at the stricter threshold of D3.
