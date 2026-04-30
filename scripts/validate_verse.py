from __future__ import annotations

import re

from .fetch_verse import VerseFetch

REF_RE = re.compile(
    r"""^(?P<book>(?:\d\s)?[A-Za-z][A-Za-z\s]+?)\s+
        (?P<chapter>\d+)
        (?::(?P<vstart>\d+)(?:-(?P<vend>\d+))?)?$""",
    re.VERBOSE,
)


def _expected_verse_count(reference: str) -> int | None:
    m = REF_RE.match(reference.strip())
    if not m:
        return None
    vstart = m.group("vstart")
    vend = m.group("vend")
    if vstart is None:
        return None
    if vend is None:
        return 1
    return int(vend) - int(vstart) + 1


def validate_verse(fetch: VerseFetch, reference: str) -> None:
    text = fetch.text.strip()
    if len(text) < 20:
        raise ValueError(f"Verse text for {reference} is suspiciously short: {text!r}")
    if re.search(r"\b(I'm sorry|as an AI|I cannot)\b", text, re.IGNORECASE):
        raise ValueError(f"Verse text for {reference} looks like a model refusal.")

    if not fetch.verses:
        raise ValueError(f"Verse text for {reference} has no structured verse data.")

    expected = _expected_verse_count(reference)
    if expected is not None and len(fetch.verses) != expected:
        raise ValueError(
            f"Verse count mismatch for {reference}: "
            f"expected {expected}, got {len(fetch.verses)}."
        )

    numbers = [v["verse"] for v in fetch.verses if v.get("verse") is not None]
    if numbers and numbers != sorted(numbers):
        raise ValueError(f"Verse numbers for {reference} are out of order: {numbers}")

    avg_words = sum(len(v["text"].split()) for v in fetch.verses) / len(fetch.verses)
    if avg_words < 3:
        raise ValueError(
            f"Verses for {reference} look truncated (avg {avg_words:.1f} words/verse)."
        )
