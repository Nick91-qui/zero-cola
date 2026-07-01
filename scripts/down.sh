#!/usr/bin/env bash
set -euo pipefail

docker-compose down --volumes

echo "Containers stopped and volumes removed."