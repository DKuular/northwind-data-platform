#!/bin/bash

echo "🔐 Creating database roles..."

# Ждём PostgreSQL
sleep 5

# Выполняем SQL скрипт
docker exec -i northwind-postgres psql -U postgres -d northwind < infrastructure/roles/postgres-roles.sql

echo "✅ Database roles created"
