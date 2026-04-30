from __future__ import annotations

from pathlib import Path

from google.genai import types

from .config import PROMPTS_DIR
from .gemini_client import get_client, safety_settings


def _summarize_response(resp) -> str:
    bits: list[str] = []
    feedback = getattr(resp, "prompt_feedback", None)
    if feedback:
        bits.append(f"prompt_feedback={feedback}")
    candidates = getattr(resp, "candidates", None) or []
    for i, c in enumerate(candidates):
        finish = getattr(c, "finish_reason", None)
        if finish:
            bits.append(f"candidate[{i}].finish_reason={finish}")
        parts = getattr(getattr(c, "content", None), "parts", None) or []
        kinds = [type(getattr(p, "inline_data", None)).__name__ if getattr(p, "inline_data", None) else "text" for p in parts]
        bits.append(f"candidate[{i}].part_kinds={kinds}")
        for p in parts:
            text = getattr(p, "text", None)
            if text:
                snippet = text[:200].replace("\n", " ")
                bits.append(f"candidate[{i}].text={snippet!r}")
    return " | ".join(bits) or "<empty response>"


def generate_image(image_prompt: str, model: str, out_path: Path) -> None:
    template = (PROMPTS_DIR / "image.md").read_text()
    full_prompt = template.replace("{image_prompt}", image_prompt.strip())

    client = get_client()
    resp = client.models.generate_content(
        model=model,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            safety_settings=safety_settings(),
        ),
    )

    for part in resp.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and inline.data:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(inline.data)
            return

    raise RuntimeError(
        "Gemini image response contained no inline image data. "
        f"Model={model!r}. Response: {_summarize_response(resp)}"
    )
