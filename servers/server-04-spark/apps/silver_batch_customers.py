#!/usr/bin/env python3
"""
Batch Silver v1: bronze/customers_cdc (raw Debezium JSON in payload_json)
-> silver/customers (flattened columns).

Run inside Jupyter/Spark image, e.g.:
  spark-submit --master spark://spark-master:7077 --jars ... silver_batch_customers.py

Env:
  MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD
  SILVER_BUCKET (optional override for bucket)
  SPARK_MASTER (optional)
  SPARK_CORES_MAX, SPARK_EXECUTOR_*, SPARK_SHUFFLE_PARTITIONS — override silver_batch in config.json
  SPARK_EVENT_LOG_ENABLED=(0|1) — override spark_observability.event_log_enabled
  SPARK_DRIVER_LOG_LEVEL — override spark_observability.driver_log_level (e.g. INFO)
"""

from __future__ import annotations

import os

import spark_config
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    coalesce,
    col,
    current_timestamp,
    get_json_object,
    to_date,
)

_cfg = spark_config.load_config()
_sb = _cfg.get("silver_batch") or {}

SILVER_SHUFFLE_DEFAULT = str(
    _sb.get("shuffle_partitions") or _cfg["spark"]["shuffle_partitions"]
)
SHUFFLE_PARTITIONS = spark_config.env_override(
    "SPARK_SHUFFLE_PARTITIONS", SILVER_SHUFFLE_DEFAULT
)
SPARK_CORES_MAX = spark_config.env_override(
    "SPARK_CORES_MAX", str(_sb.get("cores_max", "4"))
)
SPARK_EXECUTOR_CORES = spark_config.env_override(
    "SPARK_EXECUTOR_CORES", str(_sb.get("executor_cores", "2"))
)
SPARK_EXECUTOR_INSTANCES = spark_config.env_override(
    "SPARK_EXECUTOR_INSTANCES", str(_sb.get("executor_instances", "2"))
)
SPARK_EXECUTOR_MEMORY = spark_config.env_override(
    "SPARK_EXECUTOR_MEMORY", str(_sb.get("executor_memory", "1g"))
)

MINIO_ENDPOINT = spark_config.minio_endpoint(_cfg)
MINIO_ACCESS_KEY = spark_config.minio_access_key(_cfg)
MINIO_SECRET_KEY = spark_config.minio_secret_key(_cfg)
SILVER_BUCKET = spark_config.bucket_name(_cfg)

if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
    raise SystemExit(
        "Set MINIO_ROOT_USER and MINIO_ROOT_PASSWORD (non-empty). "
        "Use servers/server-04-spark/.env with docker compose, or "
        "`docker exec -e MINIO_ROOT_USER=... -e MINIO_ROOT_PASSWORD=...`."
    )

# S3A AWS SDK sometimes consults these env vars before Hadoop fs.* keys.
os.environ.setdefault("AWS_ACCESS_KEY_ID", MINIO_ACCESS_KEY)
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", MINIO_SECRET_KEY)

BRONZE_PATH = f"s3a://{SILVER_BUCKET}/bronze/customers_cdc"
SILVER_PATH = f"s3a://{SILVER_BUCKET}/silver/customers"

JARS = spark_config.extra_jars_csv(_cfg)

spark = spark_config.configure_event_log(
    SparkSession.builder.appName("northwind-silver-customers-batch")
    .master(os.getenv("SPARK_MASTER", _cfg["spark"]["master"]))
    .config("spark.cores.max", SPARK_CORES_MAX)
    .config("spark.executor.cores", SPARK_EXECUTOR_CORES)
    .config("spark.executor.instances", SPARK_EXECUTOR_INSTANCES)
    .config("spark.executor.memory", SPARK_EXECUTOR_MEMORY)
    .config("spark.sql.shuffle.partitions", SHUFFLE_PARTITIONS)
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
    )
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.jars", JARS),
    _cfg,
).getOrCreate()

spark.sparkContext.setLogLevel(spark_config.driver_log_level(_cfg))

bronze = spark.read.parquet(BRONZE_PATH)

# Debezium envelope: payload.op, payload.before / payload.after (JSON objects).
root = "$.payload"
silver = (
    bronze.select(
        get_json_object(col("payload_json"), f"{root}.op").alias("cdc_op"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.customer_id"),
            get_json_object(col("payload_json"), f"{root}.before.customer_id"),
        ).alias("customer_id"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.company_name"),
            get_json_object(col("payload_json"), f"{root}.before.company_name"),
        ).alias("company_name"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.contact_name"),
            get_json_object(col("payload_json"), f"{root}.before.contact_name"),
        ).alias("contact_name"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.contact_title"),
            get_json_object(col("payload_json"), f"{root}.before.contact_title"),
        ).alias("contact_title"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.address"),
            get_json_object(col("payload_json"), f"{root}.before.address"),
        ).alias("address"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.city"),
            get_json_object(col("payload_json"), f"{root}.before.city"),
        ).alias("city"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.region"),
            get_json_object(col("payload_json"), f"{root}.before.region"),
        ).alias("region"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.postal_code"),
            get_json_object(col("payload_json"), f"{root}.before.postal_code"),
        ).alias("postal_code"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.country"),
            get_json_object(col("payload_json"), f"{root}.before.country"),
        ).alias("country"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.phone"),
            get_json_object(col("payload_json"), f"{root}.before.phone"),
        ).alias("phone"),
        coalesce(
            get_json_object(col("payload_json"), f"{root}.after.fax"),
            get_json_object(col("payload_json"), f"{root}.before.fax"),
        ).alias("fax"),
        col("kafka_ts"),
        col("offset").alias("kafka_offset"),
        col("ingest_ts"),
        col("ingest_date"),
    )
    .withColumn("silver_processed_at", current_timestamp())
    .withColumn("silver_process_date", to_date(col("silver_processed_at")))
)

# v1: full refresh into silver path (replace dataset). Switch to merge/Iceberg later.
silver.write.mode("overwrite").partitionBy("silver_process_date").parquet(SILVER_PATH)

spark.stop()
