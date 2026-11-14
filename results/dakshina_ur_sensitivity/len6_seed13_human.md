# Hijje evaluation: dakshina_ur

**Collection built with 6-word queries, collection seed 13.** Respelling from people's spellings (lexicon train file); all other settings as in results/dakshina_ur_human.

9759 documents, 1000 queries, 5 respelled variants per query per rate, seed 13, hijje 0.4.0.

Queries were respelled only with spellings that people wrote for the same word.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.996 | 0.994–0.998 | 0.959 | 3.7% | 0.586 | 41.2% | 0.541 | 0.206 |
| bm25-l2 | 0.993 | 0.989–0.996 | 0.984 | 0.9% | 0.924 | 7.0% | 0.841 | 0.455 |
| bm25-l3 | 0.987 | 0.981–0.992 | 0.984 | 0.3% | 0.976 | 1.1% | 0.960 | 0.761 |
| bm25-l4 | 0.990 | 0.985–0.995 | 0.987 | 0.3% | 0.977 | 1.3% | 0.959 | 0.666 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.998 | 0.983 | 0.732 |
| bm25-l2 | 0.995 | 0.992 | 0.961 |
| bm25-l3 | 0.993 | 0.992 | 0.990 |
| bm25-l4 | 0.994 | 0.993 | 0.990 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | -0.003 [-0.007, -0.001] | +0.025 [+0.019, +0.030] | +0.338 [+0.314, +0.362] |
| bm25-l3 | -0.009 [-0.014, -0.005] | +0.025 [+0.018, +0.031] | +0.391 [+0.363, +0.416] |
| bm25-l4 | -0.006 [-0.010, -0.002] | +0.028 [+0.022, +0.034] | +0.392 [+0.367, +0.418] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.
