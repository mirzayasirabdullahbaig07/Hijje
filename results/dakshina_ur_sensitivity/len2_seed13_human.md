# Hijje evaluation: dakshina_ur

**Collection built with 2-word queries, collection seed 13.** Respelling from people's spellings (lexicon train file); all other settings as in results/dakshina_ur_human.

9759 documents, 1000 queries, 5 respelled variants per query per rate, seed 13, hijje 0.4.0.

Queries were respelled only with spellings that people wrote for the same word.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.973 | 0.967–0.978 | 0.632 | 35.1% | 0.427 | 56.1% | 0.413 | 0.339 |
| bm25-l2 | 0.943 | 0.934–0.953 | 0.723 | 23.4% | 0.632 | 33.0% | 0.501 | 0.613 |
| bm25-l3 | 0.837 | 0.820–0.855 | 0.743 | 11.3% | 0.712 | 14.9% | 0.625 | 0.855 |
| bm25-l4 | 0.918 | 0.905–0.930 | 0.778 | 15.3% | 0.723 | 21.2% | 0.601 | 0.771 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.986 | 0.843 | 0.544 |
| bm25-l2 | 0.979 | 0.885 | 0.781 |
| bm25-l3 | 0.924 | 0.851 | 0.824 |
| bm25-l4 | 0.971 | 0.900 | 0.852 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | -0.029 [-0.037, -0.023] | +0.091 [+0.075, +0.107] | +0.205 [+0.183, +0.225] |
| bm25-l3 | -0.136 [-0.152, -0.119] | +0.111 [+0.089, +0.133] | +0.285 [+0.256, +0.315] |
| bm25-l4 | -0.055 [-0.065, -0.045] | +0.146 [+0.126, +0.165] | +0.296 [+0.270, +0.322] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.
