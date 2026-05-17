#!/bin/sh
# Wait until Debezium has registered the CDC Kafka topic before bronze spark-submit.
# Uses Kafka Connect REST (same network as northwind-connect). See connect-init pattern.

set -e

CONNECT_URL="${CONNECT_URL:-http://northwind-connect:8083}"
CONNECTOR_NAME="${CONNECTOR_NAME:-northwind-connector}"
DATABASE_SERVER_NAME="${DATABASE_SERVER_NAME:-dbserver1}"
MAX_WAIT_SEC="${MAX_WAIT_SEC:-300}"

if [ -z "${BRONZE_TABLE:-}" ]; then
  echo "ERROR: BRONZE_TABLE is not set." >&2
  exit 1
fi

TOPIC="${DATABASE_SERVER_NAME}.public.${BRONZE_TABLE}"

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

echo "Waiting for CDC topic '${TOPIC}' (connector ${CONNECTOR_NAME}, up to ${MAX_WAIT_SEC}s)..."
i=0
while [ "$i" -lt "$MAX_WAIT_SEC" ]; do
  code=$(curl -s -o /tmp/cdc_topics_body -w "%{http_code}" \
    "${CONNECT_URL}/connectors/${CONNECTOR_NAME}/topics" 2>/dev/null || echo "000")
  if [ "$code" = "200" ] && grep -qF "${TOPIC}" /tmp/cdc_topics_body 2>/dev/null; then
    echo "CDC topic '${TOPIC}' is available."
    exit 0
  fi
  i=$((i + 5))
  sleep 5
done

echo "ERROR: CDC topic '${TOPIC}' not registered within ${MAX_WAIT_SEC}s." >&2
echo "Check connect-init logs and connector status: ${CONNECT_URL}/connectors/${CONNECTOR_NAME}/status" >&2
exit 1
