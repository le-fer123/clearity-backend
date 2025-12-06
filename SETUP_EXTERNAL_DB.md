E# Настройка внешней PostgreSQL базы данных

## Предварительные требования

У вас должна быть PostgreSQL база данных с именем `clearity`.

---

## Вариант 1: Автоматическая инициализация (Рекомендуется)

### 1. Создайте .env файл

```bash
cp .env.example .env
```

### 2. Укажите данные подключения в .env

```env
DATABASE_URL=postgresql://user:password@host:port/clearity
OPENROUTER_API_KEY=ваш_ключ
```

Пример:

```env
DATABASE_URL=postgresql://postgres:mypassword@db.example.com:5432/clearity
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Инициализируйте схему

```bash
python db_utils.py init
```

Эта команда:

- Подключится к БД
- Выполнит весь SQL из `app/schemas/db_schema.sql`
- Создаст все таблицы, индексы, триггеры
- Вставит предопределённые данные (fields)

### 5. Проверьте установку

```bash
python db_utils.py check
```

Вы должны увидеть:

```
✓ Connected to PostgreSQL
  Version: PostgreSQL 16.x

Checking tables:
  ✓ users
  ✓ sessions
  ✓ mind_maps
  ... (все 16 таблиц)
```

### 6. Запустите сервер

```bash
python app/main.py
```

---

## Вариант 2: Ручная инициализация

Если у вас есть `psql` или другой PostgreSQL клиент:

### 1. Подключитесь к базе данных

```bash
psql -h ваш_хост -U ваш_user -d clearity
```

Или используйте GUI клиент (pgAdmin, DBeaver, etc.)

### 2. Выполните SQL схему

Скопируйте содержимое файла `app/schemas/db_schema.sql` и выполните в вашей БД.

Или через psql:

```bash
psql -h ваш_хост -U ваш_user -d clearity -f app/schemas/db_schema.sql
```

### 3. Проверьте таблицы

```sql
\dt
```

Вы должны увидеть 16 таблиц:

- users
- sessions
- mind_maps
- fields
- projects
- project_fields
- connections
- issues
- issue_projects
- root_causes
- root_cause_issues
- plans
- tasks
- task_projects
- snapshots
- messages

### 4. Проверьте predefined fields

```sql
SELECT * FROM fields;
```

Должны быть 9 записей:

- startups
- career
- education
- health
- mental_health
- relationships
- money
- family
- personal_growth

---

## Проверка подключения

### Через db_utils.py

```bash
# Проверить подключение и таблицы
python db_utils.py check

# Посмотреть статистику
python db_utils.py stats
```

### Через Python скрипт

Создайте файл `test_db.py`:

```python
import asyncio
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()


async def test():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    # Проверка версии
    version = await conn.fetchval("SELECT version()")
    print(f"PostgreSQL: {version}")

    # Проверка таблиц
    tables = await conn.fetch("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    print(f"\nТаблицы ({len(tables)}):")
    for table in tables:
        print(f"  - {table['table_name']}")

    # Проверка fields
    fields = await conn.fetch("SELECT * FROM fields")
    print(f"\nFields ({len(fields)}):")
    for field in fields:
        print(f"  - {field['id']}: {field['label']}")

    await conn.close()
    print("\n✓ Всё работает!")


asyncio.run(test())
```

Запустите:

```bash
python test_db.py
```

---

## Частые проблемы

### Ошибка: "database does not exist"

База данных не создана. Создайте её:

```sql
-- Подключитесь к серверу PostgreSQL
psql -h ваш_хост -U ваш_user -d postgres

-- Создайте базу
CREATE DATABASE clearity;
```

### Ошибка: "permission denied"

У пользователя нет прав. Выдайте права:

```sql
GRANT ALL PRIVILEGES ON DATABASE clearity TO ваш_user;
GRANT ALL ON SCHEMA public TO ваш_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ваш_user;
```

### Ошибка: "could not connect to server"

Проверьте:

1. Хост и порт правильные
2. Firewall не блокирует подключение
3. PostgreSQL сервер запущен
4. SSL требования (добавьте `?sslmode=require` если нужно)

Пример с SSL:

```env
DATABASE_URL=postgresql://user:pass@host:5432/clearity?sslmode=require
```

### Таблицы уже существуют

Если нужно пересоздать схему:

```bash
python db_utils.py reset
python db_utils.py init
```

Или вручную:

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO ваш_user;
```

Затем выполните схему заново.

---

## Проверка через API

После инициализации БД запустите сервер:

```bash
python app/main.py
```

Проверьте health endpoint:

```bash
curl http://localhost:55110/health
```

Ответ:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

Если видите `"database": "disconnected"` - проверьте логи в `logs/`.

---

## Следующие шаги

1. ✅ База данных инициализирована
2. ✅ Подключение работает
3. ⏭️ Вставьте OpenRouter API ключ в `.env`
4. ⏭️ Запустите сервер: `python app/main.py`
5. ⏭️ Протестируйте API: `python test_api.py`
6. ⏭️ Начинайте разработку!

---

## Дополнительные команды db_utils.py

```bash
# Проверить подключение и таблицы
python db_utils.py check

# Инициализировать схему
python db_utils.py init

# Показать статистику БД
python db_utils.py stats

# Сбросить все данные (ОСТОРОЖНО!)
python db_utils.py reset
```

---

## Backup и восстановление

### Создать backup

```bash
pg_dump -h ваш_хост -U ваш_user -d clearity -F c -f clearity_backup.dump
```

### Восстановить из backup

```bash
pg_restore -h ваш_хост -U ваш_user -d clearity -c clearity_backup.dump
```

---

Готово! Ваша внешняя БД настроена и готова к работе.
