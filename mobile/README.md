# DocketAI mobile

Expo / React Native app — **DocketAI** (`com.docketai.app`) **v1.3.0**.

## Screens
- **Home** — 3-line product value + CTAs (Run / Build bot / Results); Desk health
- **Run** — stepped flow: bot → pack → optional persona/attack → run; progress; deep-link to Results
- **Results** — expandable scorecards, dimension bars, pass/fail scenarios, baseline delta, **copyable patches**
- **Build** — brand URL + notes → draft system prompt/FAQ → bot selectable in Run
- **Library** — personas × attacks
- **Settings** — Desk API URL

## Theme
Black / white / gold editorial (no navy/teal).

## Build APK (JS embedded, no Metro)

```bash
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export ANDROID_HOME=$HOME/Android/Sdk
cd mobile
yarn install --ignore-engines
npx expo prebuild --platform android
# ensure android/app/build.gradle has: debuggableVariants = []
cd android && ./gradlew assembleRelease
# APK: android/app/build/outputs/apk/release/app-release.apk
```

Verify embedded bundle:

```bash
unzip -l app-release.apk | grep index.android.bundle
```

## Theme Studio (Build tab)

Pick a widget look (8 presets), optional color/greeting overrides, live preview, then **Copy embed code** for WordPress / Squarespace / any HTML. Themes apply to the customer-facing widget only.
