# Northwind Data Platform

Production-like data platform for Northwind sales analytics.

## Architecture

![Architecture](docs/architecture.png)

## Tech Stack

- **CDC**: Debezium + Kafka
- **Processing**: Spark Structured Streaming
- **Storage**: Apache Iceberg + MinIO
- **Orchestration**: Apache Airflow
- **Data Quality**: Soda Core
- **Monitoring**: Prometheus + Grafana
- **Data Catalog**: OpenMetadata
- **Feature Store**: Feast
- **ML**: Prophet + MLflow
- **BI**: Apache Superset

## Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/northwind-data-platform.git
cd northwind-data-platform

# Copy environment variables
cp .env.example .env
# Edit .env with your passwords

# Deploy all servers
./scripts/deploy-all.sh

#Access URLs
Service	URL
Airflow	    http://localhost:8080
Superset	http://localhost:8088
Grafana	    http://localhost:3000
MinIO	    http://localhost:9000

License
MIT