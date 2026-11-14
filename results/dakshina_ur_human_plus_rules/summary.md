# Hijje evaluation: dakshina_ur

9759 documents, 1000 queries, 5 respelled variants per query per rate, seed 13, hijje 0.3.0.

Queries were respelled with spellings that people wrote; the hand-written rules were used for words the data lacks.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.993 | 0.990–0.996 | 0.814 | 18.0% | 0.152 | 84.7% | 0.133 | 0.070 |
| bm25-l2 | 0.988 | 0.983–0.992 | 0.948 | 4.0% | 0.812 | 17.8% | 0.659 | 0.493 |
| bm25-l3 | 0.977 | 0.969–0.983 | 0.960 | 1.7% | 0.937 | 4.0% | 0.899 | 0.802 |
| char | 0.976 | 0.970–0.982 | 0.905 | 7.4% | 0.715 | 26.8% | 0.564 | 0.286 |
| fusion | 0.993 | 0.989–0.995 | 0.920 | 7.3% | 0.534 | 46.2% | 0.375 | 0.238 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.995 | 0.909 | 0.230 |
| bm25-l2 | 0.993 | 0.978 | 0.905 |
| bm25-l3 | 0.989 | 0.984 | 0.975 |
| char | 0.993 | 0.980 | 0.896 |
| fusion | 0.995 | 0.977 | 0.780 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | -0.006 [-0.009, -0.003] | +0.134 [+0.124, +0.144] | +0.660 [+0.639, +0.683] |
| bm25-l3 | -0.017 [-0.023, -0.011] | +0.145 [+0.133, +0.156] | +0.785 [+0.763, +0.806] |
| char | -0.017 [-0.022, -0.012] | +0.090 [+0.079, +0.101] | +0.563 [+0.541, +0.586] |
| fusion | -0.001 [-0.002, +0.000] | +0.106 [+0.099, +0.113] | +0.383 [+0.365, +0.401] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.

## Which kind of respelling hurts

Change in nDCG@10 when a single rule is applied to every word it can change, measured only on the queries that rule changes.

| Rule | Example | Queries changed | bm25 | bm25-l2 | bm25-l3 | char | fusion |
|---|---|---|---|---|---|---|---|
| attested | word list | 985 | -0.470 | -0.158 | -0.037 | -0.183 | -0.245 |
| lexicon | word list | 25 | +0.000 | +0.000 | +0.000 | -0.015 | -0.001 |
| long_a | baat → bat | 504 | -0.083 | +0.000 | +0.000 | -0.022 | -0.028 |
| long_i | theek → thik | 558 | -0.041 | +0.000 | +0.000 | -0.029 | -0.011 |
| long_u | poora → pura | 146 | -0.009 | +0.000 | +0.000 | -0.026 | -0.005 |
| degeminate | achha → acha | 185 | -0.039 | +0.000 | +0.000 | -0.015 | -0.009 |
| ai_e | kaise → kese | 174 | -0.013 | +0.000 | +0.000 | -0.024 | -0.006 |
| au_o | aur → or | 77 | -0.026 | +0.000 | +0.000 | -0.029 | -0.001 |
| final_e_y | mujhe → mujhy | 304 | -0.012 | +0.000 | +0.000 | -0.008 | -0.001 |
| glide_y | kya → kia | 142 | -0.006 | +0.003 | +0.000 | -0.008 | -0.002 |
| final_h | jagah → jaga | 89 | -0.010 | +0.000 | +0.000 | -0.008 | -0.004 |
| ph_f | phir → fir | 24 | +0.000 | +0.000 | +0.000 | +0.015 | +0.015 |
| nasal_n | nahin → nahi | 180 | -0.026 | +0.000 | +0.000 | -0.007 | -0.004 |
| q_k | waqt → wakt | 242 | -0.007 | +0.000 | +0.000 | -0.024 | -0.003 |
| vowel_drop | karna → krna | 651 | -0.047 | -0.066 | -0.009 | -0.039 | -0.040 |
