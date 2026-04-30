from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import load_config
from .fetch_verse import fetch_verse
from .generate_commentary import generate_commentary
from .generate_image import generate_image
from .notify import notify
from .render import output_paths, render_markdown, slot_for_hour
from .select_passage import select_passage
from .validate_verse import validate_verse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=["morning", "evening"], default=None)
    parser.add_argument("--reference", default=None, help="Override passage selection.")
    parser.add_argument("--skip-image", action="store_true")
    parser.add_argument("--skip-notify", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of writing.")
    args = parser.parse_args(argv)

    cfg = load_config()
    tz = ZoneInfo(cfg["schedule"]["timezone"])
    now = datetime.now(tz)
    slot = args.slot or slot_for_hour(now.hour)

    languages: dict = cfg["content"]["languages"]
    if not languages:
        raise RuntimeError("config.yml: content.languages is empty.")

    reference = args.reference or select_passage(cfg["content"]["reading_plan"], slot)
    print(f"[passage] {reference}", flush=True)

    fetched_by_lang = {}
    verses_by_lang: dict[str, str] = {}
    for lang, lang_cfg in languages.items():
        fetched = fetch_verse(reference, lang_cfg["translation"])
        if cfg["ai"].get("validate_verses", True):
            validate_verse(fetched, reference)
        fetched_by_lang[lang] = fetched
        verses_by_lang[lang] = fetched.text
        print(f"[verse:{lang}] {lang_cfg['translation']} {len(fetched.verses)} verse(s)", flush=True)

    commentary = generate_commentary(reference, verses_by_lang, cfg["ai"]["text_model"])
    for lang in languages:
        tags = commentary[lang].get("tags") or []
        print(f"[title:{lang}] {commentary[lang]['title']} (tags: {', '.join(tags)})", flush=True)

    primary = cfg["content"]["primary_language"]
    _, img_path = output_paths(now, slot, primary, reference)
    image_filename = None
    if cfg["image"]["enabled"] and not args.skip_image:
        generate_image(commentary["image_prompt"], cfg["ai"]["image_model"], img_path)
        image_filename = img_path.name

    written: dict[str, str] = {}
    for lang, lang_cfg in languages.items():
        markdown = render_markdown(
            when=now,
            slot=slot,
            reference=reference,
            translation=lang_cfg["translation"],
            verse_text=fetched_by_lang[lang].text,
            title=commentary[lang]["title"],
            story=commentary[lang]["story"],
            lesson=commentary[lang]["lesson"],
            tags=commentary[lang].get("tags") or [],
            image_prompt=commentary["image_prompt"],
            models={"text": cfg["ai"]["text_model"], "image": cfg["ai"]["image_model"]},
            image_filename=image_filename,
            lang=lang,
        )
        md_path, _ = output_paths(now, slot, lang, reference)
        if args.dry_run:
            print(f"--- {md_path} ---")
            print(markdown)
            continue
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown)
        written[lang] = str(md_path)
        print(f"[wrote:{lang}] {md_path}", flush=True)

    if args.dry_run:
        print(json.dumps(commentary, indent=2, ensure_ascii=False))
        return 0

    if not args.skip_notify:
        titles_by_lang = {lang: commentary[lang]["title"] for lang in languages}
        notify(
            cfg["notifications"],
            cfg["site"],
            now.date(),
            slot,
            titles_by_lang,
            reference,
            primary_language=primary,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
