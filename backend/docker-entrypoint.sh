#!/bin/sh
set -e

echo "[backend] Running database migrations..."

max_attempts="${DB_MIGRATION_RETRIES:-30}"
attempt=1
while ! alembic upgrade head; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "[backend] Migration failed after ${max_attempts} attempts."
    exit 1
  fi

  echo "[backend] Migration attempt ${attempt} failed; retrying in 2s..."
  attempt=$((attempt + 1))
  sleep 2
done

exec "$@"
