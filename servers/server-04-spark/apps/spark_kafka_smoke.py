import time
from pyspark.sql import SparkSession

TOPIC = "dbserver1.public.customers"
BOOTSTRAP = "northwind-kafka:9092"

spark = (
    SparkSession.builder
    .appName("spark-kafka-smoke")
    .getOrCreate()
)

print(f"Spark version: {spark.version}")

# 1) Batch-read check (должен вернуть >0 при working CDC+Kafka)
batch_df = (
    spark.read
    .format("kafka")
    .option("kafka.bootstrap.servers", BOOTSTRAP)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "earliest")
    .option("endingOffsets", "latest")
    .load()
)

batch_count = batch_df.count()
print(f"Kafka batch count: {batch_count}")

batch_df.selectExpr("CAST(value AS STRING) AS json_value").show(3, truncate=False)

# 2) Streaming-read check
stream_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", BOOTSTRAP)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .load()
)

query = (
    stream_df
    .selectExpr("CAST(value AS STRING) AS json_value")
    .writeStream
    .format("memory")
    .queryName("spark_kafka_smoke_mem")
    .outputMode("append")
    .start()
)

time.sleep(10)

stream_count = spark.sql("SELECT COUNT(*) AS cnt FROM spark_kafka_smoke_mem").collect()[0]["cnt"]
print(f"Streaming micro-batch count (latest window): {stream_count}")

if query.exception() is not None:
    raise RuntimeError(f"Streaming query failed: {query.exception()}")

query.stop()
spark.stop()

# Итоговый статус
if batch_count <= 0:
    raise RuntimeError("Smoke failed: batch read returned 0 records from Kafka topic.")

print("Smoke OK: Spark can read Kafka (batch + streaming initialized).")
