SHELL := /bin/bash

.PHONY: up down logs build migrate makemigrations test lint flcheck fltest flbuild flrun flapk seed seeddemo shell bash psql

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

migrate:
	docker compose exec backend python manage.py migrate

seed:
	docker compose exec backend python manage.py seed_courts

seeddemo:
	docker compose exec backend python manage.py seed_demo

makemigrations:
	docker compose exec backend python manage.py makemigrations

test:
	docker compose run --rm backend pytest

lint:
	docker compose run --rm backend sh -c "ruff check . && flake8 && bandit -r apps"

flcheck:
	docker compose run --rm flutter flutter analyze

fltest:
	docker compose run --rm flutter flutter test

flbuild:
	docker compose run --rm flutter flutter build apk --debug

# Hot reload: DEVICE=<adb-id> make flrun  (phone must be reachable via adb, e.g. wireless debugging)
flrun:
	docker compose run --rm -i flutter flutter run -d $(DEVICE)

# Build and copy the debug APK to the project root for easy install
flapk: flbuild
	cp mobile/build/app/outputs/flutter-apk/app-debug.apk ./padelapp-debug.apk
	@echo "APK ready: ./padelapp-debug.apk"

shell:
	docker compose exec backend python manage.py shell

bash:
	docker compose exec backend bash

psql:
	docker compose exec db psql -U padel -d padel
