# Hijje evaluation: dakshina_ur

**Collection built with 4-word queries, collection seed 21.** Respelling from people's spellings (lexicon train file); all other settings as in results/dakshina_ur_human.

9759 documents, 1000 queries, 5 respelled variants per query per rate, seed 13, hijje 0.4.0.

Queries were respelled only with spellings that people wrote for the same word.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.993 | 0.990–0.996 | 0.899 | 9.4% | 0.538 | 45.8% | 0.502 | 0.241 |
| bm25-l2 | 0.987 | 0.981–0.992 | 0.948 | 3.9% | 0.836 | 15.3% | 0.708 | 0.512 |
| bm25-l3 | 0.974 | 0.965–0.982 | 0.961 | 1.4% | 0.942 | 3.3% | 0.907 | 0.813 |
| bm25-l4 | 0.980 | 0.973–0.987 | 0.965 | 1.6% | 0.938 | 4.3% | 0.882 | 0.718 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.997 | 0.961 | 0.690 |
| bm25-l2 | 0.994 | 0.978 | 0.911 |
| bm25-l3 | 0.986 | 0.981 | 0.971 |
| bm25-l4 | 0.991 | 0.984 | 0.970 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | -0.006 [-0.010, -0.002] | +0.049 [+0.041, +0.057] | +0.298 [+0.276, +0.320] |
| bm25-l3 | -0.019 [-0.026, -0.012] | +0.061 [+0.051, +0.072] | +0.404 [+0.377, +0.431] |
| bm25-l4 | -0.013 [-0.018, -0.008] | +0.066 [+0.056, +0.075] | +0.400 [+0.375, +0.425] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.
