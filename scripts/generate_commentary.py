from __future__ import annotations

import json
from typing import Any

from google.genai import types

from .config import PROMPTS_DIR
from .gemini_client import get_client, safety_settings

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "context": {"type": "string"},
        "application": {"type": "string"},
        "takeaways": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
        "prayer": {"type": "string"},
        "image_prompt": {"type": "string"},
    },
    "required": ["title", "context", "application", "takeaways", "prayer", "image_prompt"],
}


def generate_commentary(reference: str, verse_text: str, model: str) -> dict[str, Any]:
    system_prompt = (PROMPTS_DIR / "devotional.md").read_text()
    user_input = f"Passage: {reference}\n\nText:\n{verse_text}"

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
