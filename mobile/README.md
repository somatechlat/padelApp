# Andes Padel — mobile

Flutter client for the Andes Padel booking platform (courts, bookings, payments, events, tournaments, open matches, notifications). Talks to the Django API in this repo.

## Toolchain

| Item | Value | Source |
|---|---|---|
| Package name | `padel_app` | `pubspec.yaml` |
| Version | `1.0.0+8` | `pubspec.yaml` (build number is bumped by `make ship-ios`) |
| Dart SDK constraint | `^3.6.1` | `pubspec.yaml` `environment.sdk` |
| Host Flutter binary | `/usr/local/bin/flutter` | Makefile / `AGENTS.md` |
| Docker tools image (optional) | `ghcr.io/cirruslabs/flutter:3.27.3` | `docker-compose.yml` profile `tools` |

Use `/usr/local/bin/flutter`. Do not use `~/development/flutter`. Pass `--no-version-check` when invoking Flutter from scripts (the Makefile already does).

## API base URL

Required build-time define: `API_BASE_URL`.

Default in `lib/core/api_client.dart` is the **dev** API:

```
http://127.0.0.1:28002/api
```

| Build | Value |
|---|---|
| Dev / simulator | `http://127.0.0.1:28002/api` (default; or omit) |
| Test | `http://127.0.0.1:29002/api` |
| Release / TestFlight / Play | `https://www.andespadelclub.com/api` (andespadelclub.com; no server provisioned yet) |

Release builds must pass:

```bash
--dart-define=API_BASE_URL=https://www.andespadelclub.com/api
```

`make flrun`, `make fltest-dev`, and `make flbuild` already inject the dev URL.

## Locales

Four locales, Spanish-first. Template ARB is `app_es.arb` (`l10n.yaml`). Device locale is ignored.

| Locale | ARB |
|---|---|
| es (default) | `lib/core/l10n/app_es.arb` |
| en | `lib/core/l10n/app_en.arb` |
| ca | `lib/core/l10n/app_ca.arb` |
| pt | `lib/core/l10n/app_pt.arb` |

New keys must be added to all four ARBs in the same change. A key missing from `ca`/`pt` compiles and falls back to Spanish — that is a user-visible bug. After editing ARBs, run `flutter gen-l10n` and commit the regenerated `app_localizations*.dart`.

Language endonyms in the profile picker (`Español`, `English`, `Português`, `Català`) are intentional.

## Firebase prerequisite

`lib/firebase_options.dart` is **gitignored and required to compile**. `lib/core/push_notification_service.dart` imports it. Also gitignored: `android/app/google-services.json`, `ios/Runner/GoogleService-Info.plist`.

Fresh clones will not build until Firebase config is restored out-of-band or Firebase is removed. See `AGENTS.md` section 10.

## Layout

```
lib/core/      api_client, storage, friendly_error, form_validation,
               locale_controller, push_notification_service, theme, l10n, models/, widgets/
lib/features/  auth/  booking/  bookings/  events/  home/  notifications/  profile/
lib/shell/     app_shell.dart
```

`features/booking/` is the wizard + payment flow. `features/bookings/` is the list screen. Different folders — do not merge casually.

Errors shown in the UI must go through `lib/core/friendly_error.dart` (`friendlyErrorMessage`). Never render `e.toString()` or `DioException` dumps.

## Run

```bash
# from repo root, with the dev stack up
make up-dev
make flrun

# iOS simulator against dev
make ios-sim-dev
```

Direct:

```bash
cd mobile
flutter run --no-version-check \
  --dart-define=API_BASE_URL=http://127.0.0.1:28002/api
```

## Test

```bash
make fltest-dev    # against the dev API (stack must be up for most tests)
make flcheck       # flutter analyze — must report No issues found
```

Offline-safe tests: `test/brand_logo_test.dart`, `test/password_field_test.dart`. Others expect a live dev API. Prefer asserting `hasError` / `lastError` over `AuthState.error` (the latter is `null` for Dio/network failures).

## Build

| Target | Command | Notes |
|---|---|---|
| Debug APK | `make flbuild` / `make flapk` | Against dev API; `flapk` copies to repo root `padelapp-debug.apk` |
| Release APK / AAB | see `store/README.md` | Must pass prod `API_BASE_URL`; Play signing config is gitignored |
| TestFlight | `make ship-ios` | Needs `ASC_USER`, `ASC_PASSWORD` |

### `make ship-ios`

```bash
ASC_USER='<apple-id>' ASC_PASSWORD='<app-specific-password>' make ship-ios
```

Runs `mobile/tool/release_ipa.sh`: bumps the pubspec build number, `flutter pub get`, `flutter build ipa --release --export-options-plist ios/ExportOptions.plist`, uploads `build/ios/ipa/padel_app.ipa` via `xcrun altool`. Details in `docs/BUILD_AND_DEPLOY.md`.

## Bundle identifiers

| Platform | ID |
|---|---|
| Android `applicationId` | `com.andes.padel.padel_app` |
| iOS | `com.andes.padel.padelApp` |

They differ on purpose.

## Store screenshot capture

`integration_test/capture_store_test.dart` walks login → home → all five tabs
→ the booking wizard and writes the PNGs used for both store listings.
`integration_test/capture_public_test.dart` covers the pre-login screens.

Run it against the local seeded stack (`make up-dev && make seeddemo-dev`) so
the shots contain real bookings rather than empty states:

```bash
SCREENSHOT_DIR=/tmp/shots flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/capture_store_test.dart \
  --dart-define=API_BASE_URL=http://localhost:28002/api \
  --dart-define=SKIP_PUSH_PROMPT=true --dart-define=SKIP_PUSH=true \
  --dart-define=SHOT_EMAIL=cliente@andespadelclub.com \
  --dart-define=SHOT_PASSWORD=Andes12345! \
  -d "iPhone 17 Pro Max"
```

Two defines exist only for this:

| Define | Why |
|---|---|
| `SKIP_PUSH_PROMPT` | The iOS permission sheet is not a Flutter widget and swallows every tap. |
| `SKIP_PUSH` | In the simulator there is no APNS token, so `getToken()` blocks for a minute and starves the parallel Dio calls. Production builds never set either. |

See `AGENTS.md` §8 for the traps this harness encodes.

## Account deletion

`ProfileScreen` has a destructive **Borrar cuenta** row calling
`POST /api/gdpr/me/erase/`. Apple Guideline 5.1.1(v) requires in-app account
deletion for any app that supports account creation, and
`landing/privacy.html` already promised the button existed. Do not remove it.

## Release

```bash
make ship-ios       # bump build → IPA → TestFlight. Needs ASC_USER +
                    # an app-specific password (not the Apple ID password).
make ship-android   # signed AAB for Play. Fails closed without key.properties.
```

Both must pass `API_BASE_URL=https://app.andespadelclub.com/api`. A release
binary that falls back to `127.0.0.1` installs fine and cannot reach any API
on a device — `baseUrlFor()` now throws rather than ship that.
