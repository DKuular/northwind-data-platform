# Архитектура

Northwind Data Platform разделена на 8 логических серверов (`servers/server-01` ... `server-08`), объединенных общей сетью `data-platform-network`.

## Поток данных

1. `server-01-oltp`: PostgreSQL + Airflow генерируют и хранят транзакционные данные.
2. `server-03-kafka-connect`: Debezium читает WAL PostgreSQL и публикует CDC события в Kafka.
3. `server-02-kafka`: Kafka хранит событийный поток (`dbserver1.*` topics).
4. `server-04-spark`: Spark Structured Streaming читает Kafka и обрабатывает поток для аналитики.
5. `server-05-storage`: MinIO/Superset используются для хранения и BI-доступа.
6. `server-06-quality`: Prometheus/Grafana собирают и визуализируют метрики платформы.
7. `server-07-catalog` и `server-08-ml`: каталог метаданных и ML-контур.

## Точки входа

- Полный запуск: `bash scripts/start-all.sh`
- Остановка: `bash scripts/stop-all.sh`
- Проверка мониторинга: `curl -s http://localhost:9090/api/v1/targets`
