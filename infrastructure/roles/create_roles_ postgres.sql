-- 1. Администратор (уже есть)
-- postgres / postgres123

-- 2. Пользователь для Debezium (CDC)
CREATE USER debezium WITH PASSWORD 'debezium123' REPLICATION;
GRANT CONNECT ON DATABASE northwind TO debezium;
GRANT USAGE ON SCHEMA public TO debezium;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO debezium;

-- 3. Пользователь для Airflow (генерация продаж)
CREATE USER airflow_user WITH PASSWORD 'airflow123';
GRANT CONNECT ON DATABASE northwind TO airflow_user;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO airflow_user;

-- 4. Пользователь для Spark (чтение)
CREATE USER spark_reader WITH PASSWORD 'spark123';
GRANT CONNECT ON DATABASE northwind TO spark_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO spark_reader;

-- 5. Пользователь для BI (только витрины)
CREATE USER bi_reader WITH PASSWORD 'bi123';
GRANT CONNECT ON DATABASE northwind TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO bi_reader;