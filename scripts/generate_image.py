from __future__ import annotations

from pathlib import Path

from google.genai import types

from .config import PROMPTS_DIR
from .gemini_client import get_client, safety_settings


def generate_image(image_prompt: str, model: str, out_path: Path) -> None:
    template = (PROMPTS_DIR / "image.md").read_text()
    full_prompt = template.replace("{image_prompt}", image_prompt.strip())

    client = get_client()
    resp = client.models.generate_content(
        model=model,
        contents=full_prompt,
        config=types.GenerateContentConfig(safety_settings=safety_settings()),
    )

    for part in resp.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(inline.data)
            return

    raise RuntimeError("Gemini image response contained no inline image data.")
