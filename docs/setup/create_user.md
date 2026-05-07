# Создаём admin пользователя
docker exec -it northwind-superset superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@example.com \
  --password admin

# Инициализируем базу данных
docker exec -it northwind-superset superset db upgrade

# Загружаем примеры (опционально)
docker exec -it northwind-superset superset load_examples

# Инициализируем роли и разрешения
docker exec -it northwind-superset superset init


# Запуск контейера СПАРК

# Запустить в фоновом режиме

```bash
nohup spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3 \
  /home/jovyan/bronze_streaming_final.py \
  > /home/jovyan/streaming.log 2>&1 &
```

# Запуск
docker exec -d northwind-jupyter /home/jovyan/start_streaming.sh

# Остановка
docker exec northwind-jupyter /home/jovyan/stop_streaming.sh

# Статус
docker exec northwind-jupyter /home/jovyan/status_streaming.sh

# Логи
docker exec northwind-jupyter tail -f /home/jovyan/streaming.log


# Добавляем запуск стриминга в .bashrc (выполняется при входе в контейнер)
echo "/home/jovyan/start_streaming.sh" >> /home/jovyan/.bashrc

# Просмотр всех топиков Kafka
docker exec northwind-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Детальная информация о топике

# Описание конкретного топика
docker exec northwind-kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic dbserver1.public.customers

# Количество сообщений в топике
docker exec northwind-kafka kafka-run-class kafka.tools.GetOffsetShell \
  --bootstrap-server localhost:9092 \
  --topic dbserver1.public.customers \
  --time -1

# Чтение сообщений из любого топика
docker exec northwind-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic dbserver1.public.orders \
  --from-beginning \
  --max-messages 5

# Скачайте JAR-файлы Iceberg (если ещё нет)
cd /c/pojects/northwind-data-platform/servers/server-04-spark/jars

curl -L -o iceberg-spark-runtime-3.5_2.12-1.5.0.jar https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.5.0/iceberg-spark-runtime-3.5_2.12-1.5.0.jar

# Скопируйте в контейнер

docker cp jars/iceberg-spark-runtime-3.5_2.12-1.5.0.jar northwind-spark-master:/opt/spark/jars/


# Скачайте необходимые JAR-файлы на хост

# Hadoop AWS JAR
curl -L -o hadoop-aws-3.3.4.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar

docker cp /c/pojects/northwind-data-platform/servers/server-04-spark/jars/hadoop-aws-3.3.4.jar  northwind-jupyter:/usr/local/spark/jars/

# AWS SDK Core
curl -L -o aws-java-sdk-bundle-1.12.262.jar https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

docker cp /c/pojects/northwind-data-platform/servers/server-04-spark/jars/aws-java-sdk-bundle-1.12.262.jar  northwind-jupyter:/usr/local/spark/jars/
