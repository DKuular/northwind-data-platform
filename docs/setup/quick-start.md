## 🚀 Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/DKuular/northwind_modern.git
cd northwind_modern

# 2. Настроить окружение
cp .env.example .env
# Отредактируйте .env (пароли)

# 3. Запустить все сервисы
./scripts/start-all.sh

# 4. Импортировать данные
./scripts/import-northwind.sh

# 5. Проверить здоровье
./scripts/health-check.sh

# копирование файла с в докер
docker cp /c/pojects/northwind-data-platform/northwind.sql northwind-postgres:/northwind.sql



