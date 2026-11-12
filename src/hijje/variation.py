"""A controllable model of Roman Urdu spelling variation.

Given a query, this module rewrites some of its words the way people actually
respell them: dropping a long vowel ("baat" -> "bat"), losing an aspirate
("mujhe" -> "muje"), texting-style vowel dropping ("karna" -> "krna") and so on.

Why rules and not an LLM:
  * free and offline, so the benchmark can be rebuilt by anyone;
  * reproducible: the same seed always gives the same variants;
  * attributable: every edit records which rule made it, so we can measure
    which kind of variation hurts which retriever.

The rules come from patterns described in the Roman Urdu literature and from
common texting usage. They are a model, not ground truth. Every rule must be
checked by native speakers, and results on synthetic variants must be
confirmed on human-written ones (see docs/RESEARCH_PLAN.md).
"""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass
from typing import Callable, Iterable, Optional, Sequence

_C = "bcdfghjklmnpqrstvwxz"


def derive_seed(*parts: object) -> int:
    """Stable integer seed from any values.

    Python's built-in hash() changes between runs, so it cannot be used for
    reproducible experiments. SHA-256 gives the same number everywhere.
    """
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _each(pattern: str, repl: str, word: str) -> list[str]:
    """Apply a substitution at each match separately: one variant per site."""
    return [word[: m.start()] + m.expand(repl) + word[m.end():] for m in re.finditer(pattern, word)]


# --- productive rules --------------------------------------------------------

def _long_a(w: str) -> list[str]:
    return _each(r"aa", "a", w)


def _long_i(w: str) -> list[str]:
    out = _each(r"ee", "i", w)
    if len(w) >= 3 and re.search(r"[%s]i$" % _C, w):
        out.append(w[:-1] + "ee")
    return out


def _long_u(w: str) -> list[str]:
    return _each(r"oo", "u", w)


def _degeminate(w: str) -> list[str]:
    return _each(r"([%s])\1" % _C, r"\1", w)


def _ai_e(w: str) -> list[str]:
    # Only inside a word: a final "ai" is usually a + i ("parhai", "safai"),
    # which nobody writes as "e".
    out = _each(r"ai(?=.)", "e", w)
    if w.endswith("ai"):
        out.append(w[:-2] + "ay")
    return out


def _au_o(w: str) -> list[str]:
    return _each(r"au", "o", w)


def _final_e_y(w: str) -> list[str]:
    out = []
    if re.search(r"[%s]e$" % _C, w):
        out += [w[:-1] + "ay", w[:-1] + "y"]
    elif w.endswith("ye") and len(w) >= 3:
        out.append(w[:-1] + "ay")
    # A final "i" is NOT respelled as "y" ("pani" -> "pany"). Removed after
    # native review, round 1: in Pakistan a final -i is written "i", and "y"
    # at the end of a word stands for the -e sound.
    return out


def _glide_y(w: str) -> list[str]:
    out = _each(r"(?<=[%s])y(?=[aeiou])" % _C, "i", w)
    out += _each(r"(?<=[%s])y(?=[aeiou])" % _C, "iy", w)
    out += _each(r"iy(?=[aeiou])", "i", w)
    out += _each(r"(?<=[%s])iy(?=a)" % _C, "y", w)
    return out


def _final_h(w: str) -> list[str]:
    return [w[:-1]] if len(w) >= 3 and re.search(r"[aeiou]h$", w) else []


def _ph_f(w: str) -> list[str]:
    return _each(r"ph", "f", w)


_NASAL_ENDINGS = (
    ("ahin", ("ahi",)),
    ("ahan", ("aha",)),
    ("ein", ("en", "e")),
    ("ain", ("ai", "ein")),
    ("oon", ("un",)),
    ("yun", ("yu",)),
)


def _nasal_n(w: str) -> list[str]:
    out = []
    for suffix, replacements in _NASAL_ENDINGS:
        if w.endswith(suffix) and len(w) > len(suffix):
            out += [w[: -len(suffix)] + r for r in replacements]
    if len(w) >= 5 and re.search(r"[%s]on$" % _C, w):
        out.append(w[:-1])
    if len(w) >= 5 and re.search(r"[%s]un$" % _C, w):
        out.append(w[:-2] + "oon")
    return out


def _q_k(w: str) -> list[str]:
    return _each(r"q", "k", w)


# Words whose first vowel is long, so dropping it gives a form that reads as a
# typo ("pani" -> "pni"). The spelling does not show vowel length, so the rule
# cannot work this out; the list holds the words a native reviewer rejected.
VOWEL_DROP_EXCEPTIONS = frozenset({"pani"})


def _vowel_drop(w: str) -> list[str]:
    if not 3 <= len(w) <= 5 or w in VOWEL_DROP_EXCEPTIONS:
        return []
    m = re.search(r"(?<=[%s])[aiu](?=[%s])" % (_C, _C), w)
    return [w[: m.start()] + w[m.end():]] if m else []


@dataclass(frozen=True)
class Rule:
    name: str
    description: str
    example: tuple[str, str]
    apply: Callable[[str], list[str]]
    weight: float = 1.0


RULES: tuple[Rule, ...] = (
    Rule("long_a", "long 'aa' written as single 'a'", ("baat", "bat"), _long_a),
    Rule("long_i", "'ee' written as 'i'; final 'i' written as 'ee'", ("theek", "thik"), _long_i),
    Rule("long_u", "'oo' written as 'u'", ("poora", "pura"), _long_u),
    Rule("degeminate", "doubled consonant written once", ("achha", "acha"), _degeminate),
    Rule("ai_e", "'ai' inside a word written as 'e'; final 'ai' as 'ay'", ("kaise", "kese"), _ai_e),
    Rule("au_o", "'au' written as 'o'", ("aur", "or"), _au_o),
    Rule("final_e_y", "final 'e' written as 'ay' or 'y'", ("mujhe", "mujhy"), _final_e_y),
    Rule("glide_y", "'y' glide written as 'i' or 'iy' and back", ("kya", "kia"), _glide_y),
    Rule("final_h", "silent final 'h' dropped", ("jagah", "jaga"), _final_h),
    Rule("ph_f", "'ph' written as 'f'", ("phir", "fir"), _ph_f),
    Rule("nasal_n", "nasal ending respelled or dropped", ("nahin", "nahi"), _nasal_n),
    Rule("q_k", "'q' written as 'k'", ("waqt", "wakt"), _q_k),
    Rule("vowel_drop", "texting style: short vowel dropped", ("karna", "krna"), _vowel_drop, 0.5),
)

# --- attested alternates for very frequent words ------------------------------
# These are spellings commonly seen in Pakistani chat text. They were written
# from general familiarity, not counted from a corpus. A native speaker has
# reviewed a small part (round 1, see docs/VARIATION_RULES.md); the rest still
# needs review, and a corpus-derived list should replace it for the paper.

LEXICON: dict[str, tuple[str, ...]] = {
    "hai": ("hy", "he", "hay", "h"),
    "hain": ("hai", "hein", "hen", "hn"),
    "nahi": ("nahin", "nai", "nhi", "ni", "nahee"),
    "kya": ("kia", "kiya"),
    "aur": ("or", "r", "aor"),
    "ke": ("kay", "k", "ky"),
    "se": ("say", "sy"),
    "mein": ("main", "me", "mai", "mn", "men"),
    "main": ("mein", "me", "mai", "mn"),
    "bohat": ("bohot", "bahut", "boht", "bht", "buhat"),
    "kyun": ("kyu", "kiun", "kyon", "q"),
    "theek": ("thik", "thek", "thk", "theak"),
    "acha": ("achha", "accha"),
    "achi": ("achhi", "acchi"),
    "kuch": ("kuchh", "kch"),
    "yeh": ("ye", "yay", "yh"),
    "ye": ("yeh", "yay", "yh"),
    "woh": ("wo", "wh"),
    "wo": ("woh", "wh"),
    "hum": ("ham", "hm"),
    "tum": ("tm",),
    "aap": ("ap",),
    "mujhe": ("mujhay", "mujhy", "muje", "mjhe", "mjy"),
    "kaise": ("kese", "kaisay", "kesay", "kaisy"),
    "liye": ("liay", "lie", "lye", "liyay"),
    "kar": ("kr",),
    "karna": ("krna",),
    "karne": ("krne", "karnay", "krnay"),
    "raha": ("rha",),
    "rahi": ("rhi",),
    "rahe": ("rhe", "rahay"),
    "chahiye": ("chahiay", "chahye", "chaiye", "chahie"),
    "zyada": ("ziada", "ziyada", "zyda", "zada"),
    "pehle": ("pehlay", "phle", "pahle", "pehly"),
    "baad": ("bad",),
    "saath": ("sath",),
    "waqt": ("wakt", "wqt", "waqat"),
    "zaroor": ("zarur", "zrur"),
    "zaroori": ("zaruri", "zruri"),
    "tarah": ("tara", "trah"),
    "sab": ("sb",),
    "phir": ("fir", "phr"),
    "lekin": ("lakin", "lkn"),
    "agar": ("agr",),
    "abhi": ("abi", "abhe"),
    "bhi": ("bi", "b"),
    "koi": ("koe", "koy"),
    "kab": ("kb",),
    "jab": ("jb",),
    "yahan": ("yaha", "yhan"),
    "wahan": ("waha", "whan"),
    "kahan": ("kaha", "khan"),
    "kitna": ("ktna",),
    "kitni": ("ktni",),
    "kitne": ("kitnay", "ktne"),
    "paisa": ("pesa",),
    "paise": ("pese", "paisay", "pesay"),
    "tareeqa": ("tariqa", "tarika", "tareeka"),
    "karun": ("karoon", "kru", "karu", "krun"),
    "karein": ("karen", "kren", "kare", "krein"),
}

LEXICON_RULE = "lexicon"
LEXICON_WEIGHT = 3.0


@dataclass(frozen=True)
class Edit:
    position: int   # index of the whitespace-separated token
    original: str
    variant: str
    rule: str       # rule name, or several joined by "+" when max_edits > 1


@dataclass(frozen=True)
class Perturbed:
    text: str
    edits: tuple[Edit, ...]


_TOKEN_PARTS = re.compile(r"^(\W*)(.*?)(\W*)$", re.UNICODE | re.DOTALL)


class VariationModel:
    """Generates respelled versions of Roman Urdu text.

    protect: words that must never be changed. Use it for English loanwords
    ("mobile", "password"), which do not follow Urdu spelling habits.
    """

    def __init__(
        self,
        rules: Sequence[Rule] = RULES,
        lexicon: Optional[dict[str, tuple[str, ...]]] = None,
        protect: Iterable[str] = (),
    ) -> None:
        self.rules = tuple(rules)
        self.lexicon = dict(LEXICON if lexicon is None else lexicon)
        self.protect = frozenset(p.lower() for p in protect)

    def rule_names(self) -> list[str]:
        names = [LEXICON_RULE] if self.lexicon else []
        return names + [r.name for r in self.rules]

    def candidates(
        self, word: str, only_rules: Optional[Iterable[str]] = None
    ) -> list[tuple[str, str, float]]:
        """All single-edit respellings of a word as (variant, rule, weight)."""
        allowed = None if only_rules is None else set(only_rules)
        out: list[tuple[str, str, float]] = []
        seen = {word}

        def add(variant: str, rule: str, weight: float) -> None:
            if variant and variant.isalpha() and variant not in seen:
                seen.add(variant)
                out.append((variant, rule, weight))

        if allowed is None or LEXICON_RULE in allowed:
            for variant in self.lexicon.get(word, ()):
                add(variant, LEXICON_RULE, LEXICON_WEIGHT)
        for rule in self.rules:
            if allowed is None or rule.name in allowed:
                for variant in rule.apply(word):
                    add(variant, rule.name, rule.weight)
        return out

    def _eligible(self, core: str) -> bool:
        return (
            len(core) >= 2
            and core.isascii()
            and core.isalpha()
            and core.lower() not in self.protect
        )

    @staticmethod
    def _pick(cands: list[tuple[str, str, float]], rng: random.Random) -> tuple[str, str]:
        # Only rng.random() is used: unlike choice() and shuffle(), its output
        # for a given seed is guaranteed stable across Python versions.
        total = sum(w for _, _, w in cands)
        threshold = rng.random() * total
        running = 0.0
        for variant, rule, weight in cands:
            running += weight
            if threshold < running:
                return variant, rule
        return cands[-1][0], cands[-1][1]

    def perturb(
        self,
        text: str,
        rate: float = 0.5,
        seed: int = 0,
        max_edits: int = 1,
        only_rules: Optional[Iterable[str]] = None,
        ensure_change: bool = True,
    ) -> Perturbed:
        """Respell roughly `rate` of the eligible words in `text`.

        rate          probability that each eligible word is respelled
        max_edits     how many single edits may be stacked on one word
        only_rules    restrict to these rules (for per-rule analysis)
        ensure_change respell at least one word when any word can be respelled
        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError("rate must be between 0 and 1")
        only = None if only_rules is None else tuple(only_rules)
        rng = random.Random(seed)
        tokens = text.split()
        parts = [_TOKEN_PARTS.match(tok).groups() for tok in tokens]
        eligible = [
            i for i, (_, core, _) in enumerate(parts)
            if self._eligible(core) and self.candidates(core.lower(), only)
        ]
        chosen = [i for i in eligible if rng.random() < rate]
        if not chosen and eligible and ensure_change and rate > 0:
            chosen = [eligible[int(rng.random() * len(eligible))]]

        edits = []
        for i in chosen:
            lead, core, trail = parts[i]
            original = core.lower()
            word, applied = original, []
            for _ in range(max_edits):
                cands = self.candidates(word, only)
                if not cands:
                    break
                word, rule = self._pick(cands, rng)
                applied.append(rule)
            if word != original:
                tokens[i] = lead + word + trail
                edits.append(Edit(i, original, word, "+".join(applied)))
        return Perturbed(" ".join(tokens), tuple(edits))
