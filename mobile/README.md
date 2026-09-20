# DocketAI mobile

Expo / React Native app — **DocketAI** (`com.docketai.app`) v1.0.0.

## Screens
- **Home** — Desk API health, pack/bot counts
- **Run** — pick bot + pack, mystery-shop, Baseline vs Re-check regression stub
- **Results** — recent runs / scorecards
- **Library** — personas × attacks
- **Settings** — Desk API URL

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
