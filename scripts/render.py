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


def output_paths(today: date, slot: str, lang: str) -> tuple[Path, Path]:
    folder = CONTENT_DIR / f"{today:%Y}" / f"{today:%m}"
    base = f"{today:%d}-{slot}"
    return folder / f"{base}.{lang}.md", folder / f"{base}.png"


def _format_date(d: date, lang: str) -> str:
    formatted = d.strftime(LABELS[lang]["date_format"])
    if lang == "pt":
        for en_name, pt_name in PT_MONTHS.items():
            formatted = formatted.replace(en_name, pt_name)
    return formatted


def render_markdown(
    today: date,
    slot: str,
    reference: str,
    translation: str,
    verse_text: str,
    title: str,
    story: str,
    lesson: str,
    image_prompt: str,
    models: dict[str, str],
    image_filename: str | None,
    lang: str,
) -> str:
    labels = LABELS[lang]
    meta = {
        "date": today.isoformat(),
        "slot": slot,
        "lang": lang,
        "reference": reference,
        "translation": translation,
        "title": title,
        "ai": models,
    }
    if image_filename:
        meta["image"] = image_filename

    ai_data = {
        "reference": reference,
        "passage": verse_text,
        "story": story,
        "lesson": lesson,
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
