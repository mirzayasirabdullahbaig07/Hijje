# Spelling-variation rules

This file documents how `hijje` respells Roman Urdu words, and how to check
whether those respellings are realistic.

The rules are a **model written from documented patterns and common texting
usage. One native speaker has reviewed a small part of their output (round 1,
below); most of it is still unchecked, and nothing has been counted from a
corpus.** Treat every number produced with them as provisional until the
review described in this file is complete.

Current rule version: **0.2.0**.

## The rules

Printed by `hijje rules`. A test fails if this table and the code disagree.

| Rule | What it models | Example | Weight |
|---|---|---|---|
| `long_a` | long 'aa' written as single 'a' | baat → bat | 1.0 |
| `long_i` | 'ee' written as 'i'; final 'i' written as 'ee' | theek → thik | 1.0 |
| `long_u` | 'oo' written as 'u' | poora → pura | 1.0 |
| `degeminate` | doubled consonant written once | achha → acha | 1.0 |
| `ai_e` | 'ai' inside a word written as 'e'; final 'ai' as 'ay' | kaise → kese | 1.0 |
| `au_o` | 'au' written as 'o' | aur → or | 1.0 |
| `final_e_y` | final 'e' written as 'ay' or 'y' | mujhe → mujhy | 1.0 |
| `glide_y` | 'y' glide written as 'i' or 'iy' and back | kya → kia | 1.0 |
| `final_h` | silent final 'h' dropped | jagah → jaga | 1.0 |
| `ph_f` | 'ph' written as 'f' | phir → fir | 1.0 |
| `nasal_n` | nasal ending respelled or dropped | nahin → nahi | 1.0 |
| `q_k` | 'q' written as 'k' | waqt → wakt | 1.0 |
| `vowel_drop` | texting style: short vowel dropped | karna → krna | 0.5 |

**Weight** is how often a rule is picked relative to the others when several
rules can change the same word. The weights are guesses. Replace them with
frequencies counted from real text when a corpus is available.

### The word list (`lexicon`)

Very frequent words (hai, nahi, kya, mein, ke, …) have habitual short forms
that no general rule predicts: "hai" → "hy", "aur" → "r", "kyun" → "q". These
are listed by hand: 60 words, 149 alternate spellings, weight 3.0. Print the
full list with:

```bash
hijje rules --lexicon
```

## What the rules get wrong

Known weaknesses, so that a reviewer does not have to rediscover them:

1. **Vowel length is not visible in the spelling.** `vowel_drop` removes the
   first short-looking vowel between two consonants in words of 3–5 letters.
   It cannot tell that the "a" in "pani" is long. The reviewer rejected "pni"
   as a typo, so "pani" is now on a hand-made exception list
   (`VOWEL_DROP_EXCEPTIONS`). Other long-vowel words ("khali" → "khli",
   "jati" → "jti", "jane" → "jne", "wale" → "wle") have the same problem and
   have not been judged yet.
2. **"ai" is two different sounds.** In "kaise" it is one vowel and "kese" is
   common. In "faida" it is a + i, and the rule's output "feda" is doubtful.
3. **Dropping "h" is natural only in a few frequent words.** "mujhe" → "muje"
   and "bhi" → "bi" are in the word list. As a general rule it gave "saath" →
   "saat" (seven) and "theek" → "teek", so the general rule was removed in
   round 1.
4. **English loanwords are not detected.** Rules written for Urdu sounds give
   forms nobody writes when applied to English words ("phone" → "phony"). The
   current fix is a hand-made `protected_terms.txt` per dataset. A larger
   dataset needs automatic word-level language identification.
5. **One dialect, one reviewer.** Spelling habits differ between Pakistan and
   India, between cities, and between age groups. After round 1 the rules
   follow Pakistani usage: Indian-style spellings such as "v" for "w" are no
   longer generated.
6. **No frequencies.** The model says a respelling is possible, not how common
   it is.

## How to review the rules (native speaker, about one hour)

1. Run the experiment. It saves every respelled query:

   ```bash
   hijje eval --data data/seed --out results/seed
   ```

2. Make the review sheet, one row per distinct respelling:

   ```bash
   hijje review-sheet --variants results/seed/variants.jsonl --out review/seed.csv
   ```

3. Open `review/seed.csv` in any spreadsheet program. For each row ask:
   **"Would I be unsurprised to see a real person type this word this way?"**
   Write `y` or `n` in the `natural` column. Use `note` for comments.

4. Get the precision of each rule:

   ```bash
   hijje review-stats --sheet review/seed.csv
   ```

5. Act on the result. A rule that is mostly judged unnatural should be
   narrowed or removed. Ask a second person to fill a copy of the sheet
   without seeing yours; the agreement between the two of you is a number
   reviewers of the paper will ask for.

## Review round 1 (12 November 2026, one native speaker from Pakistan)

Done on the 290 respellings produced by rule version 0.1.0. The reviewer
answered in conversation for two groups and four single words; those answers
are recorded in `review/round1_native.csv` (28 rows filled, 262 blank). Rows
marked "answered for the group" were not judged one by one.

| What was asked | Reviewer's answer | Change in 0.2.0 |
|---|---|---|
| A final "i" written as "y": "pani" → "pany", "roti" → "roty" | No. People write "i". | That half of `final_e_y` removed. "achi" → "achy" removed from the word list. |
| "v" for "w": "chawal" → "chaval", "sawal" → "saval" | No. People mostly write "w". | Rule `w_v` removed. "woh" → "vo" removed from the word list. |
| "theek" → "teek", "tik" | Look like misspellings. People write "theek", "theak" or "thk". | "teek" and "tik" removed, "theak" added. Rule `aspirate_h` removed, because it also produced "teek". |
| "tareeqa" → "treeqa" | A misspelling. | Removed from the word list. |
| "pani" → "pni" | Looks like a typo; it is always "pani". | "pani" excluded from `vowel_drop`. |

Three of these changes go beyond the reviewer's literal words and should be
confirmed: removing "achy", removing "vo", and removing the whole
`aspirate_h` rule on the strength of one rejected word plus the AI first pass
(its other outputs, such as "saath" → "saat" and "dhone" → "done", were never
shown to the reviewer).

A test, `test_native_review_round1_decisions_hold`, fails if any rejected
respelling is generated again.

Effect on the seed run: exact-match BM25's loss on fully respelled queries
went from 36.2% to 34.1%. The rejected respellings were making the problem
look slightly worse than the reviewed ones do.

Still open after round 1:

- Final "i" written as "ee" ("pani" → "panee", "kitni" → "kitnee").
- Vowel dropping in words with a long vowel ("khali" → "khli", "jati" → "jti").
- "faida" → "feda", "parhai" → "parhay", "chhat" → "chht", "aaye" → "aayay",
  "nahi" → "nahee".
- Everything else: `review/seed.csv` is the blank sheet for the 252
  respellings produced by rule version 0.2.0.
- A second reviewer.

## The AI first pass (not a review)

`review/seed_ai_firstpass.csv` is the round-1 sheet (rule version 0.1.0)
pre-filled by the AI assistant that wrote the rules: 243 marked natural, 16
marked unnatural, 31 left blank as unsure. It exists to speed up the human review and to point at
rules that look wrong. It is **not** evidence that the rules are realistic:
the judge wrote the rules, is not a native speaker, and did not count anything
from real text. Do not report its numbers in a paper as a native-speaker
review.

What it flagged, and what happened:

- `aspirate_h`: all 6 respellings marked unnatural. The rule was removed in
  round 1 (see above).
- `ai_e`: 2 of 5 marked unnatural ("faida" → "feda", "parhai" → "parhay").
  Not yet answered by a person.
- `final_e_y`: final "-i" written as "-y" marked doubtful. The reviewer
  rejected it.
- `w_v`: all 9 left blank. The reviewer rejected them.

Its other answers are guesses that nobody has confirmed. The second reviewer
should fill a blank sheet without seeing them.

## Changing a rule

1. Edit the rule in `src/hijje/variation.py` and its row in the table above.
2. Run `pytest`. `test_reference_results_reproduce` fails when the change
   alters the generated variants, and `test_golden_output_guards_reproducibility`
   fails when it alters its one fixed sentence. That is expected: bump the
   version in `pyproject.toml` and `src/hijje/__init__.py`, because results
   made with the old rules can no longer be reproduced with the new ones.
3. Re-run the experiment (`hijje eval --data data/seed --out results/seed`),
   update the table in the README, and regenerate `review/seed.csv`. Save any
   filled-in review sheet under another name first, because regenerating
   overwrites it.
4. Re-run the neural notebook, and report the version used.
