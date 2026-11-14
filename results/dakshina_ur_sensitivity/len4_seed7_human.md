# Hijje evaluation: dakshina_ur

**Collection built with 4-word queries, collection seed 7.** Respelling from people's spellings (lexicon train file); all other settings as in results/dakshina_ur_human.

9759 documents, 1000 queries, 5 respelled variants per query per rate, seed 13, hijje 0.4.0.

Queries were respelled only with spellings that people wrote for the same word.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.992 | 0.988–0.995 | 0.889 | 10.3% | 0.515 | 48.0% | 0.481 | 0.245 |
| bm25-l2 | 0.989 | 0.984–0.993 | 0.952 | 3.7% | 0.821 | 16.9% | 0.690 | 0.514 |
| bm25-l3 | 0.971 | 0.962–0.979 | 0.957 | 1.4% | 0.934 | 3.8% | 0.886 | 0.807 |
| bm25-l4 | 0.980 | 0.973–0.986 | 0.964 | 1.7% | 0.932 | 4.9% | 0.873 | 0.725 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.996 | 0.950 | 0.662 |
| bm25-l2 | 0.995 | 0.980 | 0.897 |
| bm25-l3 | 0.986 | 0.982 | 0.973 |
| bm25-l4 | 0.991 | 0.983 | 0.965 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | -0.003 [-0.006, -0.000] | +0.063 [+0.054, +0.071] | +0.306 [+0.283, +0.328] |
| bm25-l3 | -0.021 [-0.027, -0.014] | +0.068 [+0.057, +0.078] | +0.419 [+0.393, +0.446] |
| bm25-l4 | -0.011 [-0.016, -0.007] | +0.074 [+0.064, +0.084] | +0.416 [+0.391, +0.443] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.
