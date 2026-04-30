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
    today = now.date()

    reference = args.reference or select_passage(cfg["content"]["reading_plan"], slot)
    print(f"[passage] {reference}", flush=True)

    fetched = fetch_verse(reference, cfg["content"]["translation"])
    if cfg["ai"].get("validate_verses", True):
        validate_verse(fetched, reference)
    verse_text = fetched.text

    commentary = generate_commentary(reference, verse_text, cfg["ai"]["text_model"])
    print(f"[title] {commentary['title']}", flush=True)

    md_path, img_path = output_paths(today, slot)
    image_filename = None
    if cfg["image"]["enabled"] and not args.skip_image:
        generate_image(commentary["image_prompt"], cfg["ai"]["image_model"], img_path)
        image_filename = img_path.name

    markdown = render_markdown(
        today=today,
        slot=slot,
        reference=reference,
        translation=cfg["content"]["translation"],
        verse_text=verse_text,
        commentary=commentary,
        models={"text": cfg["ai"]["text_model"], "image": cfg["ai"]["image_model"]},
        image_filename=image_filename,
    )

    if args.dry_run:
        print(markdown)
        print(json.dumps(commentary, indent=2))
        return 0

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(markdown)
    print(f"[wrote] {md_path}", flush=True)

    if not args.skip_notify:
        notify(
            cfg["notifications"],
            cfg["site"],
            today,
            slot,
            commentary["title"],
            reference,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
