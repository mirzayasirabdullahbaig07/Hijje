# Hijje evaluation: dakshina_ur

9759 documents, 1000 queries, 5 respelled variants per query per rate, seed 13, hijje 0.4.0.

Queries were respelled only with spellings that people wrote for the same word.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.993 | 0.990–0.996 | 0.900 | 9.4% | 0.533 | 46.3% | 0.498 | 0.252 |
| bm25-l2 | 0.988 | 0.983–0.992 | 0.953 | 3.5% | 0.836 | 15.4% | 0.697 | 0.516 |
| bm25-l3 | 0.977 | 0.969–0.983 | 0.959 | 1.8% | 0.938 | 3.9% | 0.899 | 0.810 |
| bm25-l4 | 0.985 | 0.979–0.990 | 0.970 | 1.5% | 0.934 | 5.2% | 0.875 | 0.717 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.995 | 0.961 | 0.692 |
| bm25-l2 | 0.993 | 0.982 | 0.920 |
| bm25-l3 | 0.989 | 0.983 | 0.976 |
| bm25-l4 | 0.992 | 0.988 | 0.972 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | -0.006 [-0.009, -0.003] | +0.053 [+0.045, +0.061] | +0.303 [+0.281, +0.326] |
| bm25-l3 | -0.017 [-0.023, -0.011] | +0.059 [+0.049, +0.069] | +0.405 [+0.379, +0.432] |
| bm25-l4 | -0.009 [-0.014, -0.005] | +0.070 [+0.060, +0.079] | +0.401 [+0.376, +0.426] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.
