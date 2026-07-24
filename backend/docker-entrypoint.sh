#!/bin/sh
set -e

echo "[backend] Running database migrations..."
alembic upgrade head

exec "$@"
