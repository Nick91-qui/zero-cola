# Makefile with convenient commands for development

.PHONY: up down ps logs migrate test-backend

up:
	@docker-compose up -d --build

down:
	@docker-compose down --volumes

ps:
	@docker ps --filter "name=cola_zero_" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

logs:
	@docker-compose logs -f

migrate:
	@docker-compose run --rm backend alembic upgrade head

migrate-downgrade:
	@docker-compose run --rm backend alembic downgrade -1

test-backend:
	@docker-compose run --rm backend pytest -q
