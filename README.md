# Service Desk Bot

> Telegram service desk bot on aiogram 3 + async PostgreSQL (SQLAlchemy 2.0). Role-based access (Owner/Master/Admin), 18-state FSM ticket flow, real-time notifications, FastAPI admin panel, Docker deployment. Alembic migrations.

Telegram-бот сервисной службы для приёма и обработки заявок на обслуживание жилых комплексов.

## Обслуживаемые ЖК

| ЖК | Блоки/Подъезды | Категории услуг |
|---|---|---|
| Alasha Residence | 20 подъездов | Видеонаблюдение, Face ID, Госномер, Камеры, Домофон, Прочее |
| Terekti Park | 25 блоков | Ключ/магнит, Камеры, Домофон, Прочее |
| Kemel UI | 19 блоков | Ключ/магнит, Камеры, Домофон, Прочее |
| Jana Omir | 7 блоков | Ключ/магнит, Камеры, Домофон, Прочее |

## Роли пользователей

### Собственник (Owner)
- Авторизация по номеру телефона (отправка контакта)
- Создание заявок через пошаговый диалог (выбор ЖК → блок/подъезд → квартира → категория → доп. поля → описание → фото → подтверждение)
- Просмотр своих заявок с пагинацией
- Оценка работы мастера (1-5 звёзд + комментарий)
- Инструкции по подключению к камерам (Hik-Connect для Alasha, EasyViewer для остальных)
- Лимит: 10 заявок в день

### Мастер (Master)
- Просмотр новых, активных и выполненных заявок
- Принятие заявки в работу
- Завершение заявки
- Уведомления о новых заявках с кнопками действий

### Администратор (Admin)
- Просмотр всех заявок с фильтрами (статус, ЖК, мастер, период)
- Детальная карточка заявки с историей изменений
- Переназначение мастера на заявку
- Уведомления о каждой новой заявке

## Стек

- **Python 3.11+** — язык
- **aiogram 3.x** — асинхронный Telegram Bot API фреймворк
- **PostgreSQL 16** — база данных
- **SQLAlchemy 2.0 async + asyncpg** — ORM
- **Alembic** — миграции БД
- **Docker + Docker Compose** — контейнеризация
- **pydantic-settings** — конфигурация из `.env`

## Быстрый старт

### Предварительные требования

- [Docker](https://docs.docker.com/get-docker/) и [Docker Compose](https://docs.docker.com/compose/install/)
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

### 1. Клонировать репозиторий

```bash
git clone <url-репозитория>
cd service-desk-bot
```

### 2. Создать файл `.env`

```bash
cp .env.example .env
```

Открыть `.env` и вписать свой токен бота:

```
BOT_TOKEN=123456789:AABBccDDeeFFggHHiiJJkkLLmmNNooPPqq
```

Остальные переменные можно оставить по умолчанию:

| Переменная | Описание | Значение по умолчанию |
|---|---|---|
| `BOT_TOKEN` | Токен Telegram бота | **(обязательно)** |
| `DB_HOST` | Хост PostgreSQL | `postgres` |
| `DB_PORT` | Порт PostgreSQL | `5432` |
| `DB_USER` | Пользователь БД | `qss_bot` |
| `DB_PASS` | Пароль БД | `changeme` |
| `DB_NAME` | Имя базы данных | `qss_service` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

### 3. Запустить

```bash
make up
```

Эта команда:
1. Поднимет PostgreSQL 16 в контейнере
2. Дождётся готовности БД (healthcheck)
3. Соберёт и запустит бот
4. Автоматически применит миграции Alembic при старте

### 4. Загрузить тестовые данные

```bash
make seed
```

Добавит в БД тестовых собственников, мастеров и админа. Подробности — в `scripts/seed_data.py`.

**Важно:** для тестирования мастеров и админов нужно заменить `telegram_id` в `scripts/seed_data.py` на реальные ID ваших Telegram-аккаунтов (узнать свой ID можно у бота [@userinfobot](https://t.me/userinfobot)).

### 5. Открыть бота в Telegram

Найдите вашего бота по имени в Telegram и отправьте `/start`.

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Начать работу / авторизация |
| `/help` | Справка |
| `/cancel` | Отмена текущего действия |

После авторизации навигация происходит через inline-кнопки.

## Управление проектом (Makefile)

```bash
make up                        # Собрать и запустить (PostgreSQL + бот)
make down                      # Остановить все контейнеры
make logs                      # Логи бота (tail -f)
make migrate                   # Применить миграции Alembic
make migration msg="описание"  # Создать новую миграцию
make seed                      # Загрузить тестовые данные
make psql                      # Открыть psql-консоль к БД
```

## Запуск без Docker (для разработки)

Требуется работающий PostgreSQL и Python 3.11+.

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить .env (DB_HOST=localhost для локальной БД)
cp .env.example .env
# отредактировать .env: BOT_TOKEN=..., DB_HOST=localhost

# 3. Применить миграции
alembic upgrade head

# 4. (опционально) Загрузить тестовые данные
python -m scripts.seed_data

# 5. Запустить бота
python -m bot
```

## Как добавить реальных пользователей

### Собственники

Добавить записи в таблицу `owners` через SQL или скрипт:

```sql
INSERT INTO owners (phone, full_name, residential_complex, block, entrance, apartment)
VALUES ('77001234567', 'Фамилия Имя Отчество', 'alasha', NULL, '5', '42');
```

- `phone` — номер телефона (формат: 7XXXXXXXXXX, без `+`)
- `residential_complex` — одно из: `alasha`, `terekti`, `kemel`, `jana_omir`
- `block` — номер блока (для Terekti/Kemel/Jana Omir), `NULL` для Alasha
- `entrance` — номер подъезда
- `apartment` — номер квартиры

Собственник авторизуется, отправив контакт в бот. Бот найдёт его по номеру телефона и привяжет `telegram_id`.

### Мастера

```sql
INSERT INTO masters (telegram_id, full_name, username, residential_complex)
VALUES (123456789, 'Имя Мастера', 'telegram_username', 'alasha');
```

- `telegram_id` — ID Telegram-аккаунта мастера
- `residential_complex` — через запятую, если обслуживает несколько ЖК: `'terekti,kemel,jana_omir'`

### Администраторы

```sql
INSERT INTO admins (telegram_id, full_name)
VALUES (123456789, 'Имя Администратора');
```

## Архитектура

```
handlers/ → services/ → db/repositories/ → db/models/
```

- **Handlers** — обработчики Telegram (никогда не делают SQL)
- **Services** — бизнес-логика (создание заявок, уведомления)
- **Repositories** — чистый доступ к данным (CRUD)
- **Models** — SQLAlchemy модели (5 таблиц)

### Структура проекта

```
service-desk-bot/
├── bot/
│   ├── __main__.py              # Точка входа
│   ├── config.py                # Настройки из .env
│   ├── callbacks/               # CallbackData классы для inline-кнопок
│   ├── db/
│   │   ├── models/              # SQLAlchemy модели (Owner, Master, Admin, Ticket, TicketHistory)
│   │   └── repositories/        # Функции доступа к данным
│   ├── filters/                 # RoleFilter (owner/master/admin)
│   ├── handlers/
│   │   ├── common.py            # /start, авторизация, /help, /cancel
│   │   ├── owner/               # Создание заявок, просмотр, оценка
│   │   ├── master/              # Принятие и выполнение заявок
│   │   └── admin/               # Фильтры, детали, переназначение
│   ├── keyboards/               # Inline-клавиатуры
│   ├── middlewares/              # Сессия БД, авторизация, анти-флуд
│   ├── services/                # Бизнес-логика
│   ├── states/                  # FSM-состояния
│   └── utils/                   # Константы, форматирование, пагинация
├── alembic/                     # Миграции БД
├── scripts/
│   └── seed_data.py             # Тестовые данные
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
├── .env.example
└── alembic.ini
```

## Формат ID заявки

```
QSS-YYYYMMDD-NNNN
```

Пример: `QSS-20260131-0003` — третья заявка за 31 января 2026 года.

## Статусы заявок

| Статус | Описание |
|---|---|
| Новая | Заявка создана, ожидает мастера |
| В работе | Мастер принял заявку |
| Выполнена | Мастер отметил как выполненную |
| Закрыта | Собственник оценил работу |
| Отменена | Заявка отменена |
| Ожидание клиента | Ожидается действие от собственника |

## Лицензия

MIT License. See [LICENSE](LICENSE) for details.
