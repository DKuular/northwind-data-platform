Правильный импорт (работает на Windows)


# Способ 1: через cat и psql
```bash
curl -L -o northwind.sql https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql
```


# Проверяем содержимое
```bash
head -5 northwind.sql
```

# Смотрим первые строки файла
```bash
head -5 northwind.sql
```

# Список таблиц
```bash
docker exec northwind-postgres psql -U postgres -d northwind -c "\dt"
```

# Количество записей в основных таблицах
```bash
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM customers;"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM products;"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM orders;"
docker exec northwind-postgres psql -U postgres -d northwind -c "SELECT COUNT(*) FROM order_details;"
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
  