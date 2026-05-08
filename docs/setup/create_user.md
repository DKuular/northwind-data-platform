# Пользователи и доступы

## Superset admin

```bash
# Создать администратора
docker exec -it northwind-superset superset fab create-admin \
  --username "${SUPERSET_ADMIN_USER:-admin}" \
  --firstname Admin \
  --lastname User \
  --email admin@example.com \
  --password "${SUPERSET_ADMIN_PASSWORD:-change_me}"

# Инициализация Superset
docker exec -it northwind-superset superset db upgrade
docker exec -it northwind-superset superset init
```

## Airflow admin (если нужен ручной reset)

Обычно пользователь создается автоматически при запуске `northwind-airflow`.
Проверка списка пользователей:

```bash
docker exec -it northwind-airflow airflow users list
```

Создание вручную при необходимости:

```bash
docker exec -it northwind-airflow airflow users create \
  --username admin \
  --password "${AIRFLOW_PASSWORD:-change_me}" \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```

## Быстрые проверки доступа

```bash
# Superset
curl -I http://localhost:8088

# Airflow
curl -I http://localhost:8080
```
