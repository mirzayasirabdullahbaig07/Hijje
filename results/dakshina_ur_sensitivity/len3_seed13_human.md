# Hijje evaluation: dakshina_ur

**Collection built with 3-word queries, collection seed 13.** Respelling from people's spellings (lexicon train file); all other settings as in results/dakshina_ur_human.

9759 documents, 1000 queries, 5 respelled variants per query per rate, seed 13, hijje 0.4.0.

Queries were respelled only with spellings that people wrote for the same word.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.987 | 0.983–0.991 | 0.822 | 16.7% | 0.481 | 51.3% | 0.455 | 0.283 |
| bm25-l2 | 0.978 | 0.972–0.984 | 0.891 | 8.9% | 0.742 | 24.2% | 0.602 | 0.555 |
| bm25-l3 | 0.948 | 0.937–0.958 | 0.903 | 4.7% | 0.866 | 8.6% | 0.800 | 0.824 |
| bm25-l4 | 0.972 | 0.964–0.979 | 0.928 | 4.5% | 0.865 | 11.0% | 0.775 | 0.741 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.992 | 0.927 | 0.627 |
| bm25-l2 | 0.988 | 0.957 | 0.865 |
| bm25-l3 | 0.980 | 0.958 | 0.931 |
| bm25-l4 | 0.985 | 0.968 | 0.931 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | -0.009 [-0.014, -0.005] | +0.068 [+0.059, +0.079] | +0.261 [+0.239, +0.282] |
| bm25-l3 | -0.039 [-0.048, -0.031] | +0.081 [+0.067, +0.096] | +0.385 [+0.357, +0.412] |
| bm25-l4 | -0.016 [-0.022, -0.011] | +0.105 [+0.093, +0.117] | +0.384 [+0.359, +0.409] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.
