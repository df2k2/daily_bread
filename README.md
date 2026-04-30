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

## Enabling the schedule

Uncomment the `schedule:` block in `.github/workflows/generate.yml`. Cron times are UTC; pick an hour offset to compensate for the configured timezone in `config.yml`.

## Translation

v1 ships with WEB (public domain). The verse fetcher uses [bible-api.com](https://bible-api.com) and caches results into `data/bibles/web.json`, which is committed back to the repo so subsequent runs are deterministic and offline-safe. NLT support requires a Tyndale license — see plan §2.1.

## Costs and caps

Set a monthly budget cap in Google Cloud Console for the Gemini API. Twilio and Resend each have their own billing.
