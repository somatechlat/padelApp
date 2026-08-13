# PadelApp (Andes Pádel) — Full Development Plan (Docker-First)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan phase-by-phase.

**Goal:** Deliver a production-ready padel court reservation system — Django REST API + Flutter mobile app + web admin panel — for Andes Pádel (Quito), per SRS `docs/srs/` v1.1.

**Architecture (Docker-first — EVERYTHING runs in Docker):** Django 5.x + DRF backend, PostgreSQL 15, Redis 7, Celery worker, and the Flutter toolchain are all containerized. No host-installed Python packages, no host venv, no host database. The only host requirements are Docker + Docker Compose (+ git). Settings-package config (`base/dev/prod/secrets.py`, no env vars). TDD throughout.

**Tech Stack:** Python 3.12, Django 5.x, DRF 3.15+, drf-spectacular, SimpleJWT, celery, django-cryptography (Fernet), pytest; Flutter 3.x, dio, provider, flutter_localizations, secure_storage; Stripe. All inside Docker images.

**Constraints honored (SRS C1–C12):** Django-only backend · no env-var secrets (`secrets.py` git-ignored, volume-mounted into containers) · Argon2 + validators · full i18n · PostgreSQL-only prod · UTC · Swagger docs · tests per module · PCI SAQ-A (no card data stored) · tokens in platform secure storage.

---

## Docker Services (dev) — `docker-compose.yml`

| Service | Image | Purpose |
|---------|-------|---------|
| `db` | `postgres:15-alpine` | PostgreSQL 15, named volume, healthcheck |
| `redis` | `redis:7-alpine` | Celery broker + JWT blacklist |
| `backend` | build from `Dockerfile.dev` | Django dev server (hot-reload), pytest, manage.py, ruff/flake8/bandit |
| `worker` | same image as `backend` | Celery worker (`-l info`) |
| `flutter` | `ghcr.io/cirruslabs/flutter:3.x` | Flutter/Dart toolchain: analyze, test, build APK/AAB (Android SDK baked in) |

**Container network:** service names as hostnames (`db`, `redis`) — no host IPs, no env vars. DB/Redis credentials come from the volume-mounted `secrets.py` (SRS C2/C3).

**Key compose settings:**
- `backend`/`worker`: bind-mount `./` → `/app`, `docker/backend/secrets.py` → `/app/padel/settings/secrets.py` (read-only), named volume for `.venv` and media.
- `backend` command: `python manage.py runserver 0.0.0.0:8000` (Django autoreload).
- `worker` command: `celery -A padel worker -l info`.
- `flutter` bind-mount `./mobile` → `/mobile`; HOME set to a named volume (pub cache persists).

**One-liner aliases (all commands in this plan assume these exist in a `Makefile`):**
```makefile
up:        docker compose up -d
down:      docker compose down
logs:      docker compose logs -f
migrate:   docker compose exec backend python manage.py migrate
makemigrations: docker compose exec backend python manage.py makemigrations
test:      docker compose run --rm backend pytest
lint:      docker compose run --rm backend sh -c "ruff check . && flake8 && bandit -r apps"
flcheck:   docker compose run --rm flutter flutter analyze
fltest:    docker compose run --rm flutter flutter test
flbuild:   docker compose run --rm flutter flutter build apk --debug
```

**Convention used throughout this plan:**
- Backend commands → `docker compose exec backend <cmd>` (or `run --rm backend`)
- Flutter commands → `docker compose run --rm flutter <cmd>`
- Database shell → `docker compose exec db psql -U padel -d padel`

---

## Timeline (Rapid / weekly delivery)

| Sprint | Phase | Deliverable (working software) |
|--------|-------|-------------------------------|
| S1 | Phases 0–2 | Backend skeleton + Auth API fully tested (all in Docker) |
| S2 | Phases 3–5 | Courts/Availability + Booking + Pricing API |
| S3 | Phases 6–8 | Payments + Cancellations + Notifications |
| S4 | Phase 9 | Admin panel + Reports + Events/Tournaments |
| S5 | Phase 10 | i18n + Security hardening |
| S6 | Phases 11–13 | Flutter app (auth, booking, events) in the `flutter` container |
| S7 | Phase 14 | Release prep: stores, deployment, UAT |

---

## Phase 0 — Project Setup (Foundation, all in Docker)

**Files:**
- Create: `docker-compose.yml`, `Dockerfile.dev`, `Dockerfile.prod`, `compose.prod.yml`, `docker/backend/Dockerfile`, `docker/backend/entrypoint.sh`, `docker/backend/secrets.example.py`, `.dockerignore`, `.gitignore`, `.pre-commit-config.yaml`, `Makefile`
- Create: `padel/settings/base.py`, `dev.py`, `prod.py`, `secrets.py` (git-ignored), `__init__.py`
- Create: `padel/urls.py`, `wsgi.py`, `asgi.py`, `padel/celery.py`
- Create: `apps/__init__.py`, `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `pytest.ini`, `conftest.py`, `utils/`

**Step 1: Init repo**
```bash
git init
```
Expected: empty repo, `git status` clean.

**Step 2: Author `docker-compose.yml` + `Dockerfile.dev`**
```yaml
# docker-compose.yml (dev)
services:
  db:
    image: postgres:15-alpine
    environment: { POSTGRES_DB: padel, POSTGRES_USER: padel, POSTGRES_PASSWORD: padel_dev }
    volumes: [db_data:/var/lib/postgresql/data]
    healthcheck: { test: ["CMD-SHELL","pg_isready -U padel -d padel"], interval: 5s, retries: 10 }
  redis:
    image: redis:7-alpine
    healthcheck: { test: ["CMD","redis-cli","ping"], interval: 5s, retries: 10 }
  backend:
    build: { context: ., dockerfile: Dockerfile.dev }
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - ./docker/backend/secrets.py:/app/padel/settings/secrets.py:ro
      - backend_venv:/app/.venv
    ports: ["8000:8000"]
    depends_on: { db: {condition: service_healthy}, redis: {condition: service_healthy} }
  worker:
    build: { context: ., dockerfile: Dockerfile.dev }
    command: celery -A padel worker -l info
    volumes: [".:/app", "./docker/backend/secrets.py:/app/padel/settings/secrets.py:ro", "backend_venv:/app/.venv"]
    depends_on: [backend]
  flutter:
    image: ghcr.io/cirruslabs/flutter:3.27
    working_dir: /mobile
    volumes:
      - ./mobile:/mobile
      - flutter_home:/home/cirrus
    stdin_open: true
    tty: true
volumes: { db_data: {}, backend_venv: {}, flutter_home: {} }
```
```dockerfile
# Dockerfile.dev
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements*.txt ./
RUN pip install -r requirements-dev.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

**Step 3: Secrets (volume-mounted, no env vars)**
- Create `docker/backend/secrets.py` (git-ignored, chmod 600) from `secrets.example.py`:
```python
# docker/backend/secrets.py  (NOT committed)
SECRET_KEY = "dev-only-secret-do-not-use"
DB_NAME = "padel"
DB_USER = "padel"
DB_PASSWORD = "padel_dev"
DB_HOST = "db"
DB_PORT = 5432
REDIS_URL = "redis://redis:6379/0"
STRIPE_SECRET_KEY = "sk_test_..."     # test key
STRIPE_PUBLISHABLE_KEY = "pk_test_..."
```
- `base.py` imports DB/REDIS/STRIPE from `secrets.py`; `prod.py` adds a boot-time check that fails fast if `SECRET_KEY` starts with `dev-only-` or any value is blank (SRS NFR-0008).

**Step 4: Build + verify infra**
```bash
docker compose build
docker compose up -d db redis
docker compose ps        # db & redis healthy
docker compose run --rm backend python manage.py check
```
Expected: services `Up (healthy)`; `manage.py check` reports 0 issues.

**Step 5: First commit**
```bash
git add -A && git commit -m "chore: docker-first foundation, settings package, infra"
```

**Exit criteria:** `docker compose ps` all healthy; `manage.py check` clean **inside the container**; prod settings fail fast on missing secrets.

---

## Phase 1 — Custom User & Role Model (M01)

**Files:**
- Create: `apps/users/models.py`, `apps/users/managers.py`, `apps/users/admin.py`, `apps/users/apps.py`, `apps/users/migrations/`, `apps/users/tests.py`
- Create: `apps/users/serializers.py` (partial), `apps/users/views.py` (partial)

**Step 1: Write failing tests** (`apps/users/tests.py`)
- `test_create_user_requires_email` — email required, normalized lowercase, password hashed Argon2.
- `test_create_superuser` — is_staff/is_superuser set.
- `test_roles_valid` — role choices (cliente/recepcionista/gerente/dueño/superadmin) enforced; default `cliente`.
- `test_account_states` — status `active/suspended/blocked/deleted`; login blocked when not active.

**Step 2: Run to verify fail**
```bash
docker compose run --rm backend pytest apps/users/tests.py -v
```
Expected: FAIL (ImportError — no model).

**Step 3: Implement**
```python
# apps/users/models.py
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    language_code = models.CharField(max_length=8, default="es", choices=settings.LANGUAGES)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENTE)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    email_verified = models.BooleanField(default=False)
    consent_version = models.CharField(max_length=16, null=True, blank=True)
    consent_ts = models.DateTimeField(null=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()
```
- `managers.py`: `UserManager` with `create_user`/`create_superuser`.
- Register in `admin.py` with read-only audit fields.

**Step 4: Migrate + run (in container)**
```bash
docker compose exec backend python manage.py makemigrations users
docker compose exec backend python manage.py migrate
docker compose run --rm backend pytest apps/users/tests.py -v
```
Expected: PASS.

**Step 5: Commit** — `git add -A && git commit -m "feat: custom User model with roles and account states"`

**Exit criteria:** user model tests pass in the container; migration applied to the `db` container; admin lists users.

---

## Phase 2 — Auth API (M01, M13 tokens)

**Files:**
- Create: `apps/users/serializers.py`, `apps/users/views.py`, `apps/users/urls.py`
- Create: `apps/verification/` — email code model/service for F-0003 (6-digit code, 15 min, 5 attempts)
- Modify: `padel/urls.py`, `padel/settings/base.py` (SIMPLE_JWT config)

**Endpoints (05-interface §5.1.4):** `register`, `verify`, `login`, `refresh`, `logout`, `password-reset`, `password-reset/confirm`, `password/change`, `me`, `me/devices`.

**Steps (TDD per endpoint):**
1. `test_register_creates_inactive_user_with_code` → 201, email code issued, consent required.
2. `test_register_duplicate_email_409` localized message.
3. `test_verify_code_activates`; `test_verify_wrong_5_times_expires`.
4. `test_login_returns_access_refresh`; `test_login_locked_after_5_failures` (30 min).
5. `test_refresh_rotation_and_reuse_revokes_family` (SimpleJWT rotating + blacklist).
6. `test_password_reset_link_single_use_no_enumeration`.
7. `test_change_password_revokes_tokens`.
8. `test_me_patch_updates_profile`.

Implement `RefreshTokenFamily` model (encrypted seed) + device-bound refresh (SRS F-0072). Rate-limit auth endpoints via DRF throttles (NFR-0003). SMTP mocked in tests (in-container `EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'`).

```bash
docker compose run --rm backend pytest apps/users/tests.py apps/verification/tests.py -v
docker compose exec backend python manage.py spectacular --file schema.yml
git add -A && git commit -m "feat: auth API with JWT rotation and verification"
```

**Exit criteria:** all auth endpoints pass in container; lockout/rotation/reuse tests green; Swagger lists auth routes.

---

## Phase 3 — Courts, Scheduling & Availability (M02, M03)

**Files:**
- Create: `apps/courts/models.py`, `admin.py`, `serializers.py`, `views.py`, `urls.py`, `tests.py`
- Create: `apps/scheduling/models.py` (TimeSlot, MaintenanceWindow, BookingHold), `services.py` (slot generation), `tests.py`

**Models:** `Venue` (timezone `America/Guayaquil`, currency USD), `Court` (type techada/abierta, has_lighting, status), `CourtSchedule` (per weekday), `MaintenanceWindow`, `TimeSlot` (30-min), `BookingHold`.

**Steps:**
1. Tests: court CRUD role-gated; archive prevents new bookings.
2. Tests: slot generation honors schedule, 30-min grid, durations 60/90/120, no past slots; maintenance window excluded.
3. Tests: availability endpoint excludes booked/held/blocked/maintenance/past/archived.
4. Tests: hold created at checkout, 10-min expiry, auto-release on payment failure, anti-hoarding limit.
5. Implement + migrate + run all tests green.

```bash
docker compose exec backend python manage.py makemigrations courts scheduling
docker compose exec backend python manage.py migrate
docker compose run --rm backend pytest apps/courts apps/scheduling -v
git add -A && git commit -m "feat: courts, schedules, slot generation, availability, holds"
```

**Exit criteria:** availability accurate; slot generation race-safe; holds expire.

---

## Phase 4 — Booking Engine & Pricing (M04, M05)

**Files:**
- Create: `apps/bookings/models.py` (Booking, BookingSlot, state machine), `services.py`, `serializers.py`, `views.py`, `urls.py`, `tests.py`
- Create: `apps/pricing/models.py` (PriceRule, Holiday), `services.py`, `tests.py`

**Steps (TDD, highest rigor — coverage ≥ 90%):**
1. Pricing: tariff formula test (base × zone × day × court-type), valle/pico boundaries, weekday/weekend/holiday, price-preview ignores client-supplied price.
2. Booking create: transaction + `select_for_update` on slots; **concurrency test** — 50 parallel attempts on same slot → exactly 1 success (SRS F-0020). Run inside the container with the real `db` container (PostgreSQL row locks).
3. State machine: legal/illegal transitions; every transition audited.
4. Reschedule (≥24h, free slots, price diff), cancel (policy), no-show workflow, invoice generation (tax 0% RIMPE).

```bash
docker compose run --rm backend pytest apps/bookings apps/pricing -v
git add -A && git commit -m "feat: booking engine, state machine, pricing engine"
```

**Exit criteria:** concurrency test proves no double-booking against real Postgres; state machine airtight; pricing server-authoritative.

---

## Phase 5 — Payments (M06, Stripe)

**Files:**
- Create: `apps/payments/models.py` (Payment lifecycle), `services.py` (Stripe client), `views.py` (confirm-payment, admin: transfer/cash/refund), `urls.py`, `tests.py`
- Modify: `apps/bookings/services.py` (hold→authorize→confirm→capture flow)

**Steps:**
1. Stripe PaymentIntent creation (test keys from volume-mounted `secrets.py`); authorize at booking.
2. Capture on booking start; penalty capture on no-show.
3. Bank transfer `pending_transfer` → admin confirm; cash recorded by receptionist.
4. Refunds (full/partial) via Stripe; reconciliation report.
5. PCI: verify **no card fields** in models/DB (static scan NFR-0028) — run `bandit` in container.

```bash
docker compose run --rm backend pytest apps/payments -v
docker compose run --rm backend bandit -r apps
git add -A && git commit -m "feat: payments with Stripe, transfers, cash, refunds"
```

**Exit criteria:** payment lifecycle green in test mode; no card data stored; refunds correct.

---

## Phase 6 — Cancellation & Penalties (M07)

**Files:**
- Create: `apps/policies/models.py` (CancellationPolicy config), `services.py`, `tests.py`
- Modify: `apps/bookings/services.py` (cancel path uses policy engine)

**Steps:**
1. Policy config: free-window ≥24h, penalty 50% inside, no-show 100%, hold 10 min (defaults) — all configurable.
2. Penalty computed from **server UTC time** at cancel instant (client clock never trusted).
3. No-show suggestion 30 min after start → confirm marks no_show + charges + notifies.

```bash
docker compose run --rm backend pytest apps/policies -v
git add -A && git commit -m "feat: cancellation policy, penalties, no-show"
```

**Exit criteria:** penalty math correct across window boundaries; TZ tests green.

---

## Phase 7 — Notifications (M08)

**Files:**
- Create: `apps/notifications/models.py` (Notification, NotificationPreference, DeviceToken), `services.py`, `tasks.py` (Celery), `fcm.py` (FCM/APNS client — mocked in tests), `views.py`, `urls.py`, `tests.py`

**Steps:**
1. Triggers: booking confirmed, reminders (24h/2h), cancellation, no-show penalty, payment success/failure, transfer confirmed, event published.
2. Channels: in-app + email (mocked SMTP) + push (mocked FCM).
3. Preferences per event/channel (marketing opt-out; transactional always).
4. Celery async with retry/backoff + idempotency keys (no duplicates). Tests use `CELERY_TASK_ALWAYS_EAGER=True`; real dispatch exercised against the `worker` container.
5. Verify worker delivery end-to-end:
```bash
docker compose up -d worker
docker compose exec backend python manage.py shell -c "..."   # enqueue real task
docker compose logs -f worker                                 # task executes on redis
```

```bash
docker compose run --rm backend pytest apps/notifications -v
git add -A && git commit -m "feat: notifications with celery, push, email, in-app"
```

**Exit criteria:** every trigger produces exactly one notification; retries recover; no dupes; worker container executes tasks via redis.

---

## Phase 8 — Web Admin Panel (M09)

**Files:**
- Create: `apps/adminpanel/` custom admin views (dashboard, calendar, audit viewer, settings)
- Modify: all app `admin.py` files (ModelAdmin with role-gated permissions)

**Steps:**
1. Django admin registrations: User, Court, Schedule, Booking, Payment, Event, Tournament, News, PriceRule, Policy, AuditLog (read-only).
2. Custom dashboard view: today's bookings, occupancy %, revenue, alerts.
3. Calendar grid (court × time): create booking, block slots, inline edit/cancel.
4. Audit viewer (read-only, filterable).
5. Settings management (schedule, tariffs, policy) restricted to dueño/superadmin.
6. RBAC: recepcionista cannot see financial reports (tested denial).

```bash
docker compose up -d backend
docker compose exec backend python manage.py createsuperuser   # manual smoke via :8000/admin
docker compose run --rm backend pytest apps/adminpanel -v
git add -A && git commit -m "feat: web admin panel with dashboard, calendar, audit"
```

**Exit criteria:** admin CRUD works in the browser against the running backend container; role restrictions enforced; audit visible.

---

## Phase 9 — Reports & Events/Tournaments (M10, M11)

**Files:**
- Create: `apps/reports/views.py`, `services.py`, `urls.py`, `tests.py`
- Create: `apps/events/models.py` (Event, Tournament, TournamentRegistration, NewsPost), `serializers.py`, `views.py`, `urls.py`, `tests.py`

**Steps:**
1. Reports: revenue (by day/week/month/court/method + CSV/PDF export), occupancy %, top customers, cancellation/no-show rates. Role-gated (gerente/dueño).
2. Events: draft→published; feed endpoint; i18n title/description.
3. Tournaments: states draft/open/closed/in_progress/finished; deadline closes registration; capacity enforced.
4. Registration: pending_payment→confirmed; price via payment engine; notifications on publish + reminder.

```bash
docker compose exec backend python manage.py makemigrations events
docker compose exec backend python manage.py migrate
docker compose run --rm backend pytest apps/reports apps/events -v
git add -A && git commit -m "feat: reports, events, tournaments, news"
```

**Exit criteria:** reports correct + exportable; tournament registration capacity-safe.

---

## Phase 10 — i18n + Security Hardening (M16, M12, M13)

**Files:**
- Create: `locale/es/LC_MESSAGES/django.po` (+en/pt/ca), `locale/*/django.mo`
- Modify: `padel/settings/base.py` (LOCALE_PATHS, LANGUAGES), all apps (gettext_lazy)
- Create: `apps/security/services.py` (audit log) + tests, `apps/gdpr/` (export, erase) + tests

**Steps:**
1. Wrap all user-facing strings in `gettext_lazy()`; run translation commands **inside the container**:
```bash
docker compose exec backend python manage.py makemessages -l es -l en -l pt -l ca
# translate .po files, then:
docker compose exec backend python manage.py compilemessages
```
2. `LocaleMiddleware` + Accept-Language honored; DRF errors localized.
3. Audit log model + writes on auth/booking/payment/price/role/settings actions; append-only (no update/delete API).
4. GDPR: consent record, `POST /me/export/`, `POST /me/erase/` (anonymize per §6.4).
5. Security tests: input validation, rate limit 429s, token revocation, secrets boot check (missing secret → fail).
6. Static checks in container:
```bash
docker compose run --rm backend sh -c "ruff check . && flake8 && bandit -r apps"
```

```bash
docker compose run --rm backend pytest apps/security apps/gdpr apps/users -v
docker compose run --rm backend sh -c "ruff check . && flake8 && bandit -r apps"
git add -A && git commit -m "feat: i18n catalogs, audit log, GDPR, security hardening"
```

**Exit criteria:** no hardcoded strings; catalogs ≥98%; audit append-only; secrets check fails fast; static scans clean in container.

---

## Phase 11 — Flutter Setup & Auth App (M15, M01) — in the `flutter` container

> Everything Flutter runs via `docker compose run --rm flutter ...` using the `ghcr.io/cirruslabs/flutter` image (Flutter + Android SDK preinstalled). No Flutter SDK on the host.

**Files:**
- Create: `mobile/` — generate inside the container:
```bash
docker compose run --rm flutter flutter create --org com.andes.padel --platforms android,ios mobile
```
- Create: `mobile/lib/` — `main.dart`, `app.dart`, `core/api_client.dart`, `core/storage.dart`, `core/l10n/` (ARB), `features/auth/` (login, register, verify, reset), `features/home/`, `features/bookings/`, `features/events/`, `features/profile/`
- Create: `mobile/test/` widget tests per screen

**Steps:**
1. Add deps (`pubspec.yaml`): `dio`, `provider`, `flutter_secure_storage`, `flutter_localizations`, `intl`, `stripe_payment`.
2. API client (base URL from build config, JWT header refresh logic).
3. Auth screens (login/register/verify/reset) wired to API; tokens in secure storage.
4. App shell: 5 bottom tabs (Home, Bookings, Events, Notifications, Profile) + onboarding for guests.
5. i18n via ARB (`es` default + en/pt/ca); runtime language switch.

```bash
docker compose run --rm flutter sh -c "cd mobile && flutter pub get"
docker compose run --rm flutter sh -c "cd mobile && flutter analyze"      # 0 issues
docker compose run --rm flutter sh -c "cd mobile && flutter test"          # widget tests pass
git add -A && git commit -m "feat: flutter app shell, auth, i18n"
```

**Exit criteria:** `flutter analyze` and `flutter test` pass in the container; login/register flow works against the running `backend` container; tokens secured.

---

## Phase 12 — Flutter Booking Flow (M04/M05/M06/M07)

**Files:**
- Modify: `mobile/lib/features/courts/` (list/detail), `features/booking/` (wizard: date→time→summary→pay), `features/payments/`, `features/mybookings/`
- Create: `mobile/test/` booking widget tests

**Steps:**
1. Court list/detail from `/courts/` + availability picker.
2. Booking wizard (4 steps) with draft restore; price preview via `/bookings/preview/`.
3. Stripe PaymentSheet (card/Apple/Google Pay) via `stripe_payment` — test mode.
4. My Bookings (upcoming/past/cancelled) + cancel/reschedule + invoice link.
5. Error states: slot-taken → localized message + re-select; offline banner + cache.

```bash
docker compose run --rm flutter sh -c "cd mobile && flutter analyze && flutter test"
git add -A && git commit -m "feat: flutter booking wizard, payments, my bookings"
```

**Exit criteria:** full booking journey E2E in test mode; graceful error handling.

---

## Phase 13 — Flutter Events + Notifications (M08/M11)

**Files:**
- Modify: `mobile/lib/features/events/` (feed, tournament detail, register), `features/notifications/`, `core/push/` (FCM)
- Create: `mobile/test/` widget tests

**Steps:**
1. Events feed (events/tournaments/news) + filters + register CTA.
2. Tournament registration flow (pair partner field, payment if priced).
3. In-app notification center; FCM registration + token refresh; deep links.
4. Push permission + preference toggles in settings.

```bash
docker compose run --rm flutter sh -c "cd mobile && flutter analyze && flutter test"
git add -A && git commit -m "feat: flutter events, tournaments, notifications"
```

**Exit criteria:** events end-to-end; push deep-links to correct screen.

---

## Phase 14 — Release Readiness (all in Docker)

**Files:**
- Create: `Dockerfile.prod`, `compose.prod.yml`, `gunicorn.conf.py`, `nginx/` config, `docs/release/playstore-check.md`, `docs/release/appstore-check.md`, `docs/release/uat-checklist.md`, `docs/plans/deployment-plan.md`
- Create: `apps/common/management/commands/seed_demo.py` (demo data)

**Steps:**
1. Prod build: `docker compose -f compose.prod.yml up -d` → backend (gunicorn), worker, nginx (TLS, HSTS, secure headers), db, redis.
2. Migrate on the prod db container: `docker compose -f compose.prod.yml exec backend python manage.py migrate`.
3. Backups: pg_dump cron (in-container) + WAL archiving; restore drill (RTO ≤ 4h).
4. Load test (locust) against the prod backend container: 50 concurrent / 300 req-min, p95 ≤ 300ms reads / 600ms writes.
5. Security: secret scan, pen-test checklist, OWASP API walkthrough.
6. UAT: run `08-verification-matrix` checklist against staging; fix blockers.
7. Store prep: Play Store (AAB via `flutter build appbundle` in the flutter container), App Store (screenshots, privacy policy, GDPR text); signing keys in `docker/backend/secrets.py`/keystore (git-ignored).
8. **Client handoff:** demo + acceptance sign-off (00 §0.2).

```bash
docker compose -f compose.prod.yml up -d --build
docker compose run --rm backend pytest
docker compose run --rm flutter sh -c "cd mobile && flutter test"
git add -A && git commit -m "chore: release readiness"
```

**Exit criteria:** full verification matrix green; deployment plan documented; stores prepped; everything runs from Docker images only.

---

## Definition of Done (every phase)
- All phase tests pass **inside Docker**; coverage ≥80% (M04/M06/M07 ≥90%).
- `ruff check . && flake8 && bandit -r apps` clean in container; `flutter analyze` 0 issues in container.
- No hardcoded user-facing strings; catalogs present.
- Commit per task with descriptive message.
- SRS traceability: features delivered mapped in `07`.

## Out of scope (v2) — do NOT build
Loyalty (M12), Class Booking (M17), social login, promotions/coupons, webhooks, offline sync, venue map, Google Calendar/WhatsApp/locks/cameras integrations, tournament brackets.
