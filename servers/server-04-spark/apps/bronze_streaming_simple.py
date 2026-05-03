#!/usr/bin/env python3
"""Упрощённый Spark Streaming для теста"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, LongType

spark = SparkSession.builder \
    .appName("Test Streaming") \
    .master("spark://spark-master:7077") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.iceberg.type", "hadoop") \
    .config("spark.sql.catalog.iceberg.warehouse", "s3a://iceberg-warehouse/") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minio123") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=" * 50)
print("Test Streaming Started")
print("=" * 50)

# Читаем из Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "dbserver1.public.customers") \
    .option("startingOffsets", "earliest") \
    .load()

# Выводим в консоль
query = df.writeStream \
    .outputMode("append") \
    .format("console") \
    .trigger(processingTime="5 seconds") \
    .start()

