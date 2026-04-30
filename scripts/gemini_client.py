from __future__ import annotations

import os

from google import genai
from google.genai import types

_SAFETY = [
    types.SafetySetting(category=c, threshold="BLOCK_MEDIUM_AND_ABOVE")
    for c in (
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
    )
]


def get_client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=key)


def safety_settings() -> list[types.SafetySetting]:
    return _SAFETY
