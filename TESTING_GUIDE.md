# Testing Guide

How to run the suites and how the live HTTP surface is shaped. Ports, commands and routes below are taken from the Makefile, compose overlays and `apps/*/urls.py`.

## Prerequisites

| Suite | Needs |
|---|---|
| Django (`make test-dev`) | Dev stack up (`make up-dev`) — Postgres and Redis |
| Flutter (`make fltest-dev`) | Dev stack up for integration-style tests. Offline-safe: `brand_logo_test.dart`, `password_field_test.dart` |
| Playwright (`tests/e2e/`) | A reachable admin panel. **`E2E_BASE_URL` is required** — no default is baked in |

Host Flutter for `make fltest-dev` / `make flcheck` / `make flrun` is `/usr/local/bin/flutter` (see `AGENTS.md`). Do not use `~/development/flutter`.

Fresh clones also need `mobile/lib/firebase_options.dart` (gitignored, required to compile). See `AGENTS.md` section 10.

## Environments and ports

There is no host port 8000. Inside the container Django binds 8000; host ports are:

| Env | Project | Postgres | Redis | API | Nginx |
|---|---|---|---|---|---|
| dev | `andespadel` | 28000 | 28001 | 28002 | 28003 |
| test | `andespadel-test` | 29000 | 29001 | 29002 | 29003 |
| prod | `andespadel-prod` | 34000 | 34001 | 34002 | 34003 |

API base URLs used by the Makefile and the mobile client:

| Env | API base |
|---|---|
| dev | `http://127.0.0.1:28002/api` |
| test | `http://127.0.0.1:29002/api` |
| prod | `https://<new-domain>/api` (operator-supplied; old host retired) |

Compose is always base + overlay + project name:

```bash
docker compose -p andespadel      -f docker-compose.yml -f docker-compose.dev.yml  up -d
docker compose -p andespadel-test -f docker-compose.yml -f docker-compose.test.yml up -d
docker compose -p andespadel-prod -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Prefer the make targets. Test and prod use `padel.settings.dev` and `padel.settings.prod` respectively (test is plain `padel.settings.dev`, not a special test settings module).

## Commands

### Django

```bash
make up-dev      # stack must be up first
make test-dev    # pytest apps -q  inside the backend container
make test-test   # same, against the test project
```

Tests live colocated per app (`apps/<app>/tests.py`, `tests_api.py`, `tests_auth.py`, `tests_security.py`). 215 tests (count as of `AGENTS.md`).

### Flutter

```bash
make up-dev        # most mobile tests hit the live dev API
make fltest-dev    # flutter test --dart-define=API_BASE_URL=http://127.0.0.1:28002/api
make flcheck       # flutter analyze
```

Direct (host Flutter):

```bash
cd mobile
/usr/local/bin/flutter test --no-version-check --suppress-analytics \
  --dart-define=API_BASE_URL=http://127.0.0.1:28002/api
```

Tests live in `mobile/test/`. Some assert on `AuthState.error`; that getter returns `null` for Dio/network failures, so those assertions pass when the API is down. Prefer `hasError` / `lastError` or a real success signal.

### Playwright E2E

```bash
./tests/e2e/run.sh                 # all tests
./tests/e2e/run.sh test_login.py   # one file
```

Uses `tests/e2e/pytest.ini` (marker `e2e`). **`E2E_BASE_URL` is required** — the suite refuses to start without it. 111 admin + 28 auth tests (count as of `AGENTS.md`). Separate from the Django suite.

### Lint

```bash
make lint      # ruff check . && flake8 && bandit -r apps   (backend container)
make flcheck   # flutter analyze
```

Host Python (faster):

```bash
python3 -m ruff check .
python3 -m flake8 apps padel
```

## Demo data

```bash
make seeddemo-dev     # or seeddemo-test
make seed             # seed_courts only (dev project)
```

Demo password for all seeded users: `Andes12345!`. Seed targets are for dev/test only — never run them against prod.

There is no `make seed-test`. Use `seeddemo-test`.

## API surface

Mounted at `/api/` with **no version segment**. Source: `padel/urls.py` and `apps/*/urls.py`.

### Auth and account (`/api/auth/`)

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register/` | |
| POST | `/api/auth/verify/` | Email verification |
| POST | `/api/auth/login/` | Returns JWT |
| POST | `/api/auth/refresh/` | Token refresh |
| POST | `/api/auth/logout/` | |
| POST | `/api/auth/password-reset/` | |
| POST | `/api/auth/password-reset/confirm/` | |
| POST | `/api/auth/password/change/` | |
| GET | `/api/auth/skill-levels/` | |
| GET, PUT, PATCH | `/api/auth/me/` | Current user |
| POST | `/api/auth/me/devices/` | Register push device token |
| POST | `/api/auth/me/consent/` | GDPR consent |
| GET | `/api/auth/me/export/` | GDPR export |
| POST | `/api/auth/me/erase/` | GDPR erase |

No `resend` route exists in `apps/users/urls.py`.

### Courts and club

| Method | Path | Notes |
|---|---|---|
| GET | `/api/courts/` | |
| POST | `/api/courts/` | Staff |
| GET | `/api/courts/{id}/` | |
| PUT, PATCH | `/api/courts/{id}/` | Staff |
| DELETE | `/api/courts/{id}/` | Staff |
| GET | `/api/courts/{id}/availability/` | Auth. Query `date=YYYY-MM-DD` |
| GET | `/api/club/` | Club info |
| GET | `/api/banners/` | Promo banners |

### Bookings

| Method | Path | Notes |
|---|---|---|
| GET | `/api/bookings/` | Owner sees own; staff see all |
| POST | `/api/bookings/` | Create |
| GET | `/api/bookings/{id}/` | |
| POST | `/api/bookings/preview/` | Price preview |
| POST | `/api/bookings/{id}/confirm/` | |
| POST | `/api/bookings/{id}/cancel/` | |
| GET | `/api/bookings/available-starts/` | Public. Query `date`, `duration_minutes` |

There is no booking update or delete route; cancel is the exit path.

### Payments

| Method | Path | Notes |
|---|---|---|
| POST | `/api/bookings/{booking_id}/payments/` | Create/record payment for a booking |
| POST | `/api/payments/{id}/upload-proof/` | Transfer proof upload |
| POST | `/api/payments/{id}/confirm/` | |
| POST | `/api/payments/{id}/confirm-transfer/` | Staff |
| POST | `/api/payments/{id}/reject-transfer/` | Staff |
| POST | `/api/payments/{id}/refund/` | Staff |
| POST | `/api/webhooks/stripe/` | Stripe webhook |

There is no `POST /api/payments/`. Payment creation is nested under the booking.

### Events, tournaments, open matches, news

| Method | Path | Notes |
|---|---|---|
| GET | `/api/events/` | |
| POST | `/api/events/` | Staff |
| GET, PUT, PATCH, DELETE | `/api/events/{id}/` | Writes staff-only |
| POST | `/api/events/{id}/join/` | |
| POST | `/api/events/{id}/leave/` | |
| GET | `/api/tournaments/` | Read-only list |
| GET | `/api/tournaments/{id}/` | |
| POST | `/api/tournaments/{id}/register/` | |
| POST | `/api/tournaments/{id}/confirm/` | |
| GET | `/api/open-matches/` | |
| POST | `/api/open-matches/` | |
| GET, PUT, PATCH, DELETE | `/api/open-matches/{id}/` | Writes restricted |
| POST | `/api/open-matches/{id}/join/` | |
| POST | `/api/open-matches/{id}/leave/` | |
| GET | `/api/news/` | |
| POST | `/api/news/` | Staff |
| GET, PUT, PATCH, DELETE | `/api/news/{id}/` | Writes staff-only |

### Notifications

| Method | Path | Notes |
|---|---|---|
| GET | `/api/notifications/` | |
| GET | `/api/notifications/unread-count/` | |
| POST | `/api/notifications/read-all/` | |
| POST | `/api/notifications/{id}/read/` | |
| GET, PUT | `/api/notifications/preferences/` | |

### Reports (staff)

| Method | Path |
|---|---|
| GET | `/api/reports/revenue/` |
| GET | `/api/reports/occupancy/` |
| GET | `/api/reports/customers/` |
| GET | `/api/reports/cancellations/` |

### Schema and admin

| Method | Path | Notes |
|---|---|---|
| GET | `/api/schema/` | OpenAPI (drf-spectacular) |
| GET | `/api/docs/` | Swagger UI |
| GET | `/api/redoc/` | ReDoc |
| * | `/adminpanel/` | Server-rendered staff dashboard |
| * | `/adminpanel/login/` | Admin login |
| * | `/adminpanel/logout/` | |
| * | `/adminpanel/dashboard/` | |
| * | `/adminpanel/calendar/` | |
| * | `/adminpanel/courts/` | |
| * | `/adminpanel/users/` | |
| * | `/adminpanel/payments/` | |
| * | `/adminpanel/events/` | |
| * | `/adminpanel/reports/` | |
| * | `/adminpanel/settings/` | |
| * | `/adminpanel/banners/` | |
| * | `/adminpanel/audit/` | |
| * | `/admin/` | Django admin |

## Smoke checks

```bash
# API is up (expects an auth error body without credentials)
curl http://127.0.0.1:28002/api/auth/me/

# OpenAPI schema
curl http://127.0.0.1:28002/api/schema/

# Logs / DB
make logs
make psql
```

## Build artifacts

| Artifact | How |
|---|---|
| Debug APK | `make flbuild` or `make flapk` (copies to `./padelapp-debug.apk`) |
| iOS simulator (dev API) | `make ios-sim-dev` |
| TestFlight | `make ship-ios` (needs `ASC_USER`, `ASC_PASSWORD`) |

API URL for any release build must be set explicitly:

```bash
--dart-define=API_BASE_URL=https://<new-domain>/api
```

Bundle ids differ on purpose: Android `com.andes.padel.padel_app`, iOS `com.andes.padel.padelApp`.
