#!/bin/sh
set -e

CONNECT_URL="${CONNECT_URL:-http://northwind-connect:8083}"
CONNECTOR_NAME="${CONNECTOR_NAME:-northwind-connector}"
if [ -z "$POSTGRES_PASSWORD" ]; then
  echo "ERROR: POSTGRES_PASSWORD is not set (use .env with docker compose --env-file)." >&2
  exit 1
fi
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ] || [ -z "$DATABASE_SERVER_NAME" ]; then
  echo "ERROR: POSTGRES_USER, POSTGRES_DB, DATABASE_SERVER_NAME must be set (e.g. in .env)." >&2
  exit 1
fi
POSTGRES_HOST="${POSTGRES_HOST:-northwind-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
MAX_WAIT_SEC="${MAX_WAIT_SEC:-120}"

echo "Waiting for Kafka Connect at ${CONNECT_URL} (up to ${MAX_WAIT_SEC}s)..."
i=0
while [ "$i" -lt "$MAX_WAIT_SEC" ]; do
  if curl -sf "${CONNECT_URL}/" >/dev/null 2>&1; then
    echo "Kafka Connect is ready."
    break
  fi
  i=$((i + 2))
  sleep 2
done
if ! curl -sf "${CONNECT_URL}/" >/dev/null 2>&1; then
  echo "ERROR: Kafka Connect did not become ready in time." >&2
  exit 1
fi

# GET /status may return 404 briefly after create; poll until 200 or timeout.
poll_connector_status() {
  j=0
  _wait="${STATUS_WAIT_SEC:-90}"
  _code=""
  while [ "$j" -lt "$_wait" ]; do
    _code=$(curl -s -o /tmp/debezium_status_body -w "%{http_code}" \
      "${CONNECT_URL}/connectors/${CONNECTOR_NAME}/status")
    if [ "$_code" = "200" ]; then
      echo "Connector status:"
      cat /tmp/debezium_status_body
      echo ""
      return 0
    fi
    j=$((j + 2))
    sleep 2
  done
  echo "WARNING: /connectors/${CONNECTOR_NAME}/status not ready after ${_wait}s (last HTTP ${_code})." >&2
  return 1
}

code=$(curl -s -o /dev/null -w "%{http_code}" "${CONNECT_URL}/connectors/${CONNECTOR_NAME}")
if [ "$code" = "200" ]; then
  echo "Connector '${CONNECTOR_NAME}' already exists; skipping create."
  poll_connector_status || true
  exit 0
fi

echo "Creating connector '${CONNECTOR_NAME}'..."
payload=$(printf '%s' "{
  \"name\": \"${CONNECTOR_NAME}\",
  \"config\": {
    \"connector.class\": \"io.debezium.connector.postgresql.PostgresConnector\",
    \"database.hostname\": \"${POSTGRES_HOST}\",
    \"database.port\": \"${POSTGRES_PORT}\",
    \"database.user\": \"${POSTGRES_USER}\",
    \"database.password\": \"${POSTGRES_PASSWORD}\",
    \"database.dbname\": \"${POSTGRES_DB}\",
    \"database.server.name\": \"${DATABASE_SERVER_NAME}\",
    \"topic.prefix\": \"${DATABASE_SERVER_NAME}\",
    \"plugin.name\": \"pgoutput\",
    \"table.include.list\": \"public.orders,public.customers,public.order_details,public.products\",
    \"snapshot.mode\": \"initial\"
  }
}")

http_code=$(curl -s -o /tmp/debezium_post_body -w "%{http_code}" -X POST \
  "${CONNECT_URL}/connectors" \
  -H "Content-Type: application/json" \
  -d "$payload")
http_body=$(cat /tmp/debezium_post_body 2>/dev/null || true)

if [ "$http_code" != "201" ] && [ "$http_code" != "200" ]; then
  echo "ERROR: POST /connectors failed HTTP ${http_code}: ${http_body}" >&2
  exit 1
fi

echo "Connector registered (HTTP ${http_code})."
poll_connector_status || true
echo "Done."
