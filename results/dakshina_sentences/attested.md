# Rules checked against human-written spellings

Files: ur.romanized.rejoined.aligned.cased_nopunct.tsv

- pairs read: 158780
- skipped: more than one word on the line: 4369
- skipped: source word is not in native script: 1556
- skipped: spelling has digits or symbols: 1802

15993 native-script words, 24050 distinct spellings (1.50 per word); 5058 words were spelled in more than one way.

## How people's spellings of one word differ

Each pattern is counted once per word. `a ~ aa` means one spelling has `a` where another has `aa`; `(nothing)` means the letter is simply absent in one spelling.

| Pattern | Words | Example |
| --- | --- | --- |
| `a ~ aa` | 1764 | aayen / ayen |
| `a ~ (nothing)` | 567 | abad / bad |
| `e ~ (nothing) [word end]` | 427 | aain / aaine |
| `a ~ i` | 365 | ibtadayi / ibtidayi |
| `i ~ ee` | 357 | aayeen / aayin |
| `i ~ (nothing)` | 356 | aayein / aayen |
| `a ~ e` | 328 | main / mein |
| `a ~ u` | 315 | argentin / urgentin |
| `e ~ i` | 294 | aaeni / aaini |
| `y ~ (nothing)` | 269 | aainda / aayinda |
| `e ~ ay [word end]` | 205 | atay / ate |
| `u ~ oo` | 191 | aasoodae / aasudae |
| `h ~ (nothing) [word end]` | 177 | aayinda / aayindah |
| `o ~ u` | 156 | omra / umra |
| `e ~ ai` | 144 | aihkaam / ehkaam |
| `e ~ (nothing)` | 125 | aayein / aayin |
| `u ~ (nothing)` | 122 | ar / aur |
| `n ~ (nothing) [word end]` | 111 | statio / station |
| `h ~ (nothing)` | 104 | aasoodae / aasoodahe |
| `a ~ e [word end]` | 94 | aaya / aaye |
| `o ~ oo` | 92 | bojh / boojh |
| `v ~ w` | 90 | aathveen / aathween |
| `a ~ o` | 82 | an / on |
| `e ~ ee` | 80 | aayeen / aayen |
| `o ~ au` | 80 | auzaar / ozaar |
| `i ~ ee [word end]` | 76 | ibtedayee / ibtedayi |
| `a ~ aa [word end]` | 71 | ibteda / ibtedaa |
| `ay ~ (nothing)` | 66 | aayindah / aindah |
| `r ~ (nothing)` | 62 | jazeeah / jazeerah |
| `d ~ r` | 61 | adtees / artees |
| `n ~ (nothing)` | 61 | argentina / argetina |
| `i ~ u` | 59 | idhar / udhar |
| `y ~ (nothing) [word end]` | 59 | israel / israely |
| `i ~ (nothing) [word end]` | 55 | aakhir / aakhiri |
| `i ~ y` | 53 | adaigi / adaygi |
| `a ~ (nothing) [word end]` | 50 | argentin / argentina |
| `o ~ (nothing)` | 47 | ount / unt |
| `h ~ hh` | 44 | achcha / achchha |
| `e ~ i [word end]` | 41 | aaryaee / aaryaei |
| `a ~ y` | 38 | ibtedaai / ibtedayi |

1697 rarer patterns are in the JSON file.

## Do the rules generate what people write?

For every word with several human spellings, each rule was applied to each spelling. *Also written by a person* counts the generated respellings that a person wrote for the same word. The share is a lower bound: few people spelled each word, so a missing spelling is not proof that it is wrong. Compare the rules with each other.

| Rule | Rule's own example | Generated | Also written by a person | Share | Generated but not seen |
| --- | --- | --- | --- | --- | --- |
| `lexicon` | word list | 261 | 53 | 20.3% | main → mai |
| `long_a` | baat → bat | 3077 | 1775 | 57.7% | aainda → ainda |
| `long_i` | theek → thik | 2386 | 438 | 18.4% | iswi → iswee |
| `long_u` | poora → pura | 512 | 196 | 38.3% | aabaroo → aabaru |
| `degeminate` | achha → acha | 789 | 236 | 29.9% | assaar → asaar |
| `ai_e` | kaise → kese | 688 | 134 | 19.5% | main → men |
| `au_o` | aur → or | 245 | 72 | 29.4% | austen → osten |
| `final_e_y` | mujhe → mujhy | 2623 | 179 | 6.8% | eye → eyay |
| `glide_y` | kya → kia | 1425 | 190 | 13.3% | aadmiyon → aadmion |
| `final_h` | jagah → jaga | 388 | 145 | 37.4% | aindah → ainda |
| `ph_f` | phir → fir | 47 | 4 | 8.5% | alphanson → alfanson |
| `nasal_n` | nahin → nahi | 815 | 123 | 15.1% | main → mai |
| `q_k` | waqt → wakt | 1003 | 11 | 1.1% | aafaaqi → aafaaki |
| `vowel_drop` | karna → krna | 2444 | 60 | 2.5% | iris → irs |

Of 12990 pairs of human spellings of the same word, 3473 (26.7%) differ by exactly one rule edit. The rest differ in ways the rules do not model, or by more than one edit.

## What people wrote for particular words

- **pani** = پانی: paani (36), pani (28)
- **theek** = ٹھیک: theek (7), thik (2)
- **tareeqa** = طریقہ: tareeqa (13), tariqa (10)
- **sawal** = سوال: sawaal (6), sawal (5)
- **chawal** = چاول: chawal (2)
- **roti** = روٹی: roti (3)
- **saath** = ساتھ: saath (245), sath (82)
- **saath** = سات: saat (53), saath (1)
- **saath** = ساٹھ: saath (8)
- **kitni** = کتنی: kitni (9)
- **hai** = ہے: hai (2986), he (985), hain (6), ha (2), hen (2), ai (1), haib (1), oy (1), ye (1)
- **hai** = ہیں: hain (1335), hen (451), hai (2), he (1), hian (1), hin (1), the (1)
- **hai** = ی: y (2), hai (1), kee (1), ye (1)
- **nahi** = نہیں: nahin (281), nahi (213)
- **nahi** = نہی: nahi (2)
- **mujhe** = مجھے: mujhe (22)
