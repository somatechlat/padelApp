SHELL := /bin/bash

.PHONY: up-dev up-test up-prod down-dev down-test down-prod \
	test-dev test-test lint-dev fltest-dev flcheck seeddemo-dev seeddemo-test \
	up down logs build migrate makemigrations test lint flcheck fltest flbuild flrun flapk seed seeddemo shell bash psql ship-ios

# ─── Three environments (see docs/DEPLOYMENTS.md) ───────────────────────────
# dev  → project andespadel      ports 28000+
# test → project andespadel-test ports 29000+
# prod → project andespadel-prod ports 34000+

COMPOSE_DEV  := docker compose -p andespadel      -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_TEST := docker compose -p andespadel-test -f docker-compose.yml -f docker-compose.test.yml
COMPOSE_PROD := docker compose -p andespadel-prod -f docker-compose.yml -f docker-compose.prod.yml

API_DEV  := http://127.0.0.1:28002/api
API_TEST := http://127.0.0.1:29002/api
# Production domain is andespadelclub.com. No server is provisioned yet —
# do not run up-prod anywhere until the operator supplies one.
#   make <target> API_PROD=https://www.andespadelclub.com/api
API_PROD ?=

up-dev:
	$(COMPOSE_DEV) up -d

up-test:
	$(COMPOSE_TEST) up -d

up-prod:
	$(COMPOSE_PROD) up -d

down-dev:
	$(COMPOSE_DEV) down

down-test:
	$(COMPOSE_TEST) down

down-prod:
	$(COMPOSE_PROD) down

test-dev:
	$(COMPOSE_DEV) exec -T backend pytest apps -q

test-test:
	$(COMPOSE_TEST) exec -T backend pytest apps -q

seeddemo-dev:
	$(COMPOSE_DEV) exec -T backend python manage.py seed_demo

seeddemo-test:
	$(COMPOSE_TEST) exec -T backend python manage.py seed_demo

fltest-dev:
	cd mobile && flutter test --no-version-check --suppress-analytics \
		--dart-define=API_BASE_URL=$(API_DEV)

fltest-test:
	cd mobile && flutter test --no-version-check --suppress-analytics \
		--dart-define=API_BASE_URL=$(API_TEST)

# ─── Back-compat aliases (default = dev) ────────────────────────────────────
up: up-dev
down: down-dev
test: test-dev
seeddemo: seeddemo-dev
fltest: fltest-dev

logs:
	$(COMPOSE_DEV) logs -f

build:
	$(COMPOSE_DEV) build backend

migrate:
	$(COMPOSE_DEV) exec backend python manage.py migrate

seed:
	$(COMPOSE_DEV) exec backend python manage.py seed_courts

makemigrations:
	$(COMPOSE_DEV) exec backend python manage.py makemigrations

lint:
	$(COMPOSE_DEV) exec -T backend sh -c "ruff check . && flake8 && bandit -r apps"

flcheck:
	cd mobile && flutter analyze --no-version-check

flbuild:
	cd mobile && flutter build apk --debug --no-version-check \
		--dart-define=API_BASE_URL=$(API_DEV)

flrun:
	cd mobile && flutter run --no-version-check \
		--dart-define=API_BASE_URL=$(API_DEV)

flapk: flbuild
	cp mobile/build/app/outputs/flutter-apk/app-debug.apk ./padelapp-debug.apk
	@echo "APK ready: ./padelapp-debug.apk"

# iOS simulator against DEV API
ios-sim-dev:
	cd mobile && flutter run -d "iPhone 17 Pro" --no-version-check \
		--dart-define=API_BASE_URL=$(API_DEV)

# Build iOS release IPA + upload to TestFlight
# Usage: ASC_USER=... ASC_PASSWORD=... make ship-ios
ship-ios:
	chmod +x mobile/tool/release_ipa.sh
	./mobile/tool/release_ipa.sh

shell:
	$(COMPOSE_DEV) exec backend python manage.py shell

bash:
	$(COMPOSE_DEV) exec backend bash

psql:
	$(COMPOSE_DEV) exec db psql -U padel -d padel
