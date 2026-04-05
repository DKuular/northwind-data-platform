#!/bin/bash

set -e

echo "🌐 Creating isolated networks for Northwind Data Platform"

# Функция для создания сети
create_network() {
    local name=$1
    local subnet=$2
    local gateway=$3
    
    if docker network inspect "$name" >/dev/null 2>&1; then
        echo "  ⚠️  Network $name already exists"
    else
        docker network create \
            --driver bridge \
            --subnet="$subnet" \
            --gateway="$gateway" \
            "$name"
        echo "  ✅ Created $name ($subnet)"
    fi
}

# Общая сеть для межсерверного взаимодействия
create_network "data-platform-network" "172.25.0.0/24" "172.25.0.1"

# Сервер 1: OLTP (PostgreSQL + Airflow)
create_network "oltp-network" "172.20.0.0/24" "172.20.0.1"

# Сервер 2: Kafka
create_network "kafka-network" "172.21.0.0/24" "172.21.0.1"

# Сервер 3: Kafka Connect
create_network "connect-network" "172.22.0.0/24" "172.22.0.1"

# Сервер 4: Spark
create_network "spark-network" "172.23.0.0/24" "172.23.0.1"

# Сервер 5: Storage (MinIO + Superset)
create_network "storage-network" "172.24.0.0/24" "172.24.0.1"

# Сервер 6: Quality (Soda + Prometheus + Grafana)
create_network "quality-network" "172.26.0.0/24" "172.26.0.1"

# Сервер 7: Catalog (OpenMetadata)
create_network "catalog-network" "172.27.0.0/24" "172.27.0.1"

# Сервер 8: ML (Feast + MLflow)
create_network "ml-network" "172.28.0.0/24" "172.28.0.1"

echo ""
echo "✅ Networks created successfully"
echo ""
echo "📡 Network list:"
docker network ls | grep -E "oltp|kafka|connect|spark|storage|quality|catalog|ml|data-platform"
