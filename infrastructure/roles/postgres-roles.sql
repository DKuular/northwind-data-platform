-- ============================================
-- PostgreSQL Roles for Northwind Data Platform
-- ============================================

-- Роль для Debezium (CDC)
CREATE ROLE debezium WITH LOGIN REPLICATION;
GRANT CONNECT ON DATABASE northwind TO debezium;
GRANT USAGE ON SCHEMA public TO debezium;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO debezium;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO debezium;

-- Роль для Airflow (генерация и обновление данных)
CREATE ROLE airflow WITH LOGIN;
GRANT CONNECT ON DATABASE northwind TO airflow;
GRANT USAGE ON SCHEMA public TO airflow;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO airflow;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO airflow;

-- Роль для Spark (только чтение)
CREATE ROLE spark_reader WITH LOGIN;
GRANT CONNECT ON DATABASE northwind TO spark_reader;
GRANT USAGE ON SCHEMA public TO spark_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO spark_reader;

-- Роль для BI (только чтение витрин)
CREATE ROLE bi_reader WITH LOGIN;
GRANT CONNECT ON DATABASE northwind TO bi_reader;
GRANT USAGE ON SCHEMA mart TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO bi_reader;

-- Роль для мониторинга
CREATE ROLE monitor WITH LOGIN;
GRANT CONNECT ON DATABASE northwind TO monitor;
GRANT pg_monitor TO monitor;

-- Создание publication для логической репликации
CREATE PUBLICATION debezium_publication FOR ALL TABLES;

-- Вывод информации
\du
