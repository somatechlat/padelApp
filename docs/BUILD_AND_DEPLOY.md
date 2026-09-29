# Build and Deploy

Last verified against source: 2026-09-29.

Covers the three Docker Compose environments, backend images, mobile builds, and the TestFlight pipeline.

## Compose model

`docker-compose.yml` holds the shared service definitions. It must never be run alone. Always pair it with an env overlay and a project name:

| Env | Project | Command shape | Settings module |
|---|---|---|---|
| dev | `andespadel` | `docker compose -p andespadel -f docker-compose.yml -f docker-compose.dev.yml ...` | `padel.settings.dev` |
| test | `andespadel-test` | `docker compose -p andespadel-test -f docker-compose.yml -f docker-compose.test.yml ...` | `padel.settings.dev` |
| prod | `andespadel-prod` | `docker compose -p andespadel-prod -f docker-compose.yml -f docker-compose.prod.yml ...` | `padel.settings.prod` |

Use the Makefile targets (`up-dev`, `up-test`, `up-prod`, and the matching `down-*` / `test-*` / `seeddemo-*`). They encode the correct `-p` and `-f` flags.

`compose.prod.yml` and `compose.server.yml` at the repo root are **legacy and unused** by the Makefile. Do not extend them.

Services in every env: `db` (Postgres 15), `redis` (Redis 7), `backend`, `worker` (Celery), `beat` (Celery beat), `nginx`, and an optional `flutter` tools container (compose profile `tools`).

## Ports

There is **no host port 8000**. Django binds 8000 inside the container.

| Offset | Service | dev | test | prod |
|---|---|---|---|---|
| +0 | Postgres | 28000 | 29000 | 34000 |
| +1 | Redis | 28001 | 29001 | 34001 |
| +2 | backend / API | 28002 | 29002 | 34002 |
| +3 | nginx | 28003 | 29003 | 34003 |

Nginx serves the landing page from `./landing/` and proxies `/api/`, `/adminpanel/`, `/admin/` to the backend.

## Volumes and network

Named volumes are prefixed by compose project, not `padelapp_*`:

| Env | Volume examples |
|---|---|
| dev | `andespadel_db_data`, `andespadel_media_data`, `andespadel_static_data`, `andespadel_flutter_home`, `andespadel_gradle_home`, `andespadel_android_sdk` |
| test | `andespadel-test_db_data`, `andespadel-test_media_data`, … |
| prod | `andespadel-prod_db_data`, `andespadel-prod_media_data`, … |

Networks: `andespadel-net`, `andespadel-test-net`, `andespadel-prod-net`.

If a Docker Flutter/Gradle cache is corrupt, remove the matching `*_gradle_home` / `*_flutter_home` / `*_android_sdk` volumes and rebuild.

## Backend images

| File | User | Purpose |
|---|---|---|
| `Dockerfile.dev` | `app` (uid 1000) | Dev/test. `requirements-dev.txt`, venv at `/opt/venv`, `runserver` |
| `Dockerfile.prod` | `appuser` | Prod. `requirements.txt`, gunicorn `padel.wsgi:application --bind 0.0.0.0:8000 --workers 3` |

Non-root usernames differ on purpose: `app` in `Dockerfile.dev`, `appuser` in `Dockerfile.prod`.

Dev/test mount `./docker/backend` as `/app/runsecrets` (read-only). Prod secrets live on the server under `/opt/padelapp/docker/backend/secrets.py` and are validated at startup by `padel/settings/prod.py` / `_checks.py`.

## Django settings

| File | Role |
|---|---|
| `padel/settings/base.py` | Shared. `TIME_ZONE=America/Guayaquil`, `LANGUAGE_CODE=es`, Celery, DRF/JWT, i18n |
| `padel/settings/dev.py` | `DEBUG=True`, `ALLOWED_HOSTS=["*"]`, open CORS, `CELERY_TASK_ALWAYS_EAGER=True` |
| `padel/settings/prod.py` | `DEBUG=False`, host allowlist, SSL/HSTS, secret validation |
| `padel/settings/local_sqlite.py` | Overlay for docker-less tests |
| `padel/settings/_checks.py` | Fail-fast production secret validation |

Prod `ALLOWED_HOSTS` is derived from `PROD_DOMAIN` in `settings/secrets.py` and is **required** — the module refuses to import without it. Test env uses `padel.settings.dev` — there is no separate test settings module.

## API URL (mobile)

`mobile/lib/core/api_client.dart` defaults to:

```
http://127.0.0.1:28002/api
```

That is the dev API. Every release build must override it:

```bash
--dart-define=API_BASE_URL=https://www.andespadelclub.com/api
```

| Env | API base |
|---|---|
| dev | `http://127.0.0.1:28002/api` |
| test | `http://127.0.0.1:29002/api` |
| prod | `https://www.andespadelclub.com/api` |

Makefile `API_DEV` / `API_TEST` / `API_PROD` match these values.

## Bundle identifiers

| Platform | Identifier | Source |
|---|---|---|
| Android `applicationId` | `com.andes.padel.padel_app` | `mobile/android/app/build.gradle` |
| iOS `PRODUCT_BUNDLE_IDENTIFIER` | `com.andes.padel.padelApp` | `mobile/ios/Runner.xcodeproj/project.pbxproj` |

These differ on purpose. Do not conflate them.

## Makefile targets

| Target | What it does |
|---|---|
| `up-dev` / `up-test` / `up-prod` | Start the matching stack |
| `down-dev` / `down-test` / `down-prod` | Stop the matching stack |
| `test-dev` / `test-test` | `pytest apps -q` inside that stack's backend |
| `fltest-dev` | `flutter test` against `API_DEV` |
| `seeddemo-dev` / `seeddemo-test` | `manage.py seed_demo` (dev/test only) |
| `seed` | `manage.py seed_courts` (dev project) |
| `lint` | `ruff check . && flake8 && bandit -r apps` in the backend container |
| `flcheck` | `flutter analyze` |
| `flrun` | `flutter run` against `API_DEV` |
| `flbuild` / `flapk` | Debug APK; `flapk` copies it to `./padelapp-debug.apk` |
| `ios-sim-dev` | `flutter run -d "iPhone 17 Pro"` against `API_DEV` |
| `ship-ios` | Build release IPA and upload to TestFlight |
| `migrate` / `makemigrations` | Django migrations (dev project) |
| `logs` / `shell` / `bash` / `psql` | Ops helpers (dev project) |
| `build` | Build the dev backend image |

Aliases `up`, `down`, `test`, `seeddemo`, `fltest` map to the dev variants.

There is no `make seed-test`. Use `seeddemo-test`.

## Local development

```bash
make up-dev
make migrate            # also runs automatically on backend start
make seeddemo-dev       # optional demo data, password Andes12345!
curl http://127.0.0.1:28002/api/auth/me/
```

Access points on dev:

| URL | What |
|---|---|
| `http://127.0.0.1:28002/api/` | REST API |
| `http://127.0.0.1:28002/api/docs/` | Swagger |
| `http://127.0.0.1:28002/adminpanel/` | Staff dashboard |
| `http://127.0.0.1:28002/admin/` | Django admin |
| `http://127.0.0.1:28003/` | nginx (landing + proxy) |

## Production deploy (compose)

On the server (path `/opt/padelapp` per current runbook):

```bash
docker compose -p andespadel-prod \
  -f docker-compose.yml -f docker-compose.prod.yml \
  up -d

docker compose -p andespadel-prod \
  -f docker-compose.yml -f docker-compose.prod.yml \
  exec backend python manage.py migrate

docker compose -p andespadel-prod \
  -f docker-compose.yml -f docker-compose.prod.yml \
  exec backend python manage.py collectstatic --no-input
```

Or simply `make up-prod` / `make down-prod` from a checkout with the Makefile.

Prod backend runs gunicorn (see `docker-compose.prod.yml` command override). Public URL: the new production domain, supplied by the operator.

### Server host IP — UNVERIFIED

This repo disagrees on the production server address:

- Every previously documented server address is **retired**. Production is
  moving to a new host and domain whose values the operator has not yet
  supplied. Do not treat any address in these docs as a deploy target.

**Every previously documented address is retired.** Production is moving to a new server and domain; the operator supplies both. Nothing in this tree names a production host on purpose.

### Server constraints (from ops notes)

- Do not touch Loyallia containers, networks, or configs.
- Do not use ports 33900–33914 (Loyallia range).
- Do not bind host 80/443 from Docker; host nginx owns those and proxies to `127.0.0.1:34003`.
- Reload host nginx (`nginx -s reload`); do not restart it.

## Mobile — Android

```bash
make flbuild            # debug APK against the dev API
make flapk              # same, copies to ./padelapp-debug.apk
```

Or on the host:

```bash
cd mobile
flutter pub get
flutter build apk --debug \
  --dart-define=API_BASE_URL=http://127.0.0.1:28002/api
```

| Build | Output |
|---|---|
| Debug | `mobile/build/app/outputs/flutter-apk/app-debug.apk` |
| Release | `mobile/build/app/outputs/flutter-apk/app-release.apk` |

Release APK/AAB must pass `--dart-define=API_BASE_URL=https://www.andespadelclub.com/api`. Signing for Play (keystore, `key.properties`) is documented in `store/README.md` and is gitignored.

`applicationId`: `com.andes.padel.padel_app`.

## Mobile — iOS

### Simulator against dev

```bash
make ios-sim-dev
```

### TestFlight pipeline (`make ship-ios`)

One command builds a release IPA and uploads it to App Store Connect TestFlight:

```bash
ASC_USER='<apple-id>' ASC_PASSWORD='<app-specific-password>' make ship-ios
```

What `mobile/tool/release_ipa.sh` does (invoked by `make ship-ios`):

1. Requires `ASC_USER` and `ASC_PASSWORD` (app-specific password from appleid.apple.com).
2. Bumps the `version:` build number in `mobile/pubspec.yaml`.
3. `flutter pub get`.
4. Deletes any stale `build/ios/ipa/padel_app.ipa`.
5. `flutter build ipa --release --export-options-plist ios/ExportOptions.plist`.
6. Verifies the IPA exists, then `xcrun altool --upload-app --type ios`.

Output IPA: `mobile/build/ios/ipa/padel_app.ipa`. It appears in App Store Connect → TestFlight after Apple processes it (typically 5–15 minutes).

Flutter used by the script defaults to `/usr/local/bin/flutter` (override with `FLUTTER=`). SPM packages cache under `~/Library/Caches/org.swift.swiftpm/` after the first run.

iOS bundle id: `com.andes.padel.padelApp`. Export team and provisioning live in `mobile/ios/ExportOptions.plist` and `store/README.md`.

### Unsigned debug

```bash
cd mobile
flutter pub get
cd ios && pod install && cd ..
flutter build ios --debug --no-codesign
```

## Celery beat schedule (prod)

Defined in `padel/settings/base.py` `CELERY_BEAT_SCHEDULE`. Dev sets `CELERY_TASK_ALWAYS_EAGER=True`, so tasks run inline.

| Task | Interval | Purpose |
|---|---|---|
| `tournament-reminder-daily` | 24 hours | Tournament reminders |
| `booking-reminder-daily` | 24 hours | Booking reminders |
| `booking-reminder-2h` | 30 minutes | Two-hour-before booking reminders |
| `release-expired-holds` | 5 minutes | Release expired slot holds |

## Troubleshooting

| Symptom | Action |
|---|---|
| Gradle zip corruption in Docker | `docker volume rm andespadel_gradle_home` then `make flapk` (adjust prefix for test/prod) |
| Mass Flutter SDK compile errors in Docker | Corrupted cache: remove `andespadel_flutter_home`, `andespadel_gradle_home`, `andespadel_android_sdk` and rebuild |
| APK will not install | Enable unknown sources; clear old install: `adb shell pm clear com.andes.padel.padel_app` |
| App cannot reach API | Confirm the build's `API_BASE_URL`. Dev is `http://127.0.0.1:28002/api`, not port 8000 |
| Backend will not start in prod | Secrets missing or still placeholders — `prod.py` / `_checks.py` reject them |
| Fresh clone does not compile Flutter | `mobile/lib/firebase_options.dart` is gitignored and imported. Generate it (`flutterfire configure`) or restore out-of-band. See `AGENTS.md` §10 |
| `make seed-test` fails | Target does not exist. Use `seeddemo-test` |
