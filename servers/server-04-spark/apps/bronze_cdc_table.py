#!/usr/bin/env python3

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, lit, to_date

VALID_TABLES = {"customers", "products", "orders", "order_details"}

BRONZE_TABLE = os.getenv("BRONZE_TABLE", "customers").strip().lower()
if BRONZE_TABLE not in VALID_TABLES:
    raise ValueError(
        f"Invalid BRONZE_TABLE='{BRONZE_TABLE}'. Expected one of: "
        f"{', '.join(sorted(VALID_TABLES))}"
    )

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "northwind-kafka:9092")
KAFKA_TOPIC = f"dbserver1.public.{BRONZE_TABLE}"

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://northwind-minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "change_me")

BRONZE_BUCKET = os.getenv("BRONZE_BUCKET", "iceberg-warehouse")
BRONZE_BASE_PATH = f"s3a://{BRONZE_BUCKET}/bronze/{BRONZE_TABLE}_cdc"
CHECKPOINT_PATH = f"s3a://{BRONZE_BUCKET}/checkpoints/bronze/{BRONZE_TABLE}_cdc"

spark = (
    SparkSession.builder.appName(f"northwind-bronze-{BRONZE_TABLE}-cdc")
    .master("spark://spark-master:7077")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config(
        "spark.jars",
        "/opt/spark-extra-jars/spark-sql-kafka-0-10_2.12-3.5.0.jar,"
        "/opt/spark-extra-jars/spark-token-provider-kafka-0-10_2.12-3.5.0.jar,"
        "/opt/spark-extra-jars/kafka-clients-3.5.0.jar,"
        "/opt/spark-extra-jars/commons-pool2-2.12.0.jar,"
        "/opt/spark-extra-jars/hadoop-aws-3.3.4.jar,"
        "/opt/spark-extra-jars/aws-java-sdk-bundle-1.12.262.jar,"
        "/opt/spark-extra-jars/iceberg-spark-runtime-3.5_2.12-1.5.0.jar",
    )
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

raw = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest")
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
