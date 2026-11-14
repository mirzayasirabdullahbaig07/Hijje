# Rules checked against human-written spellings

Files: ur.translit.sampled.dev.tsv, ur.translit.sampled.test.tsv, ur.translit.sampled.train.tsv

- pairs read: 127201

30000 native-script words, 127201 distinct spellings (4.24 per word); 29302 words were spelled in more than one way.

## How people's spellings of one word differ

Each pattern is counted once per word. `a ~ aa` means one spelling has `a` where another has `aa`; `(nothing)` means the letter is simply absent in one spelling.

| Pattern | Words | Example |
| --- | --- | --- |
| `a ~ aa` | 9323 | aawo / awo |
| `a ~ (nothing)` | 8422 | aidea / idea |
| `a ~ e` | 6155 | ainstein / einstein |
| `a ~ i` | 5503 | aares / aires |
| `e ~ i` | 5387 | aer / air |
| `a ~ u` | 4842 | aazar / aazur |
| `i ~ ee` | 3778 | aaeendaa / aaindaa |
| `i ~ (nothing)` | 3680 | aaizak / aazak |
| `o ~ u` | 3361 | aaon / aaun |
| `i ~ ee [word end]` | 3086 | aaee / aai |
| `y ~ (nothing)` | 2978 | aai / aayi |
| `h ~ (nothing) [word end]` | 2774 | aainda / aaindah |
| `h ~ (nothing)` | 2686 | aabadhi / aabadi |
| `e ~ (nothing)` | 2634 | aaen / aan |
| `a ~ aa [word end]` | 2279 | aaifa / aaifaa |
| `i ~ y [word end]` | 2264 | aayini / aayiny |
| `e ~ ee` | 2100 | aayeen / aayen |
| `u ~ oo` | 2054 | aabzaroor / aabzarur |
| `u ~ (nothing)` | 2011 | aablah / aabulah |
| `v ~ w` | 1981 | aariyavon / aariyawon |
| `o ~ oo` | 1791 | aabalon / aabaloon |
| `e ~ ay [word end]` | 1610 | aablay / aable |
| `a ~ o` | 1507 | aut / out |
| `e ~ (nothing) [word end]` | 1453 | aabayi / aabayie |
| `k ~ q` | 1409 | aakhir / aaqhir |
| `i ~ y` | 1388 | airesh / ayresh |
| `e ~ i [word end]` | 1372 | aaye / aayi |
| `y ~ (nothing) [word end]` | 1342 | aable / aabley |
| `e ~ ai` | 1277 | aaindah / aendah |
| `y ~ ee [word end]` | 1221 | aayinee / aayiny |
| `i ~ u` | 974 | aamin / aamun |
| `j ~ z` | 915 | aijak / aizak |
| `q ~ kh` | 899 | akhbaar / aqbaar |
| `e ~ ee [word end]` | 847 | ayenge / ayengee |
| `n ~ (nothing) [word end]` | 764 | aao / aaon |
| `e ~ y [word end]` | 743 | aarte / aarty |
| `r ~ (nothing)` | 725 | spourts / spouts |
| `e ~ y` | 724 | aendah / ayndah |
| `e ~ u` | 722 | aaren / aarun |
| `c ~ k` | 719 | aarthodocs / aarthodoks |

16436 rarer patterns are in the JSON file.

## Do the rules generate what people write?

For every word with several human spellings, each rule was applied to each spelling. *Also written by a person* counts the generated respellings that a person wrote for the same word. The share is a lower bound: few people spelled each word, so a missing spelling is not proof that it is wrong. Compare the rules with each other.

| Rule | Rule's own example | Generated | Also written by a person | Share | Generated but not seen |
| --- | --- | --- | --- | --- | --- |
| `lexicon` | word list | 529 | 131 | 24.8% | aur → aor |
| `long_a` | baat → bat | 22216 | 13132 | 59.1% | aao → ao |
| `long_i` | theek → thik | 23794 | 10371 | 43.6% | aaieen → aaiin |
| `long_u` | poora → pura | 4773 | 2455 | 51.4% | aaoo → aau |
| `degeminate` | achha → acha | 5680 | 2301 | 40.5% | artillery → artilery |
| `ai_e` | kaise → kese | 5305 | 1189 | 22.4% | aai → aay |
| `au_o` | aur → or | 2030 | 533 | 26.3% | aau → ao |
| `final_e_y` | mujhe → mujhy | 13773 | 1948 | 14.1% | aaye → aayay |
| `glide_y` | kya → kia | 11032 | 2036 | 18.5% | aaiyene → aaiene |
| `final_h` | jagah → jaga | 6903 | 1889 | 27.4% | aaendah → aaenda |
| `ph_f` | phir → fir | 1299 | 650 | 50.0% | aaphoncha → aafoncha |
| `nasal_n` | nahin → nahi | 8438 | 1181 | 14.0% | ayron → ayro |
| `q_k` | waqt → wakt | 7799 | 1620 | 20.8% | aaqbaar → aakbaar |
| `vowel_drop` | karna → krna | 21969 | 913 | 4.2% | aawat → aawt |

Of 252429 pairs of human spellings of the same word, 36500 (14.5%) differ by exactly one rule edit. The rest differ in ways the rules do not model, or by more than one edit.

## What people wrote for particular words

- **pani** = پانی: pani (5), paani (3), paanee (1), pany (1)
- **theek** = ٹھک: theek (1), thek (1), thiik (1), thik (1), thiyk (1), thuk (1)
- **theek** = ٹھیک: thek (2), theek (1), theekh (1), thik (1)
- **tareeqa** = طريقہ: tariqa (3), tarikah (2), tariqah (2), tareekeh (1), tareeqa (1), tareeqah (1), tareqqaa (1), tarika (1), tarikeh (1), tariqh (1)
- **tareeqa** = طریقہ: tariqah (2), tareeqa (1), tareeqah (1), tarika (1), tarikah (1), treeqaa (1)
- **tareeqa** = طریقہء: tareeqa (1), tareeqahaa (1), tareeqay (1), tarika (1), tariqa (1), tariqah (1), tariqahaa (1)
- **sawal** = سوال: sawal (5), saval (3), sual (1)
- **sawal** = سؤال: sawal (2), saval (1), sawaal (1), sawael (1)
- **sawal** = ساول: saaval (1), saawal (1), savil (1), sawal (1), sawil (1)
- **chawal** = چاول: chawal (3), chaawal (2)
- **roti** = روٹی: roti (2), roothi (1), rotee (1), ruuthi (1)
- **saath** = ساتھ: sath (6), saath (3)
- **saath** = ساٹھ: saath (3), sath (3)
- **kitni** = کتنی: kitni (2), katni (1), kitnee (1), kitny (1)
- **hai** = ہے: hai (5), hay (3), he (2), hi (2), hey (1)
- **hai** = ہائی: high (5), hai (1), hay (1), haye (1), hayi (1), hey (1), hiyee (1)
- **hai** = حی: hi (3), he (2), hai (1), hay (1), hee (1)
- **hai** = ہای: hai (3), hae (2), haee (1), hi (1), high (1)
- **hai** = ح: ha (2), hai (2), hay (1), huh (1)
- **nahi** = نہیں: nahin (5), naheen (2), nahean (1), nahein (1), nahi (1)
- **nahi** = نہی: nahi (5), nahee (2), nehi (1)
- **mujhe** = مجھے: mujhe (4), mujhay (3), majhe (1), mojhe (1)
- **mujhe** = مجہے: mujhe (2), majhe (1), mujhay (1), mujhey (1)
- **mujhe** = مُجھے: mujhay (3), mujhe (1)
