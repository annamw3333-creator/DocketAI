# DocketAI

**AI customer-service QA** for chatbots — mystery-shop testing, regression runs after knowledge-base updates, and a customer × attack library.

## What's in this repo

| Path | Purpose |
|------|---------|
| `desk/` | FastAPI mystery-shop companion (packs, scorecards, bake-offs, SQLite) |
| `wordpress-plugin/` | Docket Assistant WordPress plugin (hardened v1.1.0) |
| `mobile/` | Expo / React Native Android app — **DocketAI** `com.docketai.app` v1.0.0 |

## Quick start — desk

```bash
cd desk
./run.sh
```

Desk API highlights used by the mobile app:

- `GET /health`, `GET /api/packs`, `GET /api/bots`
- `POST /api/mystery-shop`, `GET /api/runs`
- `POST /api/baselines/{pack_id}`, `GET /api/baselines/{pack_id}`

## Android APK (v1.0.0)

Sideload builds are on [Releases](https://github.com/annamw3333-creator/DocketAI/releases).

- **Package:** `com.docketai.app`
- **JS embedded** in the APK (`assets/index.android.bundle`) — no Metro packager required on device
- **UI:** dark navy / teal; tabs Home · Run · Results · Library · Settings
- **Library:** 11 personas × 10 attacks; Run tab includes Baseline vs Re-check regression stub

### Build locally

```bash
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export ANDROID_HOME=$HOME/Android/Sdk
cd mobile
yarn install --ignore-engines
npx expo prebuild --platform android
# android/app/build.gradle must include: debuggableVariants = []
cd android && ./gradlew assembleRelease
# → android/app/build/outputs/apk/release/app-release.apk
```

Verify embed:

```bash
unzip -l app-release.apk | grep index.android.bundle
```

## Owner

Anna Walker (`annamw3333-creator`)
