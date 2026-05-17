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
    # Let connect-init finish before bronze (server-04) starts streaming.
    if [[ "$s" == "servers/server-03-kafka-connect" ]]; then
      if docker inspect -f '{{.State.Running}}' northwind-connect-init 2>/dev/null | grep -q true; then
        echo "   waiting for northwind-connect-init..."
        docker wait northwind-connect-init >/dev/null || true
      fi
    fi
  else
    echo "!! Missing compose file: $COMPOSE_FILE"
  fi
done

echo "Done."