#!/bin/sh
set -e

# Keep the named node_modules volume in sync with package-lock.json.
# This prevents stale host/Alpine (musl) binaries from breaking SWC/lightningcss.
LOCK_HASH="$(sha256sum package-lock.json | awk '{print $1}')"
STAMP_FILE="node_modules/.cola-zero-deps-stamp"

if [ ! -x "node_modules/.bin/next" ] || [ ! -f "$STAMP_FILE" ] || [ "$(cat "$STAMP_FILE")" != "$LOCK_HASH" ]; then
  echo "[frontend] Syncing container node_modules with npm ci..."
  npm ci
  mkdir -p node_modules
  echo "$LOCK_HASH" > "$STAMP_FILE"
fi

exec "$@"


