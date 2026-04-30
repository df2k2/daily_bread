from __future__ import annotations

import json
from urllib.parse import quote

import requests

from .config import BIBLE_CACHE

BIBLE_API = "https://bible-api.com/{ref}?translation=web"


def _load_cache() -> dict[str, str]:
    if not BIBLE_CACHE.exists():
        return {}
    with BIBLE_CACHE.open() as f:
        return json.load(f)


def _save_cache(cache: dict[str, str]) -> None:
    BIBLE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with BIBLE_CACHE.open("w") as f:
        json.dump(cache, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def fetch_verse(reference: str, translation: str = "WEB") -> str:
    if translation.upper() != "WEB":
        raise NotImplementedError(
            f"Translation {translation!r} not supported in v1; only WEB is bundled."
        )

    cache = _load_cache()
    if reference in cache:
        return cache[reference]

    url = BIBLE_API.format(ref=quote(reference))
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    text = payload["text"].strip()

    cache[reference] = text
    _save_cache(cache)
    return text
