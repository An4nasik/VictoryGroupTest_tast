
## 🛠 Технологический стек

### Backend
- **Python 3.12+** 
- **aiogram** 
- **SQLAlchemy** + **AsyncPG** 
- **Redis** 
- **APScheduler** 
- **Alembic** 

### Инфраструктура
- **PostgreSQL** 
- **Redis** 
- **Loki** + **Grafana** -
- **Docker** 
- **uv**

## 📦 Быстрый запуск

### 1. Подготовка окружения
```bash
# Клонирование репозитория
git clone <repository-url>
cd "Victury Group Test task"

# Заполните переменные окружения
```

### 2. Настройка переменных окружения
```env
BOT_TOKEN=your_telegram_bot_token
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=telegram_bot
REDIS_URL=redis://redis:6379/0

Ну а это мой
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=mydatabase
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/mydatabase
BOT_TOKEN=7743887451:AAHCGM9IIu_O3vi68BgI-onMs0l1YzHlzgw
REDIS_HOST=redis
REDIS_PORT=6379
@RazrabotTestTaskBot - а это сам бот
```

### 3. Запуск через Docker
```bash
# Запуск всех сервисов
docker-compose up -d

# Применение миграций
docker-compose exec bot alembic upgrade head
```

## 📊 Мониторинг

- **Grafana**: http://localhost:3000 - дашборды(но это вы сами сделайте) и метрики. (admin admin)
- Может надо будет data source выбрать в Grafana

## 🏗 Архитектура

```
├── handlers/       # Обработчики команд и сообщений
├── middlewares/    # Промежуточное ПО
├── models/         # SQLAlchemy модели
├── services/       # Бизнес-логика
├── states/         # FSM состояния
├── keyboards/      # Telegram клавиатуры
├── utils/          # Утилиты
└── alembic/        # Миграции БД
```

## 🔧 Основные команды

```bash
# Создание новой миграции
docker-compose exec bot alembic revision --autogenerate -m "description"

# Применение миграций
docker-compose exec bot alembic upgrade head

# Откат миграции
docker-compose exec bot alembic downgrade -1

# Форматирование кода
uv run ruff format .

# Линтинг
uv run ruff check .
```

---

**Python версия**: 3.12+

### лицензия MIT и все такое
