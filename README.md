# Andes Padel

Booking platform for a padel club in Guayaquil, Ecuador. Currency USD, timezone `America/Guayaquil`, default language Spanish.

Three surfaces, one repo:

| Surface | Stack | Where |
|---|---|---|
| API + admin panel | Django 5.2 + DRF + SimpleJWT + Celery | `apps/`, `padel/` |
| Mobile app | Flutter | `mobile/` |
| Marketing site | Static HTML | `landing/` |

Postgres + Redis behind nginx. Docker Compose driven.

## Environments and ports

There is **no port 8000 on the host**. Django listens on 8000 *inside* the container; host ports are remapped.

| Env | Compose project | Host ports | Settings | Compose files |
|---|---|---|---|---|
| dev | `andespadel` | 28000–28003 | `padel.settings.dev` | `docker-compose.yml` + `docker-compose.dev.yml` |
| test | `andespadel-test` | 29000–29003 | `padel.settings.dev` | `docker-compose.yml` + `docker-compose.test.yml` |
| prod | `andespadel-prod` | 34000–34003 | `padel.settings.prod` | `docker-compose.yml` + `docker-compose.prod.yml` |

Within each env: `N000` Postgres, `N001` Redis, `N002` backend/API, `N003` nginx.

`docker-compose.yml` must never run alone. Always pass `-p <project> -f docker-compose.yml -f docker-compose.<env>.yml`. `compose.prod.yml` and `compose.server.yml` at the repo root are legacy and unused by the Makefile.

## Quick start (dev)

```bash
make up-dev          # start the dev stack (ports 28000–28003)
make seeddemo-dev    # demo data; password Andes12345!
make flrun           # Flutter against http://127.0.0.1:28002/api
```

API base URL default in `mobile/lib/core/api_client.dart` is `http://127.0.0.1:28002/api`. Release builds must pass `--dart-define=API_BASE_URL=https://<new-domain>/api`. The old host is retired; the new domain is supplied by the operator and is **not** hard-coded anywhere.

## Tests and lint

| What | Command | Needs |
|---|---|---|
| Django (pytest, `apps/`) | `make test-dev` | dev stack up (Postgres) |
| Flutter | `make fltest-dev` | dev stack up for most tests |
| Playwright E2E | `./tests/e2e/run.sh` | a reachable admin — set `E2E_BASE_URL`, no default is baked in |
| Python lint | `make lint` (in container) or `python3 -m ruff check .` + `python3 -m flake8 apps padel` | — |
| Flutter analyze | `make flcheck` | Flutter at `/usr/local/bin/flutter` |

## Make targets (common)

| Target | Purpose |
|---|---|
| `up-dev` / `down-dev` | Start/stop the dev stack |
| `up-test` / `down-test` | Start/stop the test stack |
| `up-prod` / `down-prod` | Start/stop the prod stack |
| `test-dev` / `test-test` | Django pytest inside the matching stack |
| `fltest-dev` | `flutter test` against the dev API |
| `seeddemo-dev` / `seeddemo-test` | Demo data (dev/test only — never prod) |
| `ios-sim-dev` | Flutter run on iOS simulator against the dev API |
| `ship-ios` | Build release IPA and upload to TestFlight |
| `flrun` | `flutter run` against the dev API |
| `flbuild` / `flapk` | Debug APK (and copy to `./padelapp-debug.apk`) |
| `lint` / `flcheck` | Python / Flutter lint |
| `logs` / `shell` / `bash` / `psql` | Ops helpers (dev project) |

There is no `make seed-test`. The target is `seeddemo-test`.

## Document map

Trust levels as of 2026-09-29:

| Document | Trust | Notes |
|---|---|---|
| `AGENTS.md` | current | Operating brief. Read first. |
| `docs/DEPLOYMENTS.md` | current | Env/port/runbook reference |
| `store/README.md` | current | Store packaging and signing |
| `README.md` | current | This index |
| `TESTING_GUIDE.md` | current | Suites, endpoints, how to test |
| `docs/BUILD_AND_DEPLOY.md` | current | Build, compose, mobile, TestFlight |
| `mobile/README.md` | current | Flutter app notes |
| `docs/DEPLOYMENT_PLAN.md` | historical | One-shot plan. Not a runbook. |
| `docs/plans/` | historical | Development plan archive |
| `docs/srs/` | historical | Requirements baseline, partially superseded |

When a port, make target, URL, or API route changes, update `docs/DEPLOYMENTS.md` and `AGENTS.md` in the same commit.
