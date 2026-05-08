# Сети проекта Northwind Data Platform

## Основная сеть

- **Имя**: `data-platform-network`
- **Подсеть**: 172.25.0.0/24
- **Назначение**: связь между всеми сервисами

## IP адреса контейнеров (актуальные)

| Контейнер | IP адрес | Сети |
|-----------|----------|------|
| northwind-postgres | 172.25.0.5 | oltp-network, data-platform-network |
| northwind-kafka | 172.25.0.8 | kafka-network, data-platform-network |
| northwind-connect | 172.25.0.9 | connect-network, data-platform-network |
| northwind-spark-master | 172.25.0.X | spark-network, data-platform-network |
| northwind-minio | 172.25.0.X | storage-network, data-platform-network |

## Проверка соединений

```bash
# Пинг между контейнерами (нужен контейнер с ping)
docker run --rm --network data-platform-network alpine ping -c 2 northwind-postgres
```

## Диагностика

```bash
# Какие контейнеры подключены к общей сети
docker network inspect data-platform-network

# Проверка DNS внутри сети
docker run --rm --network data-platform-network busybox nslookup northwind-kafka
```
