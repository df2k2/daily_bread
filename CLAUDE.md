# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A self-hosted daily Bible devotional service in two halves that communicate only through committed files in `content/`:

1. **Python generation pipeline** (`scripts/`) — picks a passage, fetches the verses, drafts a bilingual devotional with Gemini, generates artwork, and writes markdown + a PNG into `content/`. Runs in GitHub Actions on cron.
2. **Astro 5 + React 19 + RizzUI site** (`site/`) — reads `../content/` via Astro's `glob` content loader and deploys the archive to GitHub Pages.

There is **no shared runtime** between the two: the pipeline commits markdown, and a separate deploy workflow rebuilds the site when `content/` (or `site/`) changes.

## Commands

Pipeline (run from repo root; scripts are a package, always invoke with `-m`):

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...                 # required for any generation
python -m scripts.generate_devotional --reference "Psalm 23" --skip-notify
python -m scripts.generate_devotional --dry-run   # prints output, writes nothing
python -m scripts.list_models             # print Gemini models your key can access
```

Useful `generate_devotional` flags: `--slot morning|evening` (otherwise derived from current hour), `--reference` (override passage selection), `--skip-image`, `--skip-notify`, `--dry-run`.

Site:

```bash
cd site
pnpm install
pnpm dev      # local dev against ../content/
pnpm build    # production build → site/dist
```

There is **no automated test suite**. Verify pipeline changes with `--dry-run` and `--skip-notify`; verify site changes with `pnpm build`.

## Architecture notes that span multiple files

**`config.yml` is the single source of truth** for languages, models, reading plan, image settings, and notification recipients — read by nearly every script via `scripts/config.py`. Exception: `schedule.frequency`/`times` are **not read by anything**; only `schedule.timezone` is consumed (to pick the morning/evening slot and localize dates). Actual run times are the cron lines in `.github/workflows/generate.yml`.

**Bilingual generation is a single Gemini call.** `generate_commentary.py` sends both languages' verse text in one request and enforces a JSON schema returning `image_prompt` + one block per language (`title`, `story`, `lesson`, `tags`). One devotional run therefore produces N markdown files (one per `content.languages`) that **share one image** and one `image_prompt`. The AI is prompted to write language-native prose, not translation. To add a language, add it under `content.languages` and add its block to `SCHEMA` in `generate_commentary.py`.

**Same-day devotionals are linked.** Before generating, `generate_devotional.py` calls `render.previous_today()` to find the most recent same-day post in the primary language and passes its theme to `generate_commentary(..., prior=...)` as an `[Earlier today]` block. The prompt (`prompts/devotional.md`) tells the model to harmonize with it while standing fully alone. Passage selection is unaffected (still the reading plan), and the first run of a day has no prior. `prior` is dropped if it would point at the same reference.

**The reading plan is a state machine.** `data/state.json` holds the plan cursor and a rolling history (last 60 picks). `select_passage.py` dispatches on the plan's `type` in `data/reading_plan.json`:
- `random` — avoids the last 7 picks.
- `sequential` — advances an index each run.
- `daily` (e.g. mcheyne) — picks per-slot readings and advances the day index **only after the evening run**.

The generate workflow commits `data/state.json` back to the repo, so the cursor persists across CI runs. Local runs mutate it too.

**Verse sources are split** (`fetch_verse.py`): `WEB/KJV/ASV/BBE` are fetched from bible-api.com and cached to `data/bibles/<translation>.json` (the cache is committed back by CI); `NLT` and the `PT-*` translations are bundled JSON under `data/bibles/sources/` and read directly. Reading-plan references are always English book names; the fetcher resolves them against the canonical 66-book order so one reference yields the right text per language. These bundled translations are copyrighted — attribution strings live in `render.py` and are appended to each post.

**Validation gates the pipeline.** When `ai.validate_verses` is true, `validate_verse.py` runs before commentary and raises on a bad fetch (wrong verse count, out-of-order numbers, refusal phrases, etc.), so malformed scripture never reaches the site.

**Output filenames encode a timestamp to prevent overwrites.** `render.output_paths()` produces `content/YYYY/MM/DD-HHMM-<reference-slug>-<lang>.md` plus a shared `DD-HHMM-<reference-slug>.png`. Re-running in the same day never clobbers prior content. Markdown frontmatter (`date`, `datetime`, `slot`, `lang`, `reference`, `book`, `translation`, `tags`, `excerpt`, `image`, `ai` models) is what the site sorts/filters on — `site/src/content.config.ts` must stay in sync with the keys `render.py` writes.

**The passage blockquote is inline HTML.** `render.scripture_blockquote()` builds the quote from the structured `verses` list, prefixing each verse with `<sup class="verse-num">N</sup>` (styled lighter in `site/src/styles/globals.css`; Astro renders the raw HTML in markdown). The post body is otherwise plain markdown — there is no AI-data/JSON section (removed). `scripts/migrate_content.py` is the one-off that retro-applied both changes to the existing archive; it rewrites only the body and is idempotent, so it's safe to re-run if older-format posts surface.

**Site i18n routing:** the primary language (`PRIMARY` in `site/src/lib/i18n.ts`) lives at `/`; others mount under `/<lang>/`. Each locale has its own RSS feed, archive, and tag pages. UI strings live in `i18n.ts`; the pipeline's notification/section copy is separate (in `notify.py` and `render.py`).

## Workflows (`.github/workflows/`)

- **generate.yml** — cron (twice daily) + manual dispatch with reference/slot/skip toggles. Runs the pipeline and commits `content/`, `data/state.json`, and `data/bibles/`. When it commits, it dispatches **deploy.yml** (`gh workflow run`), because a `GITHUB_TOKEN` push does not trigger another workflow's `push` event — hence the job's `actions: write` permission.
- **deploy.yml** — `push` to `main` touching `site/**`/`content/**` (human edits) **or** `workflow_dispatch` (from generate.yml); builds the Astro site and deploys to GitHub Pages.
- **healthcheck.yml** — hourly; opens/updates a GitHub issue if no `content/` commit landed in the last 26 hours.

Required Actions secrets: `GEMINI_API_KEY` (always), `RESEND_API_KEY` (email), `TWILIO_SID`/`TWILIO_TOKEN` (SMS).
