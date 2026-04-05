#!/bin/bash

echo "🔌 Setting up Debezium PostgreSQL connector..."

# Проверка, что Kafka Connect готов
echo "Waiting for Kafka Connect to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8083/ > /dev/null 2>&1; then
    echo "✅ Kafka Connect is ready"
    break
  fi
  echo "  Waiting... ($i/30)"
  sleep 2
done

# Создание коннектора
echo "Creating connector..."
RESPONSE=$(curl -s -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "northwind-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "database.hostname": "northwind-postgres",
      "database.port": "5432",
      "database.user": "postgres",
      "database.password": "postgres123",
      "database.dbname": "northwind",
      "database.server.name": "dbserver1",
      "topic.prefix": "dbserver1",
      "plugin.name": "pgoutput",
      "table.include.list": "public.orders,public.customers,public.order_details,public.products",
      "snapshot.mode": "initial"
    }
  }')

echo "Response: $RESPONSE"
echo ""

# Проверка статуса
echo "Checking connector status..."
sleep 3
curl -s http://localhost:8083/connectors/northwind-connector/status

echo ""
echo "✅ Done!"