# Быстрый старт

```bash
# 1) Клонировать репозиторий
git clone https://github.com/DKuular/northwind-data-platform.git
cd northwind-data-platform

# 2) Подготовить переменные окружения
cp .env.example .env
# Заполните .env реальными значениями
# Если у вас уже есть существующий volume Postgres, не меняйте POSTGRES_PASSWORD
# без явной смены пароля в БД (ALTER USER) или reset volume.

# 3) Запустить платформу
bash scripts/start-all.sh

# 4) Проверить, что контейнеры живы
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## Следующий шаг после запуска

- Импортируйте демо-данные и настройте CDC по инструкции: `docs/setup/import_northwind.md`.
- Проверьте мониторинг:

```bash
curl -s http://localhost:9090/api/v1/targets
```

Ожидается, что основные таргеты (`prometheus`, `node-exporter`,
`kafka-connect-jmx`, `postgres-exporter`) будут в статусе `up`.
