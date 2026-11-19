# Cleaning report

| Step | Rows |
|---|---|
| rows read | 1912 |
| dropped: skipped or empty | 250 |
| dropped: typed in Urdu script, not Roman | 63 |
| dropped: longer than 200 characters | 12 |
| dropped: writers with fewer than 4 usable answers | 3 |
| dropped: rows of those writers | 4 |
| rows kept | 1561 |
| writers | 111 |
| prompts answered | 444 |
| dropped: the researcher's own test answers | 40 |
| dropped: unrelated to the sentence | 169 |
| rows kept after cleaning | 1352 |
| writers after cleaning | 102 |
| prompts after cleaning | 429 |

Answer types (after the plan's rules):

| Type | Answers | Share |
|---|---|---|
| transliteration | 1096 | 72% |
| keywords | 58 | 4% |
| other | 198 | 13% |
| unrelated | 169 | 11% |

# Volunteer data: confirmatory analysis

35 prompts with at least 3 writers whose answers contain the 4 constructed words. Queries: 314 (B, volunteer words), 552 (C, as written). nDCG@10, averaged over a prompt's writers first, 95% bootstrap intervals over prompts.

| System | A constructed | B volunteer's spelling | C as written |
|---|---|---|---|
| bm25 | 1.000 (1.000–1.000) | 0.769 (0.698–0.836) | 0.909 (0.876–0.938) |
| bm25-l1 | 1.000 (1.000–1.000) | 0.886 (0.826–0.937) | 0.943 (0.926–0.960) |
| bm25-l2 | 1.000 (1.000–1.000) | 0.936 (0.900–0.968) | 0.958 (0.941–0.974) |
| bm25-l3 | 1.000 (1.000–1.000) | 0.994 (0.988–1.000) | 0.972 (0.960–0.984) |
| bm25-l4 | 1.000 (1.000–1.000) | 0.961 (0.923–0.991) | 0.968 (0.954–0.981) |
| char | 0.989 (0.968–1.000) | 0.928 (0.891–0.963) | 0.954 (0.939–0.969) |
| fusion | 1.000 (1.000–1.000) | 0.913 (0.880–0.946) | 0.945 (0.925–0.964) |

## Planned tests (Holm-corrected together)

| Test | Estimate (95% CI) | p | Holm p | Result |
|---|---|---|---|---|
| H1: BM25: constructed words (A) vs the volunteers' spelling of the same words (B) | +0.231 (+0.164 to +0.307); relative loss 23.1% (16.1–30.7%) | 0.0000 | 0.0000 | significant |
| H2: bm25-l3 minus bm25 on the volunteers' words (B) | +0.226 (+0.161 to +0.301) | 0.0000 | 0.0000 | significant |
| H3: bm25-l4 minus bm25-l3 on the volunteers' words (B) | -0.033 (-0.069 to -0.005) | 0.0070 | 0.0070 | significant |

Descriptive: answers exactly as written (C) lose 9.1% (6.3–12.5%) of BM25's nDCG@10 relative to the constructed 4-word queries. C mostly contains whole sentences, so it is not a keyword-search condition.
