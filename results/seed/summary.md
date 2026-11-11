# Hijje evaluation: seed

48 documents, 48 queries, 5 respelled variants per query per rate, seed 13, hijje 0.1.0.

## Robustness (nDCG@10)

| Retriever | Clean | 95% CI | 50% respelled | Drop | 100% respelled | Drop | Worst variant | Stability |
|---|---|---|---|---|---|---|---|---|
| bm25 | 0.993 | 0.982–1.000 | 0.919 | 7.4% | 0.634 | 36.2% | 0.634 | 0.275 |
| bm25-l1 | 0.993 | 0.982–1.000 | 0.963 | 3.0% | 0.861 | 13.3% | 0.789 | 0.352 |
| bm25-l2 | 0.993 | 0.982–1.000 | 0.985 | 0.7% | 0.970 | 2.2% | 0.962 | 0.690 |
| bm25-l3 | 0.993 | 0.982–1.000 | 0.993 | 0.0% | 0.993 | 0.0% | 0.993 | 0.878 |
| char | 0.985 | 0.966–1.000 | 0.970 | 1.6% | 0.962 | 2.3% | 0.935 | 0.491 |
| fusion | 0.993 | 0.982–1.000 | 0.962 | 3.1% | 0.882 | 11.2% | 0.858 | 0.496 |

*Drop* is the relative loss against the same retriever's clean score. *Worst variant* is the mean over queries of the lowest score among that query's variants at 100% respelled. *Stability* is the mean overlap (Jaccard) between the clean top-10 and each variant's top-10.

## Recall@10

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25 | 0.979 | 0.952 | 0.708 |
| bm25-l1 | 0.979 | 0.977 | 0.908 |
| bm25-l2 | 0.979 | 0.981 | 0.983 |
| bm25-l3 | 0.979 | 0.979 | 0.979 |
| char | 0.979 | 0.979 | 0.979 |
| fusion | 0.979 | 0.973 | 0.919 |

## Difference from `bm25` (nDCG@10, paired bootstrap 95% CI)

| Retriever | Clean | 50% respelled | 100% respelled |
|---|---|---|---|
| bm25-l1 | +0.000 [+0.000, +0.000] | +0.043 [+0.013, +0.081] | +0.227 [+0.124, +0.340] |
| bm25-l2 | +0.000 [+0.000, +0.000] | +0.066 [+0.033, +0.104] | +0.337 [+0.214, +0.459] |
| bm25-l3 | +0.000 [+0.000, +0.000] | +0.073 [+0.040, +0.113] | +0.359 [+0.238, +0.489] |
| char | -0.008 [-0.023, +0.000] | +0.050 [+0.026, +0.076] | +0.328 [+0.212, +0.451] |
| fusion | +0.000 [+0.000, +0.000] | +0.043 [+0.021, +0.070] | +0.248 [+0.149, +0.360] |

An interval that does not contain 0 means the difference is unlikely to be query-sampling noise.

## Which kind of respelling hurts

Change in nDCG@10 when a single rule is applied to every word it can change, measured only on the queries that rule changes.

| Rule | Example | Queries changed | bm25 | bm25-l1 | bm25-l2 | bm25-l3 | char | fusion |
|---|---|---|---|---|---|---|---|---|
| lexicon | word list | 48 | +0.000 | +0.000 | +0.004 | +0.000 | +0.000 | +0.002 |
| long_a | baat → bat | 16 | -0.031 | +0.000 | +0.000 | +0.000 | -0.008 | -0.031 |
| long_i | theek → thik | 31 | -0.032 | +0.000 | +0.000 | +0.000 | -0.011 | -0.018 |
| long_u | poora → pura | 6 | -0.062 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| degeminate | achha → acha | 2 | -0.185 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| ai_e | kaise → kese | 30 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| au_o | aur → or | 5 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| final_e_y | mujhe → mujhy | 46 | -0.009 | -0.009 | +0.000 | +0.000 | -0.001 | -0.001 |
| glide_y | kya → kia | 26 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| final_h | jagah → jaga | 2 | -0.152 | -0.152 | +0.000 | +0.000 | +0.000 | +0.000 |
| aspirate_h | mujhe → muje | 7 | -0.105 | -0.105 | +0.000 | +0.000 | +0.000 | +0.000 |
| ph_f | phir → fir | 0 | – | – | – | – | – | – |
| nasal_n | nahin → nahi | 33 | -0.028 | -0.028 | +0.000 | +0.000 | +0.000 | +0.000 |
| w_v | wajah → vajah | 8 | -0.043 | -0.043 | +0.000 | +0.000 | -0.038 | -0.038 |
| q_k | waqt → wakt | 8 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 | +0.000 |
| vowel_drop | karna → krna | 39 | -0.043 | -0.043 | -0.043 | +0.000 | -0.001 | -0.026 |
