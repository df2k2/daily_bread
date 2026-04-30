# daily_bread

A self-hosted daily Bible devotional service. GitHub Actions runs a Python pipeline that picks a passage, drafts a short devotional with Gemini 3.1 Pro, generates artwork with a Gemini image model, and commits the result to `/content/`. An Astro 5 + React 19 + RizzUI site builds the archive and deploys to GitHub Pages. Optional email (Resend) and SMS (Twilio) notifications go out with each new entry.

See `config.yml` to tune schedule, reading plan, models, and notifications.

## Layout

```
scripts/        Python generation pipeline
prompts/        System prompts for commentary and image generation
data/           reading_plan.json, state.json, bibles/web.json (cached verses)
content/        Generated markdown + images, committed by the bot
site/           Astro 5 + RizzUI 2.1.0 site (deployed to Pages)
.github/        Workflows
config.yml      All user-tunable settings
```

## Phase 1 setup

### Secrets

Set in repo Settings → Secrets and variables → Actions:

- `GEMINI_API_KEY` — from https://aistudio.google.com/
- `RESEND_API_KEY` — only if email is enabled in `config.yml`
- `TWILIO_SID`, `TWILIO_TOKEN` — only if SMS is enabled

### First run (locally)

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...
python -m scripts.generate_devotional --reference "Psalm 23" --skip-notify
```

This writes `content/<year>/<month>/<day>-<slot>.md` and a `.png` next to it. Verify Gemini's output before scheduling.

### First run (GitHub Actions)

Use the **Generate devotional** workflow's *Run workflow* button. It accepts an optional reference override and a skip-image / skip-notify toggle for testing.

### Site (locally)

```bash
cd site
pnpm install
pnpm dev
```

The site reads markdown from `../content/` via Astro 5's `glob` content loader.

## Schedule

Generate runs twice a day on cron (~06:00 and ~18:00 America/Los_Angeles, with ~10 min margin for GH Actions cron drift). Adjust the cron lines in `.github/workflows/generate.yml` if you change `schedule.timezone` in `config.yml`.

A separate `healthcheck.yml` workflow runs hourly and opens a GitHub issue if no new content has been committed in the last 26 hours, so a silently-failing cron won't go unnoticed.

## Reading plans

`config.yml` → `content.reading_plan` selects from `data/reading_plan.json`:

- **`random`** — picks from a curated list of well-known passages, avoiding the last 7 picks.
- **`sequential_psalms`** — cycles through 30 hand-picked psalms in order.
- **`mcheyne`** — daily 4-reading classic plan, routed by slot (morning vs. evening). Only the first 10 days are pre-seeded; expand `data/reading_plan.json` from a trusted source (e.g. Edinburgh Bible Society) for a full year. The selector handles slot rotation and day advancement automatically.

`type: "daily"` plans support a `morning`/`evening` reading list per day. The generator picks one reading per slot and advances to the next day after the evening run.

## Translation

v1 ships with WEB (public domain). The verse fetcher uses [bible-api.com](https://bible-api.com) and caches results into `data/bibles/web.json`, which is committed back to the repo so subsequent runs are deterministic and offline-safe. NLT support requires a Tyndale license — see plan §2.1.

## Verse validation

When `ai.validate_verses: true` (default), the fetched passage is checked for:

- Structured per-verse data present
- Verse count matches the requested range (e.g. `John 3:16-21` → 6 verses)
- Verse numbers in ascending order
- Plausible word count per verse (catches truncation)
- Plain-text sanity (length, no model-refusal phrases)

A failure raises before commentary generation, so a bad fetch never reaches the site.

## Costs and caps

Set a monthly budget cap in Google Cloud Console for the Gemini API. Twilio and Resend each have their own billing.
