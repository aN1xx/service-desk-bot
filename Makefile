.PHONY: up down build logs migrate migration seed admin-logs nginx-logs test test-cov

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f bot

admin-logs:
	docker compose logs -f admin

migrate:
	docker compose exec bot alembic upgrade head

migration:
	docker compose exec bot alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose exec bot python -m scripts.seed_data

nginx-logs:
	docker compose logs -f nginx

psql:
	docker compose exec postgres psql -U qss_bot -d qss_service

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=bot --cov-report=term-missing
