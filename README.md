# DocketAI

**Conversational agent QA** — mystery-shop your customer-service chatbot, catch regressions after knowledge-base updates, and stress-test replies with a persona × attack library.

Built by [Anna Walker](https://annabuildsai.com) · Android APKs: [DocketAI-releases](https://github.com/annamw3333-creator/DocketAI-releases)

## Problem

Chatbots drift. A FAQ edit or prompt tweak can quietly break tone, policy, or booking flows. DocketAI runs structured mystery-shop packs against a bot, scores the run, and lets you compare a **baseline** vs a later **re-check** so you see what changed.

## Stack

| Layer | Tech |
|-------|------|
| Desk API | **FastAPI** + SQLite (`desk/`) — packs, mystery-shop, baselines, bake-offs |
| Mobile | **Expo / React Native** Android app (`mobile/`) — `com.docketai.app` |
| Optional embed | WordPress plugin (`wordpress-plugin/`) — same lineage as [docket-assistant](https://github.com/annamw3333-creator/docket-assistant) |

**UI:** black / white / gold editorial theme (dark surfaces, `#C9A227` accents) — Home · Run · Results · Library · Settings.

**Live desk** (Render; free tier may cold-start): https://docketai-desk.onrender.com — `GET /health` → `{"status":"ok","service":"docket-desk"}`.

## What’s implemented

- **Mystery-shop runs** — `POST /api/mystery-shop` with bot + vertical pack (cleaning, dental, HVAC, salon)
- **Scorecards** — dimensions such as truthfulness, escalation, policy, tone, booking; history via `GET /api/runs`
- **Persona × attack library (mobile)** — **11 personas × 10 attacks** (Library tab); used to frame stress scenarios
- **Baseline vs re-check (mobile + desk)** — save pack scores with `POST /api/baselines/{pack_id}`, load with `GET /api/baselines/{pack_id}`; Run tab shows delta after a new mystery-shop
- **Bake-off / reports / embed helpers** — see `desk/README.md` for desk-only endpoints

## Repo layout

```
desk/                 FastAPI mystery-shop companion
mobile/               Expo Router Android app
wordpress-plugin/     Docket Assistant (v1.1.0) for site chat embed
render.yaml           Render blueprint for the desk service
```

## Quick start — desk

```bash
cd desk
./run.sh
# → http://localhost:8000  ·  docs at /docs
```

Useful endpoints for the mobile app:

- `GET /health`, `GET /api/packs`, `GET /api/bots`
- `POST /api/mystery-shop`, `GET /api/runs`
- `POST /api/baselines/{pack_id}`, `GET /api/baselines/{pack_id}`

Point the mobile **Settings** desk URL at your local or Render host.

## Quick start — mobile

```bash
cd mobile
yarn install --ignore-engines
yarn start
# Expo Go, or prebuild + assembleRelease for a sideload APK
```

Release APKs (embedded JS bundle — no Metro on device):  
→ [DocketAI-releases](https://github.com/annamw3333-creator/DocketAI-releases/releases) (current **v1.2.0**)

Local release build sketch:

```bash
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export ANDROID_HOME=$HOME/Android/Sdk
cd mobile
npx expo prebuild --platform android
cd android && ./gradlew assembleRelease
```

## License

MIT — see [LICENSE](LICENSE).

## Links

- Portfolio: https://annabuildsai.com  
- APK downloads: https://github.com/annamw3333-creator/DocketAI-releases  
- WordPress plugin (standalone): https://github.com/annamw3333-creator/docket-assistant  
