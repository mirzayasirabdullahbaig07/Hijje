"""Phonetic normalisation of Roman Urdu words, at three strengths.

Roman Urdu has no standard spelling, so one word is written many ways
("kya", "kia", "kiya"). A normaliser maps the spellings of a word to one key
so that an exact-match retriever can still find it.

The catch is that every merge that joins two spellings of the same word can
also join two different words ("kaam" = work, "kam" = less). The levels below
go from few merges to many, so the trade-off can be measured instead of
guessed:

    0  none      lowercase only
    1  length    vowel length and doubled letters   kaam = kam, achha = acha
    2  phonetic  + sound classes and endings        kya = kia = kiya, mujhe = mujhy
    3  skeleton  + drop vowels (Soundex-like)       karna = krna, bohat = bht

The normaliser is rule-based and uses no word list. That is deliberate: the
variant generator in ``variation.py`` has a word list, and a normaliser built
from the same list would "solve" the synthetic test by construction.
"""

from __future__ import annotations

import re

from .text import tokenize

LEVELS = (0, 1, 2, 3)
LEVEL_NAMES = {0: "none", 1: "length", 2: "phonetic", 3: "skeleton"}

_CONS = "bcdfghjklmnpqrstvwxz"
_ASCII_WORD = re.compile(r"^[a-z]+$")
_RUN3 = re.compile(r"(.)\1{2,}")
_RUN2 = re.compile(r"(.)\1")
_ASPIRATE = re.compile(r"([bdjt])h")
_DIPH_E = re.compile(r"ai|ae|ei|ey(?![aeiou])|ay(?![aeiou])")
_DIPH_O = re.compile(r"au|ou")
_GLIDE_IY = re.compile(r"iy(?=[aeiou])")
_GLIDE_Y = re.compile(r"(?<=[%s])y(?=[aeiou])" % _CONS)
_FINAL_H = re.compile(r"(?<=[aeiou])h$")
_FINAL_NASAL = re.compile(r"[aeiou]n$")


def _level1(w: str) -> str:
    w = _RUN3.sub(r"\1\1", w)                   # yaaar -> yaar
    w = w.replace("ee", "i").replace("oo", "u")  # theek -> thik, poora -> pura
    return _RUN2.sub(r"\1", w)                   # kaam -> kam, achha -> acha


def _level2(w: str) -> str:
    w = w.replace("ph", "f").replace("q", "k").replace("w", "v")
    w = _ASPIRATE.sub(r"\1", w)        # bhi -> bi, mujhe -> muje, theek -> tik
    w = _DIPH_E.sub("e", w)            # kaise -> kese, hai -> he, kay -> ke
    w = _DIPH_O.sub("o", w)            # aur -> or, kaun -> kon
    w = _GLIDE_IY.sub("i", w)          # kiya -> kia, liye -> lie
    w = _GLIDE_Y.sub("i", w)           # kya -> kia, zyada -> ziada
    w = _FINAL_H.sub("", w)            # yeh -> ye, jagah -> jaga
    if len(w) >= 5 and _FINAL_NASAL.search(w):
        w = w[:-1]                     # nahin -> nahi, yahan -> yaha
    if len(w) >= 2 and w[-1] in "ey":
        w = w[:-1] + "i"               # mujhe / mujhy -> muji, ke / ky -> ki
    return _RUN2.sub(r"\1", w)


def _skeleton(w: str) -> str:
    """First sound plus the following consonants. 'ch' and 'sh' stay whole."""
    marked = w.replace("ch", "C").replace("sh", "S")
    key = marked[0] + re.sub(r"[aeiouyh]", "", marked[1:])
    key = _RUN2.sub(r"\1", key)
    if len(key) < 2:
        return w  # a one-sound key says almost nothing; keep the level-2 form
    return key.replace("C", "ch").replace("S", "sh")


def normalize_word(word: str, level: int) -> str:
    """Return the normalisation key of one word at the given level."""
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}, got {level!r}")
    w = word.lower()
    if level == 0 or not _ASCII_WORD.match(w):
        return w  # digits, mixed tokens and Urdu-script words pass through
    for _ in range(6):  # repeat until stable, so the function is idempotent
        new = _level1(w)
        if level >= 2:
            new = _level2(new)
        if new == w:
            break
        w = new
    if level == 3:
        w = _skeleton(w)
    return w


def analyze(text: str, level: int = 0) -> list[str]:
    """Tokenise a text and normalise every token."""
    return [normalize_word(tok, level) for tok in tokenize(text)]


def normalize_text(text: str, level: int) -> str:
    return " ".join(analyze(text, level))
