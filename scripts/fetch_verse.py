from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import requests

from .config import DATA_DIR

API_TRANSLATIONS = {"WEB", "KJV", "ASV", "BBE"}

BUNDLED_TRANSLATIONS: dict[str, str] = {
    "NLT": "sources/nlt.json",
    "PT-NVI": "sources/pt-nvi.json",
    "PT-ACF": "sources/pt-acf.json",
    "PT-AA": "sources/pt-aa.json",
}

CANONICAL_BOOKS: list[str] = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
    "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation",
]

BOOK_ALIASES: dict[str, str] = {
    "psalm": "Psalms",
    "psalms": "Psalms",
    "song of songs": "Song of Solomon",
    "song of solomon": "Song of Solomon",
    "canticles": "Song of Solomon",
}

BIBLE_API = "https://bible-api.com/{ref}?translation={t}"
REF_RE = re.compile(
    r"^(?P<book>(?:\d\s+)?[A-Za-z][A-Za-z\s]+?)\s+"
    r"(?P<chapter>\d+)"
    r"(?::(?P<vstart>\d+)(?:-(?P<vend>\d+))?)?$"
)


@dataclass
class VerseFetch:
    text: str
    verses: list[dict]
    reference: str
    translation: str


def _cache_path(translation: str) -> Path:
    return DATA_DIR / "bibles" / f"{translation.lower()}.json"


def _bundle_path(translation: str) -> Path:
    return DATA_DIR / "bibles" / BUNDLED_TRANSLATIONS[translation]


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _parse_reference(reference: str) -> tuple[str, int, int | None, int | None]:
    m = REF_RE.match(reference.strip())
    if not m:
        raise ValueError(f"Cannot parse reference: {reference!r}")
    book_in = m.group("book").strip()
    canon = BOOK_ALIASES.get(book_in.lower(), book_in)
    match = next((b for b in CANONICAL_BOOKS if b.lower() == canon.lower()), None)
    if match is None:
        raise ValueError(f"Unknown book in reference {reference!r}: {book_in!r}")
    chapter = int(m.group("chapter"))
    vstart = int(m.group("vstart")) if m.group("vstart") else None
    vend = int(m.group("vend")) if m.group("vend") else (vstart if vstart else None)
    return match, chapter, vstart, vend


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


def _fetch_api(reference: str, translation: str) -> tuple[str, list[dict]]:
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


_BUNDLE_CACHE: dict[str, object] = {}


def _load_bundle(translation: str):
    if translation not in _BUNDLE_CACHE:
        path = _bundle_path(translation)
        with path.open(encoding="utf-8-sig") as f:
            _BUNDLE_CACHE[translation] = json.load(f)
    return _BUNDLE_CACHE[translation]


def _read_bundled(reference: str, translation: str) -> tuple[str, list[dict]]:
    book, chapter, vstart, vend = _parse_reference(reference)
    data = _load_bundle(translation)

    if isinstance(data, dict):
        # NLT shape: {book: {chapter: {verse: text}}}.
        # NLT JSON uses "Psalms" exactly as the canonical name.
        book_key = book if book in data else next(
            (k for k in data if k.lower() == book.lower()), None
        )
        if book_key is None:
            raise ValueError(f"{translation}: book {book!r} missing from bundle.")
        chap_key = str(chapter)
        if chap_key not in data[book_key]:
            raise ValueError(f"{translation}: {book} {chapter} missing from bundle.")
        chap = data[book_key][chap_key]
        all_verses = sorted(int(v) for v in chap.keys())
        target = (
            list(range(vstart, vend + 1))
            if vstart is not None and vend is not None
            else all_verses
        )
        verses = []
        for v in target:
            if str(v) not in chap:
                continue
            verses.append({
                "book": book_key,
                "chapter": chapter,
                "verse": v,
                "text": _normalize(chap[str(v)]),
            })
    else:
        # Portuguese shape: [{abbrev, name, chapters: [[v1, v2, ...], ...]}, ...].
        # Books are in canonical order; index aligns with CANONICAL_BOOKS.
        idx = CANONICAL_BOOKS.index(book)
        if idx >= len(data):
            raise ValueError(f"{translation}: book index {idx} out of range.")
        entry = data[idx]
        chapters = entry.get("chapters", [])
        if chapter > len(chapters):
            raise ValueError(f"{translation}: {book} {chapter} missing from bundle.")
        chap = chapters[chapter - 1]
        all_verses = list(range(1, len(chap) + 1))
        target = (
            list(range(vstart, vend + 1))
            if vstart is not None and vend is not None
            else all_verses
        )
        verses = []
        for v in target:
            if v < 1 or v > len(chap):
                continue
            verses.append({
                "book": entry.get("name") or entry.get("abbrev") or book,
                "chapter": chapter,
                "verse": v,
                "text": _normalize(chap[v - 1]),
            })

    if not verses:
        raise ValueError(f"{translation}: no verses found for {reference!r}.")
    text = " ".join(v["text"] for v in verses)
    return text, verses


def fetch_verse(reference: str, translation: str = "WEB") -> VerseFetch:
    t = translation.upper()

    if t in BUNDLED_TRANSLATIONS:
        text, verses = _read_bundled(reference, t)
        return VerseFetch(text=text, verses=verses, reference=reference, translation=t)

    if t not in API_TRANSLATIONS:
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

    text, verses = _fetch_api(reference, t)
    cache[reference] = {"text": text, "verses": verses}
    _save_cache(t, cache)
    return VerseFetch(text=text, verses=verses, reference=reference, translation=t)
