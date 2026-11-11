# Spelling-variation rules

This file documents how `hijje` respells Roman Urdu words, and how to check
whether those respellings are realistic.

The rules are a **model written from documented patterns and common texting
usage. They have not yet been validated by native speakers or against a
corpus.** Treat every number produced with them as provisional until the
review described at the bottom of this file is done.

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
| `final_e_y` | final 'e' or 'i' written as 'ay' or 'y' | mujhe → mujhy | 1.0 |
| `glide_y` | 'y' glide written as 'i' or 'iy' and back | kya → kia | 1.0 |
| `final_h` | silent final 'h' dropped | jagah → jaga | 1.0 |
| `aspirate_h` | aspirate 'h' dropped after b, d, j, t | mujhe → muje | 0.7 |
| `ph_f` | 'ph' written as 'f' | phir → fir | 1.0 |
| `nasal_n` | nasal ending respelled or dropped | nahin → nahi | 1.0 |
| `w_v` | 'w' and 'v' swapped | wajah → vajah | 0.5 |
| `q_k` | 'q' written as 'k' | waqt → wakt | 1.0 |
| `vowel_drop` | texting style: short vowel dropped | karna → krna | 0.5 |

**Weight** is how often a rule is picked relative to the others when several
rules can change the same word. The weights are guesses. Replace them with
frequencies counted from real text when a corpus is available.

### The word list (`lexicon`)

Very frequent words (hai, nahi, kya, mein, ke, …) have habitual short forms
that no general rule predicts: "hai" → "hy", "aur" → "r", "kyun" → "q". These
are listed by hand: 60 words, 154 alternate spellings, weight 3.0. Print the
full list with:

```bash
hijje rules --lexicon
```

## What the rules get wrong

Known weaknesses, so that a reviewer does not have to rediscover them:

1. **Vowel length is not visible in the spelling.** `vowel_drop` removes the
   first short-looking vowel between two consonants in words of 3–5 letters.
   It cannot tell that the "a" in "pani" is long, so it produces "pni", which
   is rarer than "krna" for "karna".
2. **"ai" is two different sounds.** In "kaise" it is one vowel and "kese" is
   common. In "faida" it is a + i, and the rule's output "feda" is doubtful.
3. **Aspirate dropping can change the word.** "saath" (with) → "saat" (seven).
   People do this, but less often than the rule's weight may suggest.
4. **English loanwords are not detected.** Rules written for Urdu sounds give
   forms nobody writes when applied to English words ("phone" → "phony"). The
   current fix is a hand-made `protected_terms.txt` per dataset. A larger
   dataset needs automatic word-level language identification.
5. **One dialect, one writer's intuition.** Spelling habits differ between
   Pakistan and India, between cities, and between age groups. The rules lean
   towards Pakistani chat style.
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

## Changing a rule

1. Edit the rule in `src/hijje/variation.py` and its row in the table above.
2. Run `pytest`. `test_golden_output_guards_reproducibility` will fail if the
   change alters previously generated variants. That is expected: update the
   expected text **and** bump the version in `pyproject.toml` and
   `src/hijje/__init__.py`, because results made with the old rules can no
   longer be reproduced with the new ones.
3. Re-run the experiment and report the version used.
