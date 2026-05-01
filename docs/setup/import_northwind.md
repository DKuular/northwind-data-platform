# Импорт Northwind данных и настройка CDC

## 1. Скачивание дампа Northwind

```bash
curl -L -o northwind.sql https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql
```

# 2. Копирование в контейнер и импорт
```bash
docker cp northwind.sql northwind-postgres:/northwind.sql
```

# 3. Проверка импорта
```bash
docker exec northwind-postgres psql -U postgres -d northwind -c "\dt"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM customers;"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM products;"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM orders;"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM order_details;"
```

# 4. Обновление дат (сдвиг на 9 лет)
```bash
docker exec -i northwind-postgres psql -U postgres -d northwind << 'EOF'
UPDATE orders SET 
    order_date = order_date + INTERVAL '9 years',
    required_date = required_date + INTERVAL '9 years',
    shipped_date = shipped_date + INTERVAL '9 years';

UPDATE employees SET 
    birth_date = birth_date + INTERVAL '9 years',
    hire_date = hire_date + INTERVAL '9 years';
EOF
```


# 5. Количество записей в основных таблицах
```bash
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM customers;"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM products;"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM orders;"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM order_details;"
```

# 6. Создание пользователей и прав
```bash
docker exec -i northwind-postgres psql -U postgres -d northwind << 'EOF'
-- Debezium (CDC)
CREATE USER debezium WITH PASSWORD 'debezium123' REPLICATION;
GRANT CONNECT ON DATABASE northwind TO debezium;
GRANT USAGE ON SCHEMA public TO debezium;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO debezium;
CREATE PUBLICATION dbz_publication FOR ALL TABLES;

-- Airflow (генерация данных)
CREATE USER airflow_user WITH PASSWORD 'airflow123';
GRANT CONNECT ON DATABASE northwind TO airflow_user;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO airflow_user;

-- Spark (чтение)
CREATE USER spark_reader WITH PASSWORD 'spark123';
GRANT CONNECT ON DATABASE northwind TO spark_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO spark_reader;

-- BI (только витрины)
CREATE USER bi_reader WITH PASSWORD 'bi123';
GRANT CONNECT ON DATABASE northwind TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO bi_reader;
EOF
```


# 7. Создание бд Airflow 
```bash
docker exec northwind-postgres psql -U postgres -c "CREATE DATABASE airflow;"
docker restart northwind-airflow
```
# Создание учетки в админскими правами
```bash
docker exec northwind-airflow airflow users create \
  --username admin \
  --password admin123 \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```
# Проверка какие есть учетки
```bash
docker exec northwind-airflow airflow users list
```

# 8. Настройка Debezium коннектора
```bash
# Удаляем старый коннектор (если есть)
curl -X DELETE http://localhost:8083/connectors/northwind-connector 2>/dev/null

# Создаём новый
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "northwind-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "database.hostname": "northwind-postgres",
      "database.port": "5432",
      "database.user": "debezium",
      "database.password": "debezium123",
      "database.dbname": "northwind",
      "topic.prefix": "dbserver1",
      "plugin.name": "pgoutput",
      "table.include.list": "public.customers,public.products,public.orders,public.order_details",
      "snapshot.mode": "initial"
    }
  }'
```

# 7. Проверка CDC
```bash
docker exec northwind-kafka kafka-topics --bootstrap-server localhost:9092 --list | grep dbserver1

docker exec northwind-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic dbserver1.public.customers \
  --from-beginning \
  --max-messages 3
```

# Удаляем старый коннектор
```bash
curl -X DELETE http://localhost:8083/connectors/northwind-connector
```

# Создаём новый
```bash
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "northwind-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "database.hostname": "host.docker.internal",
      "database.port": "5432",
      "database.user": "debezium",
      "database.password": "debezium123",
      "database.dbname": "northwind",
      "topic.prefix": "dbserver1",
      "plugin.name": "pgoutput",
      "table.include.list": "public.customers,public.products,public.orders,public.order_details",
      "snapshot.mode": "initial"
    }
  }'
  ```

# Проверка топиков в Kafka
```bash
docker exec northwind-kafka kafka-topics --bootstrap-server localhost:9092 --list | grep dbserver1
```

# Чтение сообщений из топика customers
```bash
docker exec northwind-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic dbserver1.public.customers \
  --from-beginning \
  --max-messages 5
```