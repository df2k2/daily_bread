# daily_bread

A self-hosted daily Bible devotional service. GitHub Actions runs a Python pipeline that picks a passage, drafts a short devotional with Gemini, generates artwork with a Gemini image model, and commits the result to `/content/`. An Astro 5 + React 19 + RizzUI site builds the archive and deploys to GitHub Pages. Optional email (Resend) and SMS (Twilio) notifications go out with each new entry.

Set `ai.text_model` and `ai.image_model` in `config.yml` to model IDs your Gemini API key can access. Run `python -m scripts.list_models` (with `GEMINI_API_KEY` exported) to print the models available to you.

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

## Translations

`content.translation` in `config.yml` accepts any of:

- `WEB`, `KJV`, `ASV`, `BBE` — public domain, fetched from [bible-api.com](https://bible-api.com) and cached at `data/bibles/<translation>.json`.
- `NLT` — **bundled** at `data/bibles/sources/nlt.json` (from [DrTooru/NLT-Bible-JSON](https://github.com/DrTooru/NLT-Bible-JSON)).
- `PT-NVI`, `PT-ACF`, `PT-AA` — Brazilian Portuguese, **bundled** at `data/bibles/sources/pt-*.json` (from [thiagobodruk/biblia](https://github.com/thiagobodruk/biblia)).

> ⚠️ **Licensing notice:** The NLT (Tyndale House), NVI (Biblica), and Almeida revisions are **copyrighted**. They are bundled here for convenience but their public redistribution may require a license from the rights holder. If this repo or its GitHub Pages site is public, verify your usage falls under fair use or obtain explicit permission. The bundled sources carry no included license file.

Reading-plan references use English book names (e.g. `John 3:16-21`). The fetcher resolves them against the canonical 66-book order — Portuguese bundles are looked up by index, so passing `John 3:16-21` with `translation: PT-ACF` returns the Portuguese verse text.

Switching translations is a config change; existing devotionals retain the translation they were generated under (recorded in frontmatter).

## Verse validation

When `ai.validate_verses: true` (default), the fetched passage is checked for:

- Structured per-verse data present
- Verse count matches the requested range (e.g. `John 3:16-21` → 6 verses)
- Verse numbers in ascending order
- Plausible word count per verse (catches truncation)
- Plain-text sanity (length, no model-refusal phrases)

A failure raises before commentary generation, so a bad fetch never reaches the site.

## Recipients

Each recipient in `config.yml` → `notifications.recipients` is an object that opts into channels and slots:

```yaml
recipients:
  - name: "Alice"
    email: "alice@example.com"
    slots: ["morning"]        # only morning notifications
    channels: ["email"]
  - name: "Bob"
    email: "bob@example.com"
    sms: "+15551234567"
    slots: []                 # both slots
    channels: ["email", "sms"]
```

The notifier sends per-recipient and per-channel — Alice gets a morning email only, Bob gets both slots on both channels. Empty `slots` means all slots; omitting a channel field skips that channel even if it's listed.

## RSS and search

- `/rss.xml` is generated at build time from the content collection. Auto-discovery `<link>` is in the base layout so feed readers find it.
- `/archive` ships a client-side search box backed by a static `/search-index.json` (title, reference, slot, date, snippet). Pure browser-side filtering — no extra infra.

## Costs and caps

Set a monthly budget cap in Google Cloud Console for the Gemini API. Twilio and Resend each have their own billing.
