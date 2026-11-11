"""Tokenisation shared by every lexical component.

One tokeniser is used everywhere so that a difference between two retrievers
can never be caused by a difference in how they split text.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Lowercase and split into runs of letters and digits."""
    return _TOKEN.findall(text.lower())
