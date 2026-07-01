#!/usr/bin/env bash
set -euo pipefail

docker ps --filter "name=cola_zero_" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
