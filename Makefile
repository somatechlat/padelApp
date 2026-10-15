SHELL := /bin/bash

.PHONY: up-dev up-test up-prod up-localprod down-dev down-test down-prod down-localprod \
	test-dev test-test test-localprod lint-dev fltest-dev flcheck seeddemo-dev seeddemo-test \
	seeddemo-localprod secrets-init certs-localprod journey-dev journey-localprod \
	mirror-prod mirror-verify \
	up down logs build migrate makemigrations test lint flcheck fltest flbuild flrun flapk seed seeddemo shell bash psql ship-ios ship-android

# ─── Four environments (see docs/DEPLOYMENTS.md) ───────────────────────────
# dev      → project andespadel          ports 28000+
# test     → project andespadel-test     ports 29000+
# prod     → project andespadel-prod     ports 34000+   (the server)
# localprod→ project andespadel-localprod ports 35000+  (prod-shaped laptop run)

COMPOSE_DEV       := docker compose -p andespadel          -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_TEST      := docker compose -p andespadel-test     -f docker-compose.yml -f docker-compose.test.yml
COMPOSE_PROD      := docker compose -p andespadel-prod     -f docker-compose.yml -f docker-compose.prod.yml
COMPOSE_LOCALPROD := docker compose -p andespadel-localprod -f docker-compose.yml -f docker-compose.localprod.yml

# The suite runs in a throwaway container with a workable memory cap.
COMPOSE_DEV_TEST  := $(COMPOSE_DEV) -f docker-compose.testsuite.yml
COMPOSE_LP_TEST   := $(COMPOSE_LOCALPROD) -f docker-compose.testsuite.yml

API_DEV       := http://127.0.0.1:28002/api
API_TEST      := http://127.0.0.1:29002/api
API_LOCALPROD := https://localhost:35003/api
# Production API. Live host for the app, admin panel and public pages:
# https://app.andespadelclub.com/api — verified answering, Let's Encrypt cert.
# The apex/www of andespadelclub.com is a different machine and does NOT serve
# /api or /privacy; do not substitute it here.
#   make ship-android API_PROD=https://staging.example.com/api
API_PROD ?= https://app.andespadelclub.com/api

SECRETS := docker/runsecrets

# ─── Secrets: one file per value, mounted at /run/secrets ───────────────────
# Real random values, generated once and never overwritten. Nothing is read
# from the environment, so `docker inspect` shows no credentials.
secrets-init:
	@mkdir -p $(SECRETS)
	@test -s $(SECRETS)/secret-key || openssl rand -hex 32 > $(SECRETS)/secret-key
	@test -s $(SECRETS)/db-password || openssl rand -hex 9 > $(SECRETS)/db-password
	@# Stripe is optional in dev/test: empty files mean "payments disabled",
	@# which settings read as "" rather than a fake key.
	@for f in stripe-secret-key stripe-publishable-key stripe-webhook-secret; do \
		test -e $(SECRETS)/$$f || : > $(SECRETS)/$$f; done
	@test -e $(SECRETS)/firebase-service-account.json || : > $(SECRETS)/firebase-service-account.json
	@chmod 600 $(SECRETS)/* 2>/dev/null || true
	@ls -la $(SECRETS) | sed 's/^/  /'

# ─── Stack control ─────────────────────────────────────────────────────────
up-dev: secrets-init
	$(COMPOSE_DEV) up -d

up-test: secrets-init
	$(COMPOSE_TEST) up -d

up-prod:
	$(COMPOSE_PROD) up -d

# localprod needs real test-mode Stripe keys and a self-signed cert for the
# TLS terminator; both are one-time setup steps with their own targets.
up-localprod: secrets-localprod certs-localprod
	$(COMPOSE_LOCALPROD) up -d --build

down-dev:
	$(COMPOSE_DEV) down

down-test:
	$(COMPOSE_TEST) down

down-prod:
	$(COMPOSE_PROD) down

down-localprod:
	$(COMPOSE_LOCALPROD) down

# ─── Tests ─────────────────────────────────────────────────────────────────
# A throwaway container rather than exec into the running one: the suite needs
# more memory than a long-lived backend should hold, and the test database is
# created and dropped per run either way.
test-dev: secrets-init
	$(COMPOSE_DEV_TEST) run --rm --no-deps -T backend pytest apps -q

test-test: secrets-init
	$(COMPOSE_TEST) -f docker-compose.testsuite.yml run --rm --no-deps -T backend pytest apps -q

test-localprod: secrets-localprod certs-localprod
	$(COMPOSE_LP_TEST) run --rm --no-deps -T -e DJANGO_SETTINGS_MODULE=padel.settings.prod_local backend pytest apps -q

# Every customer journey over HTTP, using the API origin Django settings
# themselves point at. The command runs in the *running* backend container,
# not a throwaway one: in dev its origin is gunicorn's loopback, which only
# resolves inside that container.
journey-dev: secrets-init
	$(COMPOSE_DEV) exec -T backend python manage.py journey_check

journey-localprod: secrets-localprod certs-localprod
	$(COMPOSE_LOCALPROD) exec -T backend python manage.py journey_check

seeddemo-dev:
	$(COMPOSE_DEV) exec -T backend python manage.py seed_demo

seeddemo-test:
	$(COMPOSE_TEST) exec -T backend python manage.py seed_demo

seeddemo-localprod: secrets-localprod certs-localprod
	$(COMPOSE_LOCALPROD) run --rm --no-deps -T -e DJANGO_SETTINGS_MODULE=padel.settings.prod_local backend python manage.py seed_demo

# localprod refuses to start on placeholders — it runs on real Stripe TEST
# keys, because the point of the mode is exercising the payment path in
# production shape. Drop them in docker/runsecrets/ once and they are reused.
secrets-localprod: secrets-init
	@for f in stripe-secret-key stripe-publishable-key; do \
		if [ ! -s $(SECRETS)/$$f ]; then \
			echo "✗ $(SECRETS)/$$f is empty. Put a real Stripe TEST key in it"; \
			echo "  (sk_test_…/pk_test_…) — localprod will not start on a placeholder."; \
			exit 1; \
		fi; \
		case "$$(cat $(SECRETS)/$$f)" in \
			sk_live_*|pk_live_*) echo "✗ $(SECRETS)/$$f holds a LIVE key."; exit 1;; \
			*replace_me*) echo "✗ $(SECRETS)/$$f holds the template value."; exit 1;; \
		esac; \
	done
	@chmod 600 $(SECRETS)/* 2>/dev/null || true

# Self-signed certificate for the TLS terminator. SANs cover the name in
# settings (local.andespadel.test) and the loopback forms, so a browser on the
# laptop can reach the stack either way once /etc/hosts has the one-line entry.
certs-localprod:
	@test -s $(SECRETS)/tls/cert.pem -a -s $(SECRETS)/tls/key.pem || ( \
		mkdir -p $(SECRETS)/tls && \
		openssl req -x509 -newkey rsa:2048 -nodes -days 825 \
			-keyout $(SECRETS)/tls/key.pem -out $(SECRETS)/tls/cert.pem \
			-subj "/CN=local.andespadel.test" \
			-addext "subjectAltName=DNS:local.andespadel.test,DNS:localhost,IP:127.0.0.1" \
			2>/dev/null && \
		chmod 600 $(SECRETS)/tls/key.pem && \
		echo "  created $(SECRETS)/tls/{cert,key}.pem (self-signed, 825 days)" )

# ─── Production data → local, verbatim ─────────────────────────────────────
# How to reach production for a mirror. Key-based auth by default so no
# password lives in this file or in an exported variable; override per call:
#   make mirror-prod PROD_SSH="sshpass -p '…' ssh -o PubkeyAuthentication=no root@140.82.15.48"
PROD_SSH ?= ssh root@140.82.15.48

# Dumps the club's content (courts, schedules, venue, pricing, policies,
# banners, events, tournaments, open matches, news, skill levels) from the
# running production container and loads it into the local dev database.
# Customer rows — users, bookings, payments, devices, audit logs — are NOT
# copied; that is personal data and a laptop is not the place for it.
mirror-prod: secrets-init
	@echo "→ dumping club content from production…"
	@$(PROD_SSH) 'docker exec -i andespadel-prod-backend python manage.py dumpdata \
		users.SkillLevel courts.Venue courts.Court courts.CourtSchedule courts.PromoBanner \
		pricing.PriceRule pricing.Holiday policies.CancellationPolicy \
		events.Event events.Tournament events.OpenMatch events.NewsPost \
		--indent 1' > /tmp/andes-prod-content.json
	@echo "  dump: $$(wc -c < /tmp/andes-prod-content.json) bytes"
	@echo "→ loading into local dev database…"
	@$(COMPOSE_DEV) exec -T backend python manage.py mirror_content --file - < /tmp/andes-prod-content.json

# Show local counts next to production's so a mirror can be checked, not
# assumed. Same models in the same order on both sides.
mirror-verify:
	@echo "── production ──"
	@$(PROD_SSH) 'docker exec -i andespadel-prod-backend python manage.py content_counts'
	@echo "── local (dev) ──"
	@$(COMPOSE_DEV) exec -T backend python manage.py content_counts

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
	API_BASE_URL=$(API_PROD) ./mobile/tool/release_ipa.sh

# Build the signed Android App Bundle for Google Play.
# Google Play requires an AAB, not an APK, for every new app.
# Upload itself is still a manual step — there is no Play upload tooling here.
ship-android:
	cd mobile && flutter build appbundle --release \
		--dart-define=API_BASE_URL=$(API_PROD)
	@echo "AAB ready: mobile/build/app/outputs/bundle/release/app-release.aab"

shell:
	$(COMPOSE_DEV) exec backend python manage.py shell

bash:
	$(COMPOSE_DEV) exec backend bash

psql:
	$(COMPOSE_DEV) exec db psql -U padel -d padel
