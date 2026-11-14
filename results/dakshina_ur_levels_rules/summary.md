# Hijje evaluation: dakshina_ur

9759 documents, 1000 queries, 5 respelled variants per query per rate, seed 13, hijje 0.4.0.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.993 | 0.990–0.996 | 0.879 | 11.5% | 0.420 | 57.7% | 0.409 | 0.211 |
| bm25-l2 | 0.988 | 0.983–0.992 | 0.981 | 0.7% | 0.966 | 2.2% | 0.955 | 0.759 |
| bm25-l3 | 0.977 | 0.969–0.983 | 0.974 | 0.2% | 0.972 | 0.5% | 0.970 | 0.967 |
| bm25-l4 | 0.985 | 0.979–0.990 | 0.976 | 0.9% | 0.959 | 2.6% | 0.943 | 0.749 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.995 | 0.944 | 0.564 |
| bm25-l2 | 0.993 | 0.991 | 0.986 |
| bm25-l3 | 0.989 | 0.988 | 0.986 |
| bm25-l4 | 0.992 | 0.989 | 0.981 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | -0.006 [-0.009, -0.003] | +0.102 [+0.093, +0.112] | +0.546 [+0.518, +0.572] |
| bm25-l3 | -0.017 [-0.023, -0.011] | +0.095 [+0.085, +0.105] | +0.552 [+0.526, +0.578] |
| bm25-l4 | -0.009 [-0.014, -0.005] | +0.097 [+0.087, +0.106] | +0.538 [+0.513, +0.565] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.
