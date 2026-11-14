"""A respelling generator that uses spellings people really wrote.

``variation.VariationModel`` invents respellings from hand-written rules. The
check in ``attested.py`` showed that those rules reproduce only a part of what
people write. This model does not invent anything: a word is respelled only
with a spelling that a person wrote for the same Urdu word, and the more
people wrote it, the more likely it is to be chosen.

It needs a table ``native word -> {spelling: count}``, for example from the
Dakshina lexicon (see ``attested.load_attested``).

What the counts mean depends on the source file. In the Dakshina *lexicon*
they are how many annotators gave that spelling, not how often it appears in
running text. In the Dakshina *sentences* they are real usage counts. The model
does not care which; it only uses them as weights.

Limits, stated plainly:

- A word that is not in the table is left alone. ``coverage`` tells you how
  many words of a text can be changed.
- A spelling can belong to more than one Urdu word (``ka`` is ambiguous in a
  few cases). The model picks the Urdu word that has the most weight for that
  spelling, so a query is respelled one way only.
- Spellings come from careful, written text. Chat-style forms such as ``kr``
  or ``hy`` are only here if a person wrote them for that dataset.
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from typing import Iterable, Mapping, Optional

from .variation import Edit, Perturbed, VariationModel

ATTESTED_RULE = "attested"
_TOKEN_PARTS = re.compile(r"^(\W*)(.*?)(\W*)$", re.UNICODE | re.DOTALL)


class AttestedVariation:
    """Respells words with spellings that people wrote for the same word.

    table     {native word: {spelling: count}}
    protect   words that must never be changed
    fallback  an optional ``VariationModel``. Words that the table does not
              know are respelled by its rules instead. Use it to add chat-style
              forms; leave it out to stay strictly with human data.
    """

    def __init__(
        self,
        table: Mapping[str, Mapping[str, int]],
        protect: Iterable[str] = (),
        fallback: Optional[VariationModel] = None,
    ) -> None:
        self.protect = frozenset(p.lower() for p in protect)
        self.fallback = fallback
        # spelling -> native word with the most weight for it
        best: dict[str, tuple[int, str]] = {}
        for native in sorted(table):
            for spelling, count in table[native].items():
                spelling = spelling.lower()
                if spelling not in best or count > best[spelling][0]:
                    best[spelling] = (count, native)
        self._native_of = {s: native for s, (_, native) in best.items()}
        # native word -> [(spelling, count)], sorted so that results never
        # depend on dictionary order
        merged: dict[str, dict[str, int]] = defaultdict(dict)
        for native, spellings in table.items():
            for spelling, count in spellings.items():
                spelling = spelling.lower()
                merged[native][spelling] = merged[native].get(spelling, 0) + count
        self._spellings = {
            native: sorted(d.items()) for native, d in merged.items()
        }

    # -- introspection ----------------------------------------------------

    def rule_names(self) -> list[str]:
        names = [ATTESTED_RULE]
        if self.fallback is not None:
            names += self.fallback.rule_names()
        return names

    def candidates(
        self, word: str, only_rules: Optional[Iterable[str]] = None
    ) -> list[tuple[str, str, float]]:
        """Other spellings people wrote for this word, as (variant, rule, weight)."""
        allowed = None if only_rules is None else set(only_rules)
        out: list[tuple[str, str, float]] = []
        if allowed is None or ATTESTED_RULE in allowed:
            native = self._native_of.get(word)
            if native is not None:
                out = [
                    (s, ATTESTED_RULE, float(c))
                    for s, c in self._spellings[native]
                    if s != word and s.isalpha() and s.isascii()
                ]
        if not out and self.fallback is not None:
            rest = None if allowed is None else allowed - {ATTESTED_RULE}
            if rest is None or rest:
                out = self.fallback.candidates(word, rest)
        return out

    def knows(self, word: str) -> bool:
        """True if people wrote at least one other spelling of this word."""
        return bool(self.candidates(word.lower()))

    def coverage(self, text: str) -> float:
        """Share of the words in ``text`` that can be respelled."""
        words = [
            m[1].lower() for m in (_TOKEN_PARTS.match(t).groups() for t in text.split())
            if m[1]
        ]
        words = [w for w in words if self._eligible(w)]
        if not words:
            return 0.0
        return sum(1 for w in words if self.knows(w)) / len(words)

    # -- generation -------------------------------------------------------

    def _eligible(self, core: str) -> bool:
        return (
            len(core) >= 2
            and core.isascii()
            and core.isalpha()
            and core.lower() not in self.protect
        )

    @staticmethod
    def _pick(cands: list[tuple[str, str, float]], rng: random.Random) -> tuple[str, str]:
        # Only rng.random() is used, so a seed gives the same output on every
        # Python version (see VariationModel._pick).
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
        """Respell roughly ``rate`` of the changeable words in ``text``.

        ``max_edits`` is accepted so that this class can replace
        ``VariationModel``, but it has no effect on words answered from the
        table: a word gets one spelling that a person wrote, never a chain of
        invented edits.
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
            cands = self.candidates(original, only)
            if not cands:
                continue
            word, rule = self._pick(cands, rng)
            if rule != ATTESTED_RULE and max_edits > 1:
                # the fallback rules may stack, exactly as in VariationModel
                applied = [rule]
                for _ in range(max_edits - 1):
                    more = self.fallback.candidates(word, None if only is None else [r for r in only if r != ATTESTED_RULE])
                    if not more:
                        break
                    word, rule2 = VariationModel._pick(more, rng)
                    applied.append(rule2)
                rule = "+".join(applied)
            if word != original:
                tokens[i] = lead + word + trail
                edits.append(Edit(i, original, word, rule))
        return Perturbed(" ".join(tokens), tuple(edits))
