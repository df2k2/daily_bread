from __future__ import annotations

import json
import re
from dataclasses import dataclass
from urllib.parse import quote

import requests

from .config import BIBLE_CACHE

BIBLE_API = "https://bible-api.com/{ref}?translation=web"


@dataclass
class VerseFetch:
    text: str
    verses: list[dict]
    reference: str


def _load_cache() -> dict:
    if not BIBLE_CACHE.exists():
        return {}
    with BIBLE_CACHE.open() as f:
        return json.load(f)


def _save_cache(cache: dict) -> None:
    BIBLE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with BIBLE_CACHE.open("w") as f:
        json.dump(cache, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def fetch_verse(reference: str, translation: str = "WEB") -> VerseFetch:
    if translation.upper() != "WEB":
        raise NotImplementedError(
            f"Translation {translation!r} not supported in v1; only WEB is bundled."
        )

    cache = _load_cache()
    if reference in cache and isinstance(cache[reference], dict):
        entry = cache[reference]
        return VerseFetch(
            text=entry["text"], verses=entry.get("verses", []), reference=reference
        )

    url = BIBLE_API.format(ref=quote(reference))
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

    cache[reference] = {"text": text, "verses": verses}
    _save_cache(cache)
    return VerseFetch(text=text, verses=verses, reference=reference)
