# Related work and reading list

Status on 11 November 2026. This is the start of a literature review, not a
finished one. Before claiming a research gap you need to read these papers
themselves and search further.

"Checked" means the paper's page, abstract or repository was opened that day.
It does not mean the full paper was read.

## Closest work (checked)

| Work | What it does | What it leaves open for this project |
|---|---|---|
| [Lost in Transliteration: Bridging the Script Gap in Neural IR](https://arxiv.org/abs/2505.08411) (SIGIR 2025) | Shows neural retrievers are not robust to transliterated queries; proposes training on transliterated queries. Chinese and Russian, mMARCO and neuCLIR, romanisation produced by a tool. | No Urdu. One fixed romanisation per word, so the non-standard spelling problem is not studied. Read via a third-party summary; read the paper itself. |
| [urdu-english-retrieval-benchmark](https://github.com/SMHC-hub/urdu-english-retrieval-benchmark) (GitHub, no paper) | Measures dense-retrieval loss for Urdu-English code-switched queries, including a Roman Urdu condition, on English corpora (SciFact, NFCorpus). Queries written by an LLM; 50 spot-checked. | Queries are not human-written; documents are English; spelling variation is not analysed or handled. 3 commits at the time of checking. |
| [Low-Resource Transliteration for Roman-Urdu and Urdu Using Transformer-Based Models](https://aclanthology.org/2025.loresmt-1.13.pdf) (LoResMT 2025) | Urdu ↔ Roman Urdu transliteration; notes that Roman Urdu has no standard spelling; uses Roman-Urdu-Parl and Dakshina. | Evaluates transliteration quality, not retrieval. Useful as a component for the "transliterate then retrieve" baseline and as a data source. |
| [DR-RAG: Addressing Retrieval Misalignment in Low-Resource Urdu Question Answering](https://aclanthology.org/2026.chipsal-1.6/) (CHiPSAL 2026) | RAG for Urdu with a dual index of chunks and generated question-answer pairs. | Urdu script; Roman Urdu is not mentioned in the abstract. |

## Related, found by title only (to read)

- [An Unsupervised Method for Discovering Lexical Variations in Roman Urdu Informal Text](https://aclanthology.org/D15-1097/) (EMNLP 2015). As recalled, not re-read: earlier work on grouping Roman Urdu spelling variants using a phonetic encoding called UrduPhone. If that is right, the level-3 key in this project is in the same family and must be compared against it directly.
- [CharacterBERT and Self-Teaching for Improving the Robustness of Dense Retrievers on Queries with Typos](https://arxiv.org/pdf/2204.00716v2.pdf). Typo robustness for English dense retrieval. The methods are candidates for RQ4.
- [A dataset of Roman Urdu text with spelling variations for sentence level sentiment analysis](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11683287/). Possible source of attested spelling variants.
- [ROMEVA: Geometry-Preserving Vocabulary Expansion for Roman Urdu Language Models](https://arxiv.org/abs/2606.22478).
- [Roman Urdu as a Low-Resource Language](https://acl-bg.org/proceedings/2025/LowResNLP%202025/pdf/2025.lowresnlp-1.9.pdf) (LowResNLP 2025).
- [How You Ask Matters! Adaptive RAG Robustness to Query Variations](https://arxiv.org/pdf/2604.10745).
- [Elevating Code-mixed Text Handling through Auditory Information of Words](https://arxiv.org/pdf/2310.18155). Phonetic information for code-mixed text.
- [UQA-RAG: Enhancing Urdu Question-Answer Retrieval With Semantic Similarity and LLMs](https://ieeexplore.ieee.org/abstract/document/11322726/).
- [roman-urdu-rag-bias-audit](https://github.com/malahilghauri-design/roman-urdu-rag-bias-audit). Repository was empty when checked, but its description (retrieval consistency for Roman Urdu RAG) shows someone else is looking at this area. Watch it.

## Background to cite (from memory, verify every detail before citing)

- BM25: Robertson and Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond".
- Reciprocal Rank Fusion: Cormack, Clarke and Büttcher, SIGIR 2009.
- BEIR benchmark and file format: Thakur et al., 2021.
- Dense models to evaluate: multilingual E5, BGE-M3, LaBSE.
- Typos in neural ranking: Zhuang and Zuccon (2021); Sidiropoulos and Kanoulas (2022).
- Mixed-script and transliterated search for Indian languages: the FIRE shared tasks on mixed-script information retrieval. Romanised Hindi is the nearest neighbour of Roman Urdu; search this literature carefully, a close precedent may exist there.
- Romanisation resources: Dakshina dataset; Roman-Urdu-Parl; the uroman tool.

## Searches still to run

- Romanised Hindi / Hinglish query spelling variation and retrieval.
- Roman Urdu search-engine query logs, query normalisation, spelling correction.
- Soundex-style keys in retrieval for other languages without standard spelling (Arabizi, Greeklish, romanised Bengali).
- Any Roman Urdu passage-ranking or question-answering dataset with a licence.

## For the backup project (old-vs-new document RAG)

That area is active, which is why it was not chosen first:
[Re3 / Re2Bench](https://aclanthology.org/2026.acl-long.1180.pdf) (ACL 2026),
[FRESCO](https://arxiv.org/abs/2604.14227),
[CONFLICTS](https://arxiv.org/pdf/2506.08500),
[VERITAS](https://www.preprints.org/manuscript/202610.0085).
