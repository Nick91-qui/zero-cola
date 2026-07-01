#!/usr/bin/env bash
set -euo pipefail

if command -v podman >/dev/null 2>&1; then
  COMPOSE_CMD=(podman compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
elif command -v docker >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
else
  echo "Please install podman or docker/docker-compose" >&2
  exit 1
fi

"${COMPOSE_CMD[@]}" down --volumes

echo "Containers stopped and volumes removed." 
