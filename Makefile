# Makefile with convenient commands for development

.PHONY: up down ps logs migrate test-backend

COMPOSE_CMD := $(shell (command -v podman >/dev/null 2>&1 && echo "podman compose") || (command -v docker-compose >/dev/null 2>&1 && echo "docker-compose") || (command -v docker >/dev/null 2>&1 && echo "docker compose"))

up:
	@$(COMPOSE_CMD) up -d --build

down:
	@$(COMPOSE_CMD) down --volumes

ps:
	@$(COMPOSE_CMD) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

logs:
	@$(COMPOSE_CMD) logs -f

migrate:
	@$(COMPOSE_CMD) run --rm backend alembic upgrade head

migrate-downgrade:
	@$(COMPOSE_CMD) run --rm backend alembic downgrade -1

test-backend:
	@$(COMPOSE_CMD) run --rm backend pytest -q
