"""One-off migration for already-committed devotionals.

Brings the existing archive in line with two render changes:
  1. Verse blockquotes get superscript verse numbers (re-fetched from the same
     translation source the post was generated with).
  2. The trailing "Behind the Scenes" AI-data JSON section is removed.

Frontmatter is preserved byte-for-byte; only the body is rewritten. The script
is idempotent (a post already carrying `class="verse-num"` / lacking the JSON
section is left untouched) and never raises on a single bad file.

    python -m scripts.migrate_content --dry-run
    python -m scripts.migrate_content
"""
from __future__ import annotations

import argparse
import re
import sys

import yaml

from .config import CONTENT_DIR
from .fetch_verse import fetch_verse
from .render import scripture_blockquote

FM_RE = re.compile(r"(?s)^---\n(?P<yaml>.*?)\n---\n(?P<body>.*)$")
BEHIND_MARKERS = ("Behind the Scenes", "Nos Bastidores")


def _strip_behind(lines: list[str]) -> bool:
    """Remove the trailing AI-data section in place. Returns True if changed."""
    for i, ln in enumerate(lines):
        if ln.startswith("## ") and any(m in ln for m in BEHIND_MARKERS):
            del lines[i:]
            while lines and lines[-1].strip() == "":
                lines.pop()
            lines.append("")
            return True
    return False


def _add_superscripts(lines: list[str], reference: str, translation: str) -> bool:
    """Rewrite the passage blockquote with verse-number superscripts. Returns
    True if changed."""
    bold = f"**{reference}**"
    try:
        bi = next(i for i, ln in enumerate(lines) if ln.strip() == bold)
    except StopIteration:
        return False
    for j in range(bi + 1, len(lines)):
        s = lines[j].strip()
        if not s:
            continue
        if not s.startswith(">"):
            return False  # ran past the blockquote without finding it
        if 'class="verse-num"' in lines[j]:
            return False  # already migrated
        verses = fetch_verse(reference, translation).verses
        fallback = lines[j].lstrip("> ").strip()
        lines[j] = scripture_blockquote(verses, fallback)
        return True
    return False


def migrate_file(path, dry_run: bool) -> dict[str, bool]:
    text = path.read_text()
    m = FM_RE.match(text)
    if not m:
        return {"skipped": True}
    meta = yaml.safe_load(m.group("yaml")) or {}
    reference, translation = meta.get("reference"), meta.get("translation")
    fm_block = f"---\n{m.group('yaml')}\n---\n"
    lines = m.group("body").split("\n")

    changed_sup = False
    if reference and translation:
        try:
            changed_sup = _add_superscripts(lines, reference, translation)
        except Exception as exc:  # noqa: BLE001 - never let one file abort the run
            print(f"  ! {path.name}: verse re-fetch failed ({exc})", flush=True)
    changed_behind = _strip_behind(lines)

    if (changed_sup or changed_behind) and not dry_run:
        path.write_text(fm_block + "\n".join(lines))
    return {"superscripts": changed_sup, "behind": changed_behind}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Process at most N files.")
    args = parser.parse_args(argv)

    files = sorted(CONTENT_DIR.rglob("*.md"))
    if args.limit:
        files = files[: args.limit]

    n_sup = n_behind = n_touched = 0
    for path in files:
        result = migrate_file(path, args.dry_run)
        if result.get("skipped"):
            continue
        if result.get("superscripts") or result.get("behind"):
            n_touched += 1
            n_sup += int(result["superscripts"])
            n_behind += int(result["behind"])
            flags = []
            if result["superscripts"]:
                flags.append("superscripts")
            if result["behind"]:
                flags.append("stripped-json")
            print(f"  {'[dry] ' if args.dry_run else ''}{path.relative_to(CONTENT_DIR)}: {', '.join(flags)}")

    verb = "would change" if args.dry_run else "changed"
    print(f"\n{verb} {n_touched} file(s): {n_sup} blockquote(s), {n_behind} JSON section(s) removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
