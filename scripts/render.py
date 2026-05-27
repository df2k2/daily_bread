from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import frontmatter
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
        "date_format": "%B %-d, %Y",
    },
    "pt": {
        "heading": "Leitura Diária",
        "reading": "A Leitura",
        "story": "A História",
        "application": "Aplicação para Hoje",
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


def scripture_blockquote(verses: list[dict], fallback_text: str = "") -> str:
    """A single markdown blockquote of the passage with each verse number
    rendered as a lighter superscript (`<sup class="verse-num">`). Falls back
    to plain text if structured verses aren't available."""
    parts: list[str] = []
    for v in verses or []:
        text = (v.get("text") or "").strip()
        if not text:
            continue
        num = v.get("verse")
        if num is not None:
            parts.append(f'<sup class="verse-num">{num}</sup> {text}')
        else:
            parts.append(text)
    if not parts:
        return f"> {fallback_text}".rstrip()
    return "> " + " ".join(parts)


def previous_today(when: datetime, lang: str) -> dict | None:
    """The most recent devotional already written today in `lang`, if any.

    Used so a day's later devotional can harmonize with the earlier one. Reads
    only frontmatter (title/reference/tags/excerpt); returns None on the first
    run of the day. Never raises on a malformed file — a bad read just means no
    prior context.
    """
    folder = CONTENT_DIR / f"{when:%Y}" / f"{when:%m}"
    if not folder.exists():
        return None
    today_iso = when.date().isoformat()
    candidates: list[tuple[str, frontmatter.Post]] = []
    for path in folder.glob(f"*-{lang}.md"):
        try:
            post = frontmatter.load(str(path))
        except Exception:
            continue
        if str(post.get("date")) != today_iso:
            continue
        candidates.append((str(post.get("datetime") or path.name), post))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    post = candidates[-1][1]
    return {
        "reference": post.get("reference"),
        "title": post.get("title"),
        "tags": post.get("tags") or [],
        "excerpt": post.get("excerpt") or "",
    }


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
    verses: list[dict],
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
    body.append(scripture_blockquote(verses, verse_text))
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

    return _frontmatter(meta) + "\n" + "\n".join(body)
