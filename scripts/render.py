from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .config import CONTENT_DIR


def _frontmatter(meta: dict[str, Any]) -> str:
    return "---\n" + yaml.safe_dump(meta, sort_keys=False).strip() + "\n---\n"


def slot_for_hour(hour: int) -> str:
    return "morning" if hour < 12 else "evening"


def output_paths(today: date, slot: str) -> tuple[Path, Path]:
    folder = CONTENT_DIR / f"{today:%Y}" / f"{today:%m}"
    base = f"{today:%d}-{slot}"
    return folder / f"{base}.md", folder / f"{base}.png"


def render_markdown(
    today: date,
    slot: str,
    reference: str,
    translation: str,
    verse_text: str,
    commentary: dict[str, Any],
    models: dict[str, str],
    image_filename: str | None,
) -> str:
    meta = {
        "date": today.isoformat(),
        "slot": slot,
        "reference": reference,
        "translation": translation,
        "title": commentary["title"],
        "ai": models,
    }
    if image_filename:
        meta["image"] = image_filename

    body = []
    if image_filename:
        body.append(f"![Devotional image]({image_filename})\n")
    body.append("## The Passage")
    body.append(f"> {verse_text}\n")
    body.append("## What's Happening Here")
    body.append(commentary["context"] + "\n")
    body.append("## What This Means for Today")
    body.append(commentary["application"] + "\n")
    body.append("## Three Things to Carry With You")
    for i, item in enumerate(commentary["takeaways"], start=1):
        body.append(f"{i}. {item}")
    body.append("\n## A Prayer")
    body.append(commentary["prayer"] + "\n")

    return _frontmatter(meta) + "\n" + "\n".join(body) + "\n"
