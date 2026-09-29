# Andes Padel — Deployment Environments

Three isolated deployments. Never mix ports, secrets, or data between them.

| Env | Compose project | Host ports | Settings | Data | Purpose |
|-----|-----------------|------------|----------|------|---------|
| **dev** | `andespadel` | **28000–28003** | `padel.settings.dev` | local Docker volume `andespadel_db_data` | Local development |
| **test** | `andespadel-test` | **29000–29003** | `padel.settings.dev` | volume `andespadel-test_db_data` | QA / UAT / staging |
| **prod** | `andespadel-prod` | **34000–34003** (server) | `padel.settings.prod` | volume `andespadel-prod_db_data` | Live `andespadel.yachaq.io` |

Port map (same offsets in every env):

| Offset | Service | dev | test | prod (server 140.82.15.48) |
|--------|---------|-----|------|------------------------------|
| +0 | PostgreSQL | 28000 | 29000 | 34000 |
| +1 | Redis | 28001 | 29001 | 34001 |
| +2 | Django backend | 28002 | 29002 | 34002 |
| +3 | Nginx (API + landing) | 28003 | 29003 | 34003 |

**Hard rules**
- Ports **33900–33914** belong to Loyallia — never use them.
- One Docker network per env: `andespadel-net` / `andespadel-test-net` / `andespadel-prod-net`.
- Secrets never in git. Per-env secrets live in `docker/backend/secrets.py` (dev/test) or `/opt/padelapp/docker/backend/secrets.py` (prod, server only).
- Images run as non-root user (`app` in `Dockerfile.dev`, `appuser` in `Dockerfile.prod`) with packages in `/opt/venv` — never `pip install` as root at runtime.
- iOS/Android apps are **not** containers. They are Flutter builds that talk to the env API URL.

---

## Files

```
docker-compose.yml          # shared service definitions (base)
docker-compose.dev.yml      # dev overlay: ports 28000+, project andespadel
docker-compose.test.yml     # test overlay: ports 29000+, project andespadel-test
docker-compose.prod.yml     # prod overlay: ports 34000+, project andespadel-prod
Dockerfile.dev              # non-root Python image (dev/test)
Dockerfile.prod             # non-root gunicorn image (prod)
```

---

## Commands

```bash
# DEV (local, ports 28000+)
make up-dev
make test-dev          # pytest inside andespadel cluster
make fltest-dev        # flutter test → http://127.0.0.1:28002/api

# TEST / UAT (ports 29000+)
make up-test
make seeddemo-test
make test-test

# PROD (server ports 34000+, or local dry-run)
make up-prod
# real prod: on 140.82.15.48 under /opt/padelapp only (R18)
```

Equivalent raw compose (always pass `-f` base + overlay):

```bash
# dev
docker compose -p andespadel \
  -f docker-compose.yml -f docker-compose.dev.yml \
  up -d

# test
docker compose -p andespadel-test \
  -f docker-compose.yml -f docker-compose.test.yml \
  up -d

# prod
docker compose -p andespadel-prod \
  -f docker-compose.yml -f docker-compose.prod.yml \
  up -d
```

---

## Settings & parameters per environment

| Parameter | dev | test | prod |
|-----------|-----|------|------|
| `DJANGO_SETTINGS_MODULE` | `padel.settings.dev` | `padel.settings.dev` | `padel.settings.prod` |
| `DEBUG` | True | True | False (forced by prod) |
| `SECRET_KEY` | `dev-only-…` (allowed) | `dev-only-…` (allowed) | real key (rejects `dev-only-`) |
| DB name | `padel` | `padel_test` | `padel_prod` |
| DB password | `padel_dev` | `padel_test` | strong secret in `secrets.py` |
| Celery eager | True (dev) | False | False |
| Email | console | console | real SMTP in `secrets.py` |
| Stripe | test keys | test keys | live or test keys |
| Allowed hosts | `*` / localhost | test host | `andespadel.yachaq.io` |
| SSL | off | off | terminated by host nginx |
| Public API URL (mobile) | `http://127.0.0.1:28002/api` | `http://<test-host>:29002/api` | `https://andespadel.yachaq.io/api` |

Mobile builds select the API with:

```bash
flutter build apk --debug --dart-define=API_BASE_URL=http://127.0.0.1:28002/api   # dev
flutter build apk --debug --dart-define=API_BASE_URL=http://127.0.0.1:29002/api   # test
flutter build apk --release --dart-define=API_BASE_URL=https://andespadel.yachaq.io/api  # prod
```

---

## Cluster name & isolation

| | dev | test | prod |
|--|-----|------|------|
| Compose project `name` | `andespadel` | `andespadel-test` | `andespadel-prod` |
| Network | `andespadel-net` | `andespadel-test-net` | `andespadel-prod-net` |
| Containers | `andespadel-*` | `andespadel-test-*` | `andespadel-prod-*` |

Same Docker host can run all three at once. They share nothing.

---

## Architecture reminder

```
Flutter (iOS + Android)  ──HTTP──►  Nginx :+3  ──►  Django backend :+2
                                                    │
                                    Postgres :+0  Redis :+1  Celery worker + beat
```

- Flutter never runs inside Docker (except the optional `flutter` toolchain service under profile `tools`).
- Backend/worker/beat/db/redis/nginx are always one compose project per env.
