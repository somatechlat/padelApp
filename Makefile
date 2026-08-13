SHELL := /bin/bash

.PHONY: up down logs build migrate makemigrations test lint flcheck fltest flbuild shell bash psql

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

shell:
	docker compose exec backend python manage.py shell

bash:
	docker compose exec backend bash

psql:
	docker compose exec db psql -U padel -d padel
