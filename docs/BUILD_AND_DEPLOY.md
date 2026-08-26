# Build & Deploy — Andes Pádel

**Last updated:** 2026-08-26  
**Covers:** 3 deployment modes + Android APK + iOS build

---

## Deployment Modes Overview

| Mode | Compose file | Settings | Use case |
|------|-------------|----------|----------|
| **A. Local Development** | `docker-compose.yml` | `padel.settings.dev` | Daily dev on your machine |
| **B. Testing Server** | `compose.server.yml` | `padel.settings.prod` | LOYALLIA server (140.82.155.48) |
| **C. Production (basic)** | `compose.prod.yml` | `padel.settings.prod` | Minimal production without landing page |

---

## MODE A: Local Development

Everything runs on your machine via Docker. No external server needed.

### A1. Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Docker Desktop | Latest | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| Git | Any | `git --version` |

### A2. Start all services

```bash
cd padelApp

# Build images (first time or after Dockerfile changes)
make build

# Start all services (db, redis, backend, worker, flutter)
make up
```

This starts:

| Service | Container | Port | What it does |
|---------|-----------|------|--------------|
| `db` | PostgreSQL 15 | 5432 | Database |
| `redis` | Redis 7 | 6379 | Cache + Celery broker |
| `backend` | Django dev server | 8000 | API + Admin panel |
| `worker` | Celery worker | — | Background tasks |
| `flutter` | Flutter SDK | — | For building mobile app |

### A3. Setup database

```bash
# Run migrations
make migrate

# Load demo data (optional)
make seeddemo
```

### A4. Verify it's running

```bash
# Check all containers are up
docker compose ps

# Test the API
curl http://localhost:8000/api/auth/me/

# Check logs
make logs
```

### A5. Access points

| URL | What |
|-----|------|
| `http://localhost:8000/api/` | REST API |
| `http://localhost:8000/adminpanel/` | Admin dashboard |
| `http://localhost:8000/admin/` | Django admin |
| `http://localhost:8000/api/docs/` | Swagger API docs |

### A6. Secrets (dev)

Secrets are pre-configured for local dev. File: `docker/backend/secrets.py`

```
DB_NAME=padel
DB_USER=padel
DB_PASSWORD=padel_dev
DB_HOST=db
REDIS_URL=redis://redis:6379/0
```

This file is git-ignored. It's volume-mounted into the container at `/app/runsecrets/secrets.py`.

### A7. Useful commands

| Command | Purpose |
|---------|---------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Follow logs |
| `make build` | Rebuild Docker images |
| `make migrate` | Run database migrations |
| `make makemigrations` | Create new migrations |
| `make seeddemo` | Load demo data |
| `make seed` | Seed courts only |
| `make shell` | Django management shell |
| `make bash` | Bash into backend container |
| `make psql` | PostgreSQL shell |
| `make test` | Run backend tests (pytest) |
| `make lint` | Lint backend code (ruff + flake8 + bandit) |

---

## MODE B: Testing Server (LOYALLIA)

Full production deployment on the LOYALLIA server (140.82.155.48).

### B1. Server constraints

- **DO NOT** touch Loyallia containers/networks/configs
- **DO NOT** use ports 33900-33914 (Loyallia range)
- **DO NOT** use ports 80/443 on Docker (host nginx owns these)
- Nginx reload only (no restart)

### B2. Server architecture

```
┌──────────────── Host (140.82.155.48) ────────────────┐
│                                                       │
│  Host nginx (ports 80/443)                            │
│    └─ andespadel.yachaq.io:443 → 127.0.0.1:34003    │
│                                                       │
│  Docker: padelapp-net (isolated bridge)               │
│  ┌──────────────────────────────────────────────┐     │
│  │ db:34000      (PostgreSQL 15)                │     │
│  │ redis:34001   (Redis 7)                      │     │
│  │ backend:34002 (Django/Gunicorn)              │     │
│  │ worker         (Celery worker)                │     │
│  │ beat           (Celery beat)                  │     │
│  │ nginx:34003   (Reverse proxy)                │     │
│  └──────────────────────────────────────────────┘     │
│                                                       │
│  Loyallia containers (UNTOUCHED)                      │
│    loyallia-postgres, loyallia-redis, etc.            │
│    on loyallia_backend-net, ports 33900-33914         │
└───────────────────────────────────────────────────────┘
```

### B3. Port mapping

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| PostgreSQL | 34000 | 5432 |
| Redis | 34001 | 6379 |
| Backend | 34002 | 8000 |
| Nginx | 34003 | 80 |

### B4. Deploy step by step

```bash
# 1. SSH into the server
ssh root@140.82.155.48

# 2. Clone or pull the repo
cd /root
git clone https://github.com/somatechlat/padelApp.git
cd padelApp

# 3. Configure secrets for production
cp docker/backend/secrets.example.py docker/backend/secrets.py
# Edit docker/backend/secrets.py with real production values:
#   SECRET_KEY, DB_NAME=padel_prod, DB_USER, DB_PASSWORD, DB_HOST=db
#   REDIS_URL, EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
#   STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET
#   FIREBASE_CREDENTIALS_PATH

# 4. Deploy with compose.server.yml
docker compose -f compose.server.yml up -d --build

# 5. Run migrations
docker compose -f compose.server.yml exec backend python manage.py migrate

# 6. Create superuser
docker compose -f compose.server.yml exec backend python manage.py createsuperuser

# 7. Load demo data (optional)
docker compose -f compose.server.yml exec backend python manage.py seed_demo

# 8. Collect static files
docker compose -f compose.server.yml exec backend python manage.py collectstatic --no-input

# 9. Verify
docker compose -f compose.server.yml ps
curl https://andespadel.yachaq.io/api/auth/me/
```

### B5. What runs in production

| Service | Command | Purpose |
|---------|---------|---------|
| `backend` | `gunicorn padel.wsgi:application --bind 0.0.0.0:8000 --workers 3` | WSGI server |
| `worker` | `celery -A padel worker -l info` | Background tasks |
| `beat` | `celery -A padel beat -l info` | Scheduled tasks (reminders, hold release) |
| `nginx` | Reverse proxy | Routes traffic, serves landing page + static files |

### B6. Celery beat schedule

| Task | Interval | What it does |
|------|----------|-------------|
| `tournament-reminder-daily` | 24 hours | Send tournament reminders |
| `booking-reminder-daily` | 24 hours | Send booking reminders |
| `booking-reminder-2h` | 30 min | Send 2-hour-before reminders |
| `release-expired-holds` | 5 min | Release expired time slot holds |

### B7. SSL / HTTPS

SSL is handled by the **host nginx** (not Docker). The host nginx:

1. Terminates SSL on port 443
2. Proxies to `127.0.0.1:34003` (Docker nginx)
3. Docker nginx proxies to `backend:8000`

Django sees `X-Forwarded-Proto: https` header → `SECURE_PROXY_SSL_HEADER` in `prod.py`.

### B8. Nginx routing

| Path | Proxied to | What |
|------|-----------|------|
| `/` | Landing page | Static HTML from `./landing/` |
| `/api/` | `backend:8000` | Django REST API |
| `/adminpanel/` | `backend:8000` | Admin dashboard |
| `/admin/` | `backend:8000` | Django admin |
| `/webhooks/` | `backend:8000` | Stripe webhooks |
| `/static/` | Served directly | Cached 30 days |
| `/media/` | Served directly | Cached 7 days |

### B9. Production secrets

File: `docker/backend/secrets.py` (on the server)

```python
import secrets as _std

SECRET_KEY = "your-real-secret-key"
DB_NAME = "padel_prod"
DB_USER = "padel"
DB_PASSWORD = "your-strong-password"
DB_HOST = "db"
DB_PORT = 5432
REDIS_URL = "redis://redis:6379/0"

EMAIL_HOST = "smtp.your-provider.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "your-email"
EMAIL_HOST_PASSWORD = "your-password"

STRIPE_SECRET_KEY = "sk_live_..."
STRIPE_PUBLISHABLE_KEY = "pk_live_..."
STRIPE_WEBHOOK_SECRET = "whsec_..."

FIREBASE_CREDENTIALS_PATH = "/app/runsecrets/firebase-service-account.json"
```

The `prod.py` settings validate these at startup — the app will crash if any are missing or contain dev placeholders.

### B10. Updating the server

```bash
# 1. Pull latest code
git pull origin main

# 2. Rebuild and restart
docker compose -f compose.server.yml up -d --build

# 3. Run migrations (if any new ones)
docker compose -f compose.server.yml exec backend python manage.py migrate

# 4. Collect static files (if any new ones)
docker compose -f compose.server.yml exec backend python manage.py collectstatic --no-input

# 5. Verify
docker compose -f compose.server.yml ps
```

---

## MODE C: Production (Basic — No Landing Page)

Minimal production setup without landing page or Celery beat.

### C1. Deploy

```bash
# 1. Configure secrets
cp docker/backend/secrets.example.py docker/backend/secrets.py
# Edit with production values (same as B9 above)

# 2. Deploy
docker compose -f compose.prod.yml up -d --build

# 3. Setup database
docker compose -f compose.prod.yml exec backend python manage.py migrate
docker compose -f compose.prod.yml exec backend python manage.py createsuperuser
docker compose -f compose.prod.yml exec backend python manage.py collectstatic --no-input
```

### C2. Differences from Mode B

| Feature | Mode B (server) | Mode C (basic) |
|---------|----------------|-----------------|
| Celery beat | Yes | No |
| Landing page | Yes (nginx serves `./landing/`) | No |
| Healthchecks | Yes | No |
| Dedicated network | `padelapp-net` | Default |
| DB name | `padel_prod` | `padel` |
| DB password | Env var `${DB_PASSWORD}` | Hardcoded `padel_dev` |
| Nginx port | `34003:80` | `80:80` |

---

## Android APK

### Prerequisites

| Mode | Requirements |
|------|-------------|
| Docker (recommended) | Docker Desktop, Docker Compose, Git |
| Local (no Docker) | Flutter 3.27.3, Java 21 (OpenJDK), Android SDK |

### API URL configuration

**File:** `mobile/lib/core/api_client.dart` (line 17)

```dart
_dio.options.baseUrl = baseUrl ??
    const String.fromEnvironment('API_BASE_URL',
        defaultValue: 'https://andespadel.yachaq.io/api');
```

Override at build time without changing code:

```bash
--dart-define=API_BASE_URL=https://your-server.com/api
```

### Build with Docker

```bash
cd padelApp

# Quick build (builds APK + copies to project root)
make flapk

# Output: ./padelapp-debug.apk
```

### Build without Docker

```bash
cd padelApp/mobile

# 1. Get dependencies
flutter pub get

# 2. Analyze (optional)
flutter analyze

# 3. Test (optional)
flutter test

# 4. Build debug APK
flutter build apk --debug

# 5. Build release APK
flutter build apk --release
```

| Build type | Output |
|------------|--------|
| Debug | `mobile/build/app/outputs/flutter-apk/app-debug.apk` |
| Release | `mobile/build/app/outputs/flutter-apk/app-release.apk` |

### Install on phone

**Option 1: ADB (USB)**
```bash
adb install ./padelapp-debug.apk
```

**Option 2: ADB (Wireless)**
```bash
adb connect <phone-ip>:5555
adb install ./padelapp-debug.apk
```

**Option 3: Manual**
1. Copy `padelapp-debug.apk` to phone (USB, email, cloud)
2. On phone: Open file manager → tap APK → Install
3. Enable "Install from unknown sources" if prompted

---

## iOS Build

> **Requires:** macOS + Xcode + CocoaPods + Apple Developer account (for signed builds)

### Setup

```bash
# Verify Xcode
xcodebuild -version

# Install CocoaPods (if not installed)
sudo gem install cocoapods

# Point xcode-select to Xcode (not CommandLineTools)
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer

# Verify Flutter sees Xcode
flutter doctor
```

### Build (debug — no signing)

```bash
cd padelApp/mobile

flutter pub get

cd ios && pod install && cd ..

flutter build ios --debug --no-codesign
```

### Build (release — requires signing)

```bash
flutter build ios --release
```

### Export IPA for client delivery

**Option A: Xcode**

1. Open `mobile/ios/Runner.xcworkspace` in Xcode
2. Runner target → Signing & Capabilities → set Team + Bundle ID (`com.andes.padel.padel_app`)
3. Product → Archive → Distribute App → Ad Hoc or Development

**Option B: Command line**

```bash
flutter build ipa --release
# Output: mobile/build/ios/ipa/
```

### Install on iPhone

| Method | Requirements |
|--------|-------------|
| Xcode | USB cable, Apple Developer account |
| TestFlight | Apple Developer account, upload to App Store Connect |
| `ios-deploy` | `npm install -g ios-deploy`, USB cable |

### iOS signing checklist

- [ ] Apple Developer account active
- [ ] Bundle ID registered: `com.andes.padel.padel_app`
- [ ] Provisioning profile created
- [ ] Xcode project signed with correct team
- [ ] `ios/Podfile` generated and `pod install` run

---

## Django Settings Chain

```
padel/settings/base.py     → shared config, imports runsecrets/secrets.py
padel/settings/dev.py      → DEBUG=True, ALLOWED_HOSTS=["*"], CORS open, Celery eager
padel/settings/prod.py     → DEBUG=False, ALLOWED_HOSTS=[andespadel.yachaq.io], SSL, SMTP
padel/settings/_checks.py  → validates production secrets at startup
```

| Setting | dev.py | prod.py |
|---------|--------|---------|
| `DEBUG` | `True` | `False` |
| `ALLOWED_HOSTS` | `["*"]` | `["andespadel.yachaq.io", ...]` |
| `CORS_ALLOW_ALL_ORIGINS` | `True` | `False` (whitelist) |
| `CELERY_TASK_ALWAYS_EAGER` | `True` | Not set (real broker) |
| `EMAIL_BACKEND` | Console | SMTP |
| `SECURE_SSL_REDIRECT` | No | Yes |
| `SECRET_KEY validation` | No | Yes (rejects dev placeholders) |

---

## Troubleshooting

### Gradle zip corruption (Docker)

**Symptom:** `java.util.zip.ZipException: zip END header not found`

```bash
docker volume rm padelapp_gradle_home
make flapk
```

### "Matrix4 isn't a type" (Docker)

**Symptom:** Hundreds of Flutter SDK internal compile errors

**Cause:** Corrupted Flutter SDK cache in Docker volumes

```bash
docker volume rm padelapp_flutter_home padelapp_gradle_home padelapp_android_sdk
make flapk
```

### APK won't install

- Enable "Install from unknown sources" in Android settings
- Check Android version (min SDK 24)
- Clear old install: `adb shell pm clear com.andes.padel.padel_app`

### Can't connect to backend

- **Local:** Check `docker compose ps`, test `curl http://localhost:8000/api/auth/me/`
- **Server:** Test `curl https://andespadel.yachaq.io/api/auth/me/`
- Expected response: `{"detail":"Las credenciales de autenticación no se proveyeron."}`

### iOS "pod install" fails

```bash
cd ios
pod deintegrate
pod install --verbose
```

### iOS Xcode signing errors

1. Open `Runner.xcworkspace` in Xcode
2. Runner target → Signing & Capabilities → select Team
3. No team? Xcode → Settings → Accounts → add Apple Developer account

### Production app crashes on startup

- Check secrets are not dev placeholders (validated by `prod.py`)
- Check Firebase credentials file exists at the configured path
- Check database is accessible from the container

---

## Quick Reference

### Build commands

| Target | Command |
|--------|---------|
| Android APK (Docker) | `make flapk` |
| Android APK (local) | `cd mobile && flutter build apk --debug` |
| Android APK (custom URL) | `flutter build apk --debug --dart-define=API_BASE_URL=https://...` |
| iOS debug | `cd mobile && flutter build ios --debug --no-codesign` |
| iOS release | `cd mobile && flutter build ios --release` |
| iOS IPA | `cd mobile && flutter build ipa --release` |
| Flutter analyze | `make flcheck` or `flutter analyze` |
| Flutter tests | `make fltest` or `flutter test` |

### Install commands

| Target | Command |
|--------|---------|
| Android (ADB) | `adb install ./padelapp-debug.apk` |
| Android (wireless) | `adb connect <ip>:5555 && adb install ./padelapp-debug.apk` |
| iOS (Xcode) | Open `.xcworkspace` → Run on device |
| iOS (TestFlight) | Upload IPA to App Store Connect → invite testers |

### Local dev commands (Makefile)

| Command | Purpose |
|---------|---------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Follow logs |
| `make build` | Rebuild Docker images |
| `make migrate` | Run database migrations |
| `make seeddemo` | Load demo data |
| `make shell` | Django management shell |
| `make psql` | PostgreSQL shell |
| `make test` | Run backend tests |
| `make lint` | Lint backend code |

### Server commands (compose.server.yml)

| Command | Purpose |
|---------|---------|
| `docker compose -f compose.server.yml up -d --build` | Deploy |
| `docker compose -f compose.server.yml ps` | Check status |
| `docker compose -f compose.server.yml logs -f` | Follow logs |
| `docker compose -f compose.server.yml exec backend python manage.py migrate` | Migrate |
| `docker compose -f compose.server.yml exec backend python manage.py createsuperuser` | Create admin |

---

**Last APK built:** `./padelapp-debug.apk` (86 MB, 2026-08-26)  
**Production server:** https://andespadel.yachaq.io
