#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SERVERS=(
  "servers/server-01-oltp"
  "servers/server-02-kafka"
  "servers/server-03-kafka-connect"
  "servers/server-04-spark"
  "servers/server-05-storage"
  "servers/server-06-quality"
  "servers/server-07-catalog"
  "servers/server-08-ml"
)

echo "Starting Northwind Data Platform..."
for s in "${SERVERS[@]}"; do
  COMPOSE_FILE="$ROOT_DIR/$s/docker-compose.yml"
  if [[ -f "$COMPOSE_FILE" ]]; then
    echo "-> $s"
    docker compose --env-file "$ROOT_DIR/.env" -f "$COMPOSE_FILE" up -d
  else
    echo "!! Missing compose file: $COMPOSE_FILE"
  fi
done

echo "Done."