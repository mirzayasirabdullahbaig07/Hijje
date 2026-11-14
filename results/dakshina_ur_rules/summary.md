# Hijje evaluation: dakshina_ur

9759 documents, 1000 queries, 5 respelled variants per query per rate, seed 13, hijje 0.3.0.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.993 | 0.990–0.996 | 0.879 | 11.5% | 0.420 | 57.7% | 0.409 | 0.211 |
| bm25-l2 | 0.988 | 0.983–0.992 | 0.981 | 0.7% | 0.966 | 2.2% | 0.955 | 0.759 |
| bm25-l3 | 0.977 | 0.969–0.983 | 0.974 | 0.2% | 0.972 | 0.5% | 0.970 | 0.967 |
| char | 0.976 | 0.970–0.982 | 0.937 | 4.0% | 0.864 | 11.5% | 0.831 | 0.434 |
| fusion | 0.993 | 0.989–0.995 | 0.955 | 3.8% | 0.746 | 24.9% | 0.699 | 0.389 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.995 | 0.944 | 0.564 |
| bm25-l2 | 0.993 | 0.991 | 0.986 |
| bm25-l3 | 0.989 | 0.988 | 0.986 |
| char | 0.993 | 0.989 | 0.972 |
| fusion | 0.995 | 0.987 | 0.918 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l2 | -0.006 [-0.009, -0.003] | +0.102 [+0.093, +0.112] | +0.546 [+0.518, +0.572] |
| bm25-l3 | -0.017 [-0.023, -0.011] | +0.095 [+0.085, +0.105] | +0.552 [+0.526, +0.578] |
| char | -0.017 [-0.022, -0.012] | +0.058 [+0.048, +0.068] | +0.444 [+0.418, +0.469] |
| fusion | -0.001 [-0.002, +0.000] | +0.076 [+0.069, +0.083] | +0.326 [+0.307, +0.345] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.

## Which kind of respelling hurts

Change in nDCG@10 when a single rule is applied to every word it can change, measured only on the queries that rule changes.

| Rule | Example | Queries changed | bm25 | bm25-l2 | bm25-l3 | char | fusion |
|---|---|---|---|---|---|---|---|
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
