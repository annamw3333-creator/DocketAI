# Docket Desk

Companion mystery-shop API for **Docket Assistant** (WordPress plugin).  
Runs locally with **SQLite** — no MongoDB required for the zip demo.

## Features

| # | Feature | Endpoint / tool |
|---|---------|-----------------|
| 1 | Vertical scenario packs (cleaning / dental / HVAC / salon) | `GET /api/packs` |
| 2 | Scorecard (Truthfulness, Escalation, Policy, Tone, Booking) + history | `POST /api/mystery-shop`, `GET /api/scorecard/history` |
| 3 | Diff vs approved FAQ/script | included in mystery-shop result |
| 4 | Regression suite CLI + CI (fails on score drop) | `scripts/regression.py`, `.github/workflows/regression.yml` |
| 5 | Human-handoff test scenarios | `GET /api/handoff-scenarios` |
| 6 | Side-by-side replay + shareable report links | `POST /api/replay`, `GET /reports/{id}` |
| 7 | Bake-off: two bot URLs → ranked report | `POST /api/bakeoff` |
| 8 | Generic embed snippet generator | `POST /api/embed-snippet` |
| 9 | Alerts webhook/email on score drop | env `ALERT_*`, fired from mystery-shop |
| 10 | Suggested prompt patches from failures | `patches` in mystery-shop response |

## Quick start

```bash
cd desk
cp .env.example .env
./run.sh
# → http://localhost:8000  ·  docs at /docs
# Demo widget: http://localhost:8000/widget/harbor-hearth
```

Or manually:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
python -c "from app.seed import seed_demo; from app import storage; storage.init_db(); seed_demo()"
uvicorn app.main:app --reload --port 8000
```

## Seed demo — Harbor & Hearth

On startup (or `POST /api/seed`) the desk loads:

- **harbor-hearth** — restaurant FAQ/script (Harbor & Hearth style)
- **sparkle-cleaning** — cleaning vertical for pack demos

## Mystery-shop example

```bash
curl -s -X POST http://localhost:8000/api/mystery-shop \
  -H 'Content-Type: application/json' \
  -d '{"bot_id":"sparkle-cleaning","pack_id":"cleaning"}' | jq .
```

## Regression

```bash
python scripts/regression.py --bot sparkle-cleaning --pack cleaning --write-baseline
python scripts/regression.py --bot sparkle-cleaning --pack cleaning
# exit 1 if any dimension drops vs baseline
```

## WordPress plugin

Point **Settings → Docket Assistant → Docket URL** at `http://localhost:8000` (with `WP_DEBUG` on) or your HTTPS desk host. Bot ID: `harbor-hearth` or `sparkle-cleaning`.
