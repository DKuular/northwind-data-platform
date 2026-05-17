#!/usr/bin/env python3
"""Bronze CDC stream. Чекпоинт в MinIO удаляй вручную при сбое Kafka; опционально BRONZE_CHECKPOINT_SUFFIX=v2 для нового пути."""

import os
import re

import spark_config
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, lit, to_date


def _spark_session(builder) -> SparkSession:
    """Сброс singleton, если JVM SparkContext уже stopped (повторный запуск / падение master)."""
    stale = False
    try:
        active = SparkSession.getActiveSession()
    except Exception:
        active = None
    if active is not None:
        try:
            jsc = active.sparkContext._jsc
            stale = jsc is None or active.sparkContext._jsc.sc().isStopped()
        except Exception:
            stale = True
    sc = getattr(SparkContext, "_active_spark_context", None)
    if not stale and sc is not None:
        try:
            stale = sc._jsc is None or sc._jsc.sc().isStopped()
        except Exception:
            stale = True
    if stale:
        SparkSession._instantiatedSession = None
        SparkSession._activeSession = None
        SparkContext._active_spark_context = None
    return builder.getOrCreate()

VALID_TABLES = {"customers", "products", "orders", "order_details"}

BRONZE_TABLE = os.getenv("BRONZE_TABLE", "customers").strip().lower()
if BRONZE_TABLE not in VALID_TABLES:
    raise ValueError(
        f"Invalid BRONZE_TABLE='{BRONZE_TABLE}'. Expected one of: "
        f"{', '.join(sorted(VALID_TABLES))}"
    )


_cfg = spark_config.load_config()
_bs = _cfg.get("bronze_streaming") or {}

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "northwind-kafka:9092")
# Должно совпадать с database.server.name / topic.prefix в Debezium (см. DATABASE_SERVER_NAME в .env).
_topic_prefix = (
    os.getenv("DEBEZIUM_TOPIC_PREFIX")
    or os.getenv("DATABASE_SERVER_NAME")
    or "dbserver1"
).strip().rstrip(".")
KAFKA_TOPIC = f"{_topic_prefix}.public.{BRONZE_TABLE}"
# Spark по умолчанию падает, если чекпоинт указывает на смещения, которых уже нет в Kafka.
# KAFKA_STRICT_OFFSETS=1 — снова жёсткий режим (для прод при контролируемом retention).
_STRICT_OFFSETS = os.getenv("KAFKA_STRICT_OFFSETS", "").strip().lower() in (
    "1",
    "true",
    "yes",
)
_FAIL_ON_LOSS = "true" if _STRICT_OFFSETS else "false"

MINIO_ENDPOINT = spark_config.minio_endpoint(_cfg)
MINIO_ACCESS_KEY = spark_config.minio_access_key(_cfg)
MINIO_SECRET_KEY = spark_config.minio_secret_key(_cfg)

if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
    raise SystemExit(
        "Set MINIO_ROOT_USER and MINIO_ROOT_PASSWORD (non-empty). "
        "Pass via docker compose environment / .env."
    )

os.environ.setdefault("AWS_ACCESS_KEY_ID", MINIO_ACCESS_KEY)
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", MINIO_SECRET_KEY)

BRONZE_BUCKET = spark_config.bronze_bucket(_cfg)
BRONZE_BASE_PATH = f"s3a://{BRONZE_BUCKET}/bronze/{BRONZE_TABLE}_cdc"
_cp_extra = os.getenv("BRONZE_CHECKPOINT_SUFFIX", "").strip()
if _cp_extra:
    _cp_extra = "_" + re.sub(r"[^a-zA-Z0-9_-]", "", _cp_extra.lstrip("_"))
else:
    _cp_extra = ""
CHECKPOINT_PATH = (
    f"s3a://{BRONZE_BUCKET}/checkpoints/bronze/{BRONZE_TABLE}_cdc{_cp_extra}"
)

SPARK_CORES_MAX = spark_config.env_override(
    "SPARK_CORES_MAX", str(_bs.get("cores_max", "2"))
)
SPARK_EXECUTOR_CORES = spark_config.env_override(
    "SPARK_EXECUTOR_CORES", str(_bs.get("executor_cores", "2"))
)
SPARK_EXECUTOR_INSTANCES = spark_config.env_override(
    "SPARK_EXECUTOR_INSTANCES", str(_bs.get("executor_instances", "1"))
)
SPARK_EXECUTOR_MEMORY = spark_config.env_override(
    "SPARK_EXECUTOR_MEMORY", str(_bs.get("executor_memory", "768m"))
)

JARS = spark_config.extra_jars_csv(_cfg)

spark = _spark_session(
    spark_config.configure_event_log(
        SparkSession.builder.appName(f"northwind-bronze-{BRONZE_TABLE}-cdc")
        .master(_cfg["spark"]["master"])
        .config("spark.cores.max", SPARK_CORES_MAX)
        .config("spark.executor.cores", SPARK_EXECUTOR_CORES)
        .config("spark.executor.instances", SPARK_EXECUTOR_INSTANCES)
        .config("spark.executor.memory", SPARK_EXECUTOR_MEMORY)
        .config("spark.sql.shuffle.partitions", _cfg["spark"]["shuffle_partitions"])
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
    )
)

spark.sparkContext.setLogLevel(spark_config.driver_log_level(_cfg))

print(
    f"[bronze_cdc] bootstrap={KAFKA_BOOTSTRAP} topic={KAFKA_TOPIC} "
    f"failOnDataLoss={_FAIL_ON_LOSS} checkpoint={CHECKPOINT_PATH}",
    flush=True,
)

raw = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest")
    .option("failOnDataLoss", _FAIL_ON_LOSS)
    .option("kafkaConsumer.request.timeout.ms", "120000")
    .option("kafkaConsumer.metadata.max.age.ms", "5000")
    .load()
)

bronze = (
    raw.select(
        col("key").cast("string").alias("kafka_key"),
        col("value").cast("string").alias("payload_json"),
        col("topic"),
        col("partition"),
        col("offset"),
        col("timestamp").alias("kafka_ts"),
        current_timestamp().alias("ingest_ts"),
    )
    .withColumn("ingest_date", to_date(col("ingest_ts")))
    .withColumn("source_topic", lit(KAFKA_TOPIC))
)

query = (
    bronze.writeStream.format("parquet")
    .outputMode("append")
    .option("path", BRONZE_BASE_PATH)
    .option("checkpointLocation", CHECKPOINT_PATH)
    .partitionBy("ingest_date")
    .trigger(processingTime="10 seconds")
    .start()
)

query.awaitTermination()
