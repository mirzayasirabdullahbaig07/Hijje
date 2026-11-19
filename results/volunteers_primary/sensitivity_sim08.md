# Volunteer data: confirmatory analysis

27 prompts with at least 3 writers whose answers contain the 4 constructed words. Queries: 194 (B, volunteer words), 448 (C, as written). nDCG@10, averaged over a prompt's writers first, 95% bootstrap intervals over prompts.

| System | A constructed | B volunteer's spelling | C as written |
|---|---|---|---|
| bm25 | 1.000 (1.000–1.000) | 0.799 (0.705–0.887) | 0.927 (0.896–0.953) |
| bm25-l3 | 1.000 (1.000–1.000) | 0.998 (0.993–1.000) | 0.979 (0.968–0.989) |
| bm25-l4 | 1.000 (1.000–1.000) | 0.975 (0.941–1.000) | 0.973 (0.960–0.984) |

## Planned tests (Holm-corrected together)

| Test | Estimate (95% CI) | p | Holm p | Result |
|---|---|---|---|---|
| H1: BM25: constructed words (A) vs the volunteers' spelling of the same words (B) | +0.201 (+0.118 to +0.296); relative loss 20.1% (11.2–30.0%) | 0.0000 | 0.0000 | significant |
| H2: bm25-l3 minus bm25 on the volunteers' words (B) | +0.198 (+0.116 to +0.291) | 0.0000 | 0.0000 | significant |
| H3: bm25-l4 minus bm25-l3 on the volunteers' words (B) | -0.023 (-0.056 to +0.002) | 0.1010 | 0.1010 | not significant |

Descriptive: answers exactly as written (C) lose 7.3% (4.8–10.3%) of BM25's nDCG@10 relative to the constructed 4-word queries. C mostly contains whole sentences, so it is not a keyword-search condition.
