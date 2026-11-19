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

57 prompts with at least 3 writers whose answers contain the 4 constructed words. Queries: 388 (B, volunteer words), 631 (C, as written). nDCG@10, averaged over a prompt's writers first, 95% bootstrap intervals over prompts.

| System | A constructed | B volunteer's spelling | C as written |
|---|---|---|---|
| bm25 | 1.000 (1.000–1.000) | 0.768 (0.697–0.833) | 0.910 (0.873–0.940) |
| bm25-l1 | 1.000 (1.000–1.000) | 0.898 (0.850–0.939) | 0.960 (0.945–0.972) |
| bm25-l2 | 1.000 (1.000–1.000) | 0.956 (0.934–0.979) | 0.974 (0.962–0.985) |
| bm25-l3 | 1.000 (1.000–1.000) | 0.997 (0.992–1.000) | 0.983 (0.974–0.991) |
| bm25-l4 | 1.000 (1.000–1.000) | 0.976 (0.953–0.995) | 0.981 (0.971–0.990) |
| char | 0.987 (0.968–1.000) | 0.929 (0.892–0.960) | 0.970 (0.959–0.980) |
| fusion | 1.000 (1.000–1.000) | 0.888 (0.836–0.935) | 0.949 (0.926–0.970) |

## Planned tests (Holm-corrected together)

| Test | Estimate (95% CI) | p | Holm p | Result |
|---|---|---|---|---|
| H1: BM25: constructed words (A) vs the volunteers' spelling of the same words (B) | +0.232 (+0.166 to +0.301); relative loss 23.2% (16.8–30.1%) | 0.0000 | 0.0000 | significant |
| H2: bm25-l3 minus bm25 on the volunteers' words (B) | +0.228 (+0.159 to +0.304) | 0.0000 | 0.0000 | significant |
| H3: bm25-l4 minus bm25-l3 on the volunteers' words (B) | -0.020 (-0.042 to -0.003) | 0.0070 | 0.0070 | significant |

Descriptive: answers exactly as written (C) lose 9.0% (5.9–12.7%) of BM25's nDCG@10 relative to the constructed 4-word queries. C mostly contains whole sentences, so it is not a keyword-search condition.
