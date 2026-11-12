# Hijje evaluation: seed

48 documents, 48 queries, 5 respelled variants per query per rate, seed 13, hijje 0.1.0.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.993 | 0.982–1.000 | 0.919 | 7.4% | 0.634 | 36.2% | 0.634 | 0.275 |
| bm25-l2 | 0.993 | 0.982–1.000 | 0.985 | 0.7% | 0.970 | 2.2% | 0.962 | 0.690 |
| char | 0.985 | 0.966–1.000 | 0.970 | 1.6% | 0.962 | 2.3% | 0.935 | 0.491 |
| dense:intfloat/multilingual-e5-small | 0.803 | 0.722–0.880 | 0.730 | 9.1% | 0.672 | 16.3% | 0.607 | 0.602 |
| dense:intfloat/multilingual-e5-base | 0.881 | 0.803–0.955 | 0.811 | 8.0% | 0.706 | 19.9% | 0.588 | 0.537 |
| dense:BAAI/bge-m3 | 0.957 | 0.919–0.990 | 0.913 | 4.6% | 0.856 | 10.6% | 0.785 | 0.556 |
| dense:sentence-transformers/LaBSE | 0.902 | 0.828–0.962 | 0.837 | 7.2% | 0.761 | 15.6% | 0.671 | 0.622 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.979 | 0.952 | 0.708 |
| bm25-l2 | 0.979 | 0.981 | 0.983 |
| char | 0.979 | 0.979 | 0.979 |
| dense:intfloat/multilingual-e5-small | 0.948 | 0.883 | 0.775 |
| dense:intfloat/multilingual-e5-base | 0.917 | 0.883 | 0.819 |
| dense:BAAI/bge-m3 | 0.990 | 0.973 | 0.956 |
| dense:sentence-transformers/LaBSE | 0.948 | 0.935 | 0.910 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | +0.000 [+0.000, +0.000] | +0.066 [+0.033, +0.104] | +0.337 [+0.214, +0.459] |
| char | -0.008 [-0.023, +0.000] | +0.050 [+0.026, +0.076] | +0.328 [+0.212, +0.451] |
| dense:intfloat/multilingual-e5-small | -0.190 [-0.276, -0.113] | -0.189 [-0.276, -0.106] | +0.038 [-0.089, +0.167] |
| dense:intfloat/multilingual-e5-base | -0.111 [-0.192, -0.039] | -0.109 [-0.188, -0.037] | +0.073 [-0.024, +0.174] |
| dense:BAAI/bge-m3 | -0.036 [-0.074, -0.004] | -0.007 [-0.041, +0.030] | +0.222 [+0.123, +0.326] |
| dense:sentence-transformers/LaBSE | -0.091 [-0.162, -0.030] | -0.082 [-0.142, -0.027] | +0.128 [+0.027, +0.237] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.

## Which kind of respelling hurts

Change in nDCG@10 when a single rule is applied to every word it can change, measured only on the queries that rule changes.

| Rule | Example | Queries changed | bm25 | bm25-l2 | char | dense:intfloat/multilingual-e5-small | dense:intfloat/multilingual-e5-base | dense:BAAI/bge-m3 | dense:sentence-transformers/LaBSE |
|---|---|---|---|---|---|---|---|---|---|
| lexicon | word list | 48 | +0.000 | +0.004 | +0.000 | -0.083 | -0.036 | -0.006 | -0.039 |
| long_a | baat → bat | 16 | -0.031 | +0.000 | -0.008 | -0.002 | -0.075 | -0.075 | -0.023 |
| long_i | theek → thik | 31 | -0.032 | +0.000 | -0.011 | -0.046 | -0.014 | -0.018 | +0.004 |
| long_u | poora → pura | 6 | -0.062 | +0.000 | +0.000 | -0.056 | +0.000 | -0.062 | +0.000 |
| degeminate | achha → acha | 2 | -0.185 | +0.000 | +0.000 | -0.011 | +0.000 | +0.000 | +0.000 |
| ai_e | kaise → kese | 30 | +0.000 | +0.000 | +0.000 | -0.045 | -0.030 | -0.025 | -0.028 |
| au_o | aur → or | 5 | +0.000 | +0.000 | +0.000 | -0.069 | +0.077 | +0.040 | -0.074 |
| final_e_y | mujhe → mujhy | 46 | -0.009 | +0.000 | -0.001 | -0.090 | -0.062 | -0.017 | -0.062 |
| glide_y | kya → kia | 26 | +0.000 | +0.000 | +0.000 | -0.073 | -0.056 | -0.002 | -0.031 |
| final_h | jagah → jaga | 2 | -0.152 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| aspirate_h | mujhe → muje | 7 | -0.105 | +0.000 | +0.000 | -0.100 | +0.006 | -0.071 | +0.000 |
| ph_f | phir → fir | 0 | – | – | – | – | – | – | – |
| nasal_n | nahin → nahi | 33 | -0.028 | +0.000 | +0.000 | -0.056 | -0.046 | +0.000 | -0.099 |
| w_v | wajah → vajah | 8 | -0.043 | +0.000 | -0.038 | +0.000 | +0.005 | +0.026 | -0.079 |
| q_k | waqt → wakt | 8 | +0.000 | +0.000 | +0.000 | +0.009 | -0.021 | +0.025 | -0.105 |
| vowel_drop | karna → krna | 39 | -0.043 | -0.043 | -0.001 | -0.068 | -0.078 | -0.054 | -0.049 |
