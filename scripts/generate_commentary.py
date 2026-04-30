from __future__ import annotations

import json
from typing import Any

from google.genai import types

from .config import PROMPTS_DIR
from .gemini_client import get_client, safety_settings

_LANG_FIELDS = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "story": {"type": "string"},
        "lesson": {"type": "string"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 6,
        },
    },
    "required": ["title", "story", "lesson", "tags"],
}

SCHEMA = {
    "type": "object",
    "properties": {
        "image_prompt": {"type": "string"},
        "en": _LANG_FIELDS,
        "pt": _LANG_FIELDS,
    },
    "required": ["image_prompt", "en", "pt"],
}


def generate_commentary(
    reference: str,
    verses_by_lang: dict[str, str],
    model: str,
) -> dict[str, Any]:
    system_prompt = (PROMPTS_DIR / "devotional.md").read_text()
    blocks = [f"Passage: {reference}"]
    for lang, text in verses_by_lang.items():
        blocks.append(f"\n[{lang.upper()} text]\n{text}")
    user_input = "\n".join(blocks)

    client = get_client()
    resp = client.models.generate_content(
        model=model,
        contents=[system_prompt, user_input],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SCHEMA,
            temperature=0.7,
            safety_settings=safety_settings(),
        ),
    )
    return json.loads(resp.text)
