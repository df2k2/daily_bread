from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import quote

import requests

from .config import DATA_DIR

PUBLIC_DOMAIN = {"WEB", "KJV", "ASV", "BBE"}
LICENSED = {"NLT"}  # require user-provided fetcher; not bundled

BIBLE_API = "https://bible-api.com/{ref}?translation={t}"


@dataclass
class VerseFetch:
    text: str
    verses: list[dict]
    reference: str
    translation: str


def _cache_path(translation: str):
    return DATA_DIR / "bibles" / f"{translation.lower()}.json"


def _load_cache(translation: str) -> dict:
    path = _cache_path(translation)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_cache(translation: str, cache: dict) -> None:
    path = _cache_path(translation)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(cache, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _fetch_public_domain(reference: str, translation: str) -> tuple[str, list[dict]]:
    url = BIBLE_API.format(ref=quote(reference), t=translation.lower())
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    text = _normalize(payload["text"])
    verses = [
        {
            "book": v.get("book_name"),
            "chapter": v.get("chapter"),
            "verse": v.get("verse"),
            "text": _normalize(v.get("text", "")),
        }
        for v in payload.get("verses", [])
    ]
    return text, verses


def fetch_verse(reference: str, translation: str = "WEB") -> VerseFetch:
    t = translation.upper()

    if t in LICENSED:
        raise NotImplementedError(
            f"Translation {t!r} requires a separate licensed fetcher. "
            "Add a function in scripts/fetch_verse.py that returns "
            "(text, verses) and route it here once licensing is in place."
        )
    if t not in PUBLIC_DOMAIN:
        raise ValueError(f"Unsupported translation: {translation!r}")

    cache = _load_cache(t)
    if reference in cache and isinstance(cache[reference], dict):
        entry = cache[reference]
        return VerseFetch(
            text=entry["text"],
            verses=entry.get("verses", []),
            reference=reference,
            translation=t,
        )

    text, verses = _fetch_public_domain(reference, t)
    cache[reference] = {"text": text, "verses": verses}
    _save_cache(t, cache)
    return VerseFetch(text=text, verses=verses, reference=reference, translation=t)
