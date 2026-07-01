# Makefile with convenient commands for development (podman)

.PHONY: up down ps logs migrate migrate-downgrade test-backend

up:
	@podman compose up -d --build

down:
	@podman compose down --volumes

ps:
	@podman compose ps

logs:
	@podman compose logs -f

migrate:
	@podman compose run --rm backend alembic upgrade head

migrate-downgrade:
	@podman compose run --rm backend alembic downgrade -1

test-backend:
	@podman compose run --rm backend pytest -q
