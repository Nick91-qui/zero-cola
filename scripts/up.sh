#!/usr/bin/env bash
set -euo pipefail

# Start containers
docker-compose up -d --build

echo "Containers started. Use 'docker-compose ps' to see status." 
