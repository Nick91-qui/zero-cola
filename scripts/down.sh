#!/usr/bin/env bash
set -euo pipefail

podman compose down --volumes

echo "Containers stopped and volumes removed."
