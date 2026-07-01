#!/usr/bin/env bash
set -euo pipefail

podman compose up -d --build

echo "Containers started. Use './scripts/ps.sh' or podman compose ps to see status."
