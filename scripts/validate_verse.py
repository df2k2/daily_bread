from __future__ import annotations

import re


def validate_verse(text: str, reference: str) -> None:
    cleaned = text.strip()
    if len(cleaned) < 20:
        raise ValueError(f"Verse text for {reference} is suspiciously short: {cleaned!r}")
    if re.search(r"\b(I'm sorry|as an AI|I cannot)\b", cleaned, re.IGNORECASE):
        raise ValueError(f"Verse text for {reference} looks like a model refusal.")
