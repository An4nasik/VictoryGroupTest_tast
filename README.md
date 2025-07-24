
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
git clone https://github.com/An4nasik/VictoryGroupTest_tast
cd "VictoryGroupTest_tast"

# Заполните переменные окружения
```

### 2. Настройка переменных окружения
```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DATABASE_URL=
BOT_TOKEN=
REDIS_HOST=
REDIS_PORT=

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

## 🤖 Команды бота

### 👥 Общие команды (для всех пользователей)
Потыкайтесь главное, там не слишком интуитивно вышло, но получилось че получилось, а менять что то - я боюсь 
| Команда | Описание |
|---------|----------|
| `/start` | Регистрация нового пользователя или приветствие существующего |
| `/reregister` | Повторная регистрация (смена email и роли) |

### 📝 Команды модератора

| Команда | Описание |
|---------|----------|
| `/create_newsletter` | Создание новой раcсылки с поддержкой текста, медиа и inline-кнопок, ну в общем че вы там хотели. |

### ⚙️ Команды администратора

| Команда | Описание |
|---------|----------|
| `/stats` | Просмотр общей статистики пользователей в боте |
| `/setrole` | Изменение роли пользователя по Telegram ID |


**Python версия**: 3.12+

### лицензия MIT и все такое
