from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .config import CONTENT_DIR

ATTRIBUTIONS: dict[str, str] = {
    "NLT": (
        "Scripture quotations are taken from the Holy Bible, New Living "
        "Translation, copyright © 1996, 2004, 2015 by Tyndale House Foundation. "
        "Used by permission of Tyndale House Publishers."
    ),
    "PT-NVI": (
        "Citações bíblicas extraídas da Nova Versão Internacional (NVI), "
        "© 1993, 2000 por Biblica, Inc. Usado com permissão."
    ),
    "PT-ACF": (
        "Citações bíblicas extraídas da Almeida Corrigida Fiel (ACF), "
        "© Sociedade Bíblica Trinitariana do Brasil."
    ),
    "PT-AA": (
        "Citações bíblicas extraídas da Almeida Revista e Atualizada / "
        "Imprensa Bíblica (Almeida Atualizada)."
    ),
}


def _frontmatter(meta: dict[str, Any]) -> str:
    return "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip() + "\n---\n"


def slot_for_hour(hour: int) -> str:
    return "morning" if hour < 12 else "evening"


def output_paths(today: date, slot: str) -> tuple[Path, Path]:
    folder = CONTENT_DIR / f"{today:%Y}" / f"{today:%m}"
    base = f"{today:%d}-{slot}"
    return folder / f"{base}.md", folder / f"{base}.png"


def _format_date(d: date) -> str:
    return d.strftime("%B %-d, %Y")


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

    ai_data = {
        "reference": reference,
        "passage": verse_text,
        "story": commentary["story"],
        "lesson": commentary["lesson"],
        "image_prompt": commentary["image_prompt"],
    }

    body: list[str] = []
    body.append(f"# Daily Reading: {reference}")
    body.append("")
    body.append(f"*{_format_date(today)}*")
    body.append("")
    if image_filename:
        body.append(f"![{commentary['image_prompt']}]({image_filename})")
        body.append("")
        body.append(f"> *(Image: {commentary['image_prompt']})*")
        body.append("")

    body.append(f"## The Reading ({translation})")
    body.append("")
    body.append(f"**{reference}**")
    body.append("")
    body.append(f"> {verse_text}")
    body.append("")

    body.append("## The Story")
    body.append("")
    body.append(commentary["story"])
    body.append("")

    body.append("## Application for Today")
    body.append("")
    body.append(commentary["lesson"])
    body.append("")

    attribution = ATTRIBUTIONS.get(translation.upper())
    if attribution:
        body.append(f"---")
        body.append("")
        body.append(f"*{attribution}*")
        body.append("")

    body.append("## Behind the Scenes: The AI Data")
    body.append("")
    body.append(
        f"For curiosity: the JSON `generate_devotional.py` requested from the "
        f"`{models.get('text', 'gemini')}` model to build this entry, and the "
        f"prompt used for the `{models.get('image', 'gemini')}` image."
    )
    body.append("")
    body.append("```json")
    body.append(json.dumps(ai_data, indent=2, ensure_ascii=False))
    body.append("```")
    body.append("")

    return _frontmatter(meta) + "\n" + "\n".join(body)
