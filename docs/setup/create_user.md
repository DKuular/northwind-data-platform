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