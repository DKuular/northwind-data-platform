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

# Create env file
cp .env.example .env
# Edit .env with your local credentials

# Start platform
bash scripts/start-all.sh

```

## Service URLs

- Airflow: <http://localhost:8080>
- Superset: <http://localhost:8088>
- Grafana: <http://localhost:3000>
- MinIO: <http://localhost:9000>
- Jupyter: <http://localhost:8888>
- Prometheus: <http://localhost:9090>

## Spark/Jupyter (Production-like setup)

Jupyter uses a custom image from servers/server-04-spark/Dockerfile.jupyter.
Spark/Kafka dependencies are pinned for reproducible local runs.
Current validated Spark version: 3.5.0.

## Bronze Multi-Topic Streaming

Bronze ingestion runs as 4 independent services using one shared image
(`northwind-jupyter:3.5.0`) and one universal app
(`servers/server-04-spark/apps/bronze_cdc_table.py`).
Each service sets `BRONZE_TABLE` and writes to canonical MinIO paths in
`s3a://iceberg-warehouse`.

| Topic | Data path | Checkpoint path |
| --- | --- | --- |
| `dbserver1.public.customers` | `s3a://iceberg-warehouse/bronze/customers_cdc` | `s3a://iceberg-warehouse/checkpoints/bronze/customers_cdc` |
| `dbserver1.public.products` | `s3a://iceberg-warehouse/bronze/products_cdc` | `s3a://iceberg-warehouse/checkpoints/bronze/products_cdc` |
| `dbserver1.public.orders` | `s3a://iceberg-warehouse/bronze/orders_cdc` | `s3a://iceberg-warehouse/checkpoints/bronze/orders_cdc` |
| `dbserver1.public.order_details` | `s3a://iceberg-warehouse/bronze/order_details_cdc` | `s3a://iceberg-warehouse/checkpoints/bronze/order_details_cdc` |

Basic operations:

```bash
# View Bronze service containers
docker ps --filter "name=northwind-bronze"

# Tail logs per table
docker logs -f northwind-bronze-customers
docker logs -f northwind-bronze-products
docker logs -f northwind-bronze-orders
docker logs -f northwind-bronze-order-details
```

## Smoke Check

In Jupyter run:

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
print(spark.version)

df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "northwind-kafka:9092") \
    .option("subscribe", "dbserver1.public.customers") \
    .option("startingOffsets", "latest") \
    .load()

print("Kafka source initialized:", df.isStreaming)

```

Expected:

- `spark.version == 3.5.0`
- `Kafka source initialized: True`

## Monitoring Smoke Check

```bash
curl -s http://localhost:9090/api/v1/targets
```

Expected targets with `health: "up"`:

- `kafka-connect-jmx`
- `postgres-exporter`
- `node-exporter`
- `prometheus`

## License

MIT
