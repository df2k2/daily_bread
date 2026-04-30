from __future__ import annotations

import json
import re
from datetime import date, datetime
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

LABELS: dict[str, dict[str, str]] = {
    "en": {
        "heading": "Daily Reading",
        "reading": "The Reading",
        "story": "The Story",
        "application": "Application for Today",
        "behind": "Behind the Scenes: The AI Data",
        "behind_intro": (
            "For curiosity: the JSON the generator received from the text "
            "model and the prompt used for the image."
        ),
        "date_format": "%B %-d, %Y",
    },
    "pt": {
        "heading": "Leitura Diária",
        "reading": "A Leitura",
        "story": "A História",
        "application": "Aplicação para Hoje",
        "behind": "Nos Bastidores: Os Dados da IA",
        "behind_intro": (
            "Por curiosidade: o JSON que o gerador recebeu do modelo de "
            "texto e o prompt usado para a imagem."
        ),
        "date_format": "%-d de %B de %Y",
    },
}

PT_MONTHS = {
    "January": "janeiro", "February": "fevereiro", "March": "março",
    "April": "abril", "May": "maio", "June": "junho",
    "July": "julho", "August": "agosto", "September": "setembro",
    "October": "outubro", "November": "novembro", "December": "dezembro",
}


def _frontmatter(meta: dict[str, Any]) -> str:
    return "---\n" + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).strip() + "\n---\n"


def slot_for_hour(hour: int) -> str:
    return "morning" if hour < 12 else "evening"


def reference_slug(reference: str) -> str:
    s = reference.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def book_from_reference(reference: str) -> str:
    m = re.match(r"^((?:\d\s+)?[A-Za-z][A-Za-z\s]+?)\s+\d+", reference.strip())
    return m.group(1).strip() if m else reference.split()[0]


def _normalize_tag(tag: str) -> str:
    return re.sub(r"\s+", " ", tag).strip().lower()


def tag_slug(tag: str) -> str:
    s = _normalize_tag(tag)
    # Keep lowercase letters (incl. accented) and digits; everything else → hyphen.
    s = re.sub(r"[^\w]+", "-", s, flags=re.UNICODE)
    return s.strip("-")


def output_paths(when: datetime, slot: str, lang: str, reference: str) -> tuple[Path, Path]:
    today = when.date()
    folder = CONTENT_DIR / f"{today:%Y}" / f"{today:%m}"
    base = f"{today:%d}-{when:%H%M}-{reference_slug(reference)}"
    return folder / f"{base}-{lang}.md", folder / f"{base}.png"


def _format_date(d: date, lang: str) -> str:
    formatted = d.strftime(LABELS[lang]["date_format"])
    if lang == "pt":
        for en_name, pt_name in PT_MONTHS.items():
            formatted = formatted.replace(en_name, pt_name)
    return formatted


def _excerpt(story: str, lesson: str, max_len: int = 280) -> str:
    text = re.sub(r"\s+", " ", story).strip()
    if len(text) >= 120:
        return text[:max_len].rstrip() + ("…" if len(text) > max_len else "")
    combined = (text + " " + re.sub(r"\s+", " ", lesson).strip()).strip()
    return combined[:max_len].rstrip() + ("…" if len(combined) > max_len else "")


def render_markdown(
    when: datetime,
    slot: str,
    reference: str,
    translation: str,
    verse_text: str,
    title: str,
    story: str,
    lesson: str,
    tags: list[str],
    image_prompt: str,
    models: dict[str, str],
    image_filename: str | None,
    lang: str,
) -> str:
    labels = LABELS[lang]
    today = when.date()
    normalized_tags = sorted({_normalize_tag(t) for t in tags if t.strip()})
    excerpt = _excerpt(story, lesson)

    meta: dict[str, Any] = {
        "date": today.isoformat(),
        "datetime": when.isoformat(),
        "slot": slot,
        "lang": lang,
        "reference": reference,
        "book": book_from_reference(reference),
        "translation": translation,
        "title": title,
        "tags": normalized_tags,
        "excerpt": excerpt,
        "ai": models,
    }
    if image_filename:
        meta["image"] = image_filename

    ai_data = {
        "reference": reference,
        "passage": verse_text,
        "story": story,
        "lesson": lesson,
        "tags": normalized_tags,
        "image_prompt": image_prompt,
    }

    body: list[str] = []
    body.append(f"# {labels['heading']}: {reference}")
    body.append("")
    body.append(f"*{_format_date(today, lang)}*")
    body.append("")
    if image_filename:
        body.append(f"![{image_prompt}]({image_filename})")
        body.append("")
        body.append(f"> *(Image: {image_prompt})*")
        body.append("")

    body.append(f"## {labels['reading']} ({translation})")
    body.append("")
    body.append(f"**{reference}**")
    body.append("")
    body.append(f"> {verse_text}")
    body.append("")

    body.append(f"## {labels['story']}")
    body.append("")
    body.append(story)
    body.append("")

    body.append(f"## {labels['application']}")
    body.append("")
    body.append(lesson)
    body.append("")

    attribution = ATTRIBUTIONS.get(translation.upper())
    if attribution:
        body.append("---")
        body.append("")
        body.append(f"*{attribution}*")
        body.append("")

    body.append(f"## {labels['behind']}")
    body.append("")
    body.append(labels["behind_intro"])
    body.append("")
    body.append("```json")
    body.append(json.dumps(ai_data, indent=2, ensure_ascii=False))
    body.append("```")
    body.append("")

    return _frontmatter(meta) + "\n" + "\n".join(body)
