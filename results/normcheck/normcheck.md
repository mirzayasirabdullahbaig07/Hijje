# Normalisers checked on human spellings

Words per split: train 25000, dev 2500, test 2500.

*Unified pairs*: share of the different spellings of one Urdu word that get one key (higher is better).
*Extra shared keys*: share of words whose key another word also has, beyond level 0 (lower is better; an upper bound on false merges).

| Level | train: unified | dev: unified | test: unified | train: extra shared | dev: extra shared | test: extra shared |
|---|---|---|---|---|---|---|
| 0 none | 0.0% | 0.0% | 0.0% | +0.0 pts | +0.0 pts | +0.0 pts |
| 1 length | 12.8% | 12.2% | 13.1% | +2.3 pts | +2.2 pts | +2.8 pts |
| 2 phonetic | 29.8% | 29.4% | 31.2% | +12.8 pts | +12.6 pts | +13.9 pts |
| 3 skeleton | 78.5% | 79.4% | 79.1% | +42.4 pts | +42.6 pts | +43.8 pts |
| 4 vowelclass | 59.8% | 59.6% | 60.3% | +24.2 pts | +24.3 pts | +25.4 pts |
