# Clearity Backend - Quick Start

## Быстрый старт с внешней PostgreSQL БД

### 1. Настройте переменные окружения

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите ваши данные:

```env
DATABASE_URL=postgresql://ваш_user:ваш_пароль@ваш_хост:5432/clearity
OPENROUTER_API_KEY=ваш_openrouter_ключ_здесь
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Инициализируйте базу данных

Используйте утилиту для инициализации схемы:

```bash
python db_utils.py init
```

Или вручную выполните SQL:

```bash
# Если у вас есть psql
psql -h ваш_хост -U ваш_user -d clearity -f app/schemas/db_schema.sql
```

Проверьте подключение:

```bash
python db_utils.py check
```

### 4. Запустите сервер

**Рекомендуемый способ (работает везде):**

```bash
uvicorn app.main:app --reload
```

**Или на Windows:**

```bash
run.bat
```

**Или напрямую:**

```bash
python -m app.main
```

### 5. Проверьте работу

Откройте браузер:

- API Docs: http://localhost:55110/docs
- Health Check: http://localhost:55110/health

Или запустите тестовый скрипт:

```bash
python test_api.py
```

---

## Основные API endpoints

### Создать сессию

```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d "{}"
```

### Отправить сообщение

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I feel overwhelmed with too many projects"
  }'
```

### Получить mind map

```bash
curl http://localhost:8000/api/sessions/{session_id}/mindmap
```

### Получить задачи

```bash
curl http://localhost:8000/api/sessions/{session_id}/tasks
```

---

## Структура ответа /api/chat

```json
{
  "session_id": "uuid",
  "message": "Ответ ассистента...",
  "mind_map": {
    "map_name": "Lost Between 3 Startups",
    "central_theme": "Choosing where to focus as a founder",
    "fields": [...],
    "projects": [...],
    "connections": [...]
  },
  "suggested_tasks": [
    {
      "id": "uuid",
      "name": "Define what 'great' means for you",
      "priority_score": 0.92,
      "kpi": "You have written 5-10 bullet points...",
      "subtasks": ["Step 1", "Step 2", ...],
      "estimated_time_min": 20
    }
  ],
  "metadata": {
    "emotion": "overwhelm",
    "emotion_intensity": "high"
  }
}
```

---

## Troubleshooting

### База данных не подключается

Проверьте:

1. Правильный DATABASE_URL в `.env`
2. База данных `clearity` существует
3. Пользователь имеет права доступа
4. Хост и порт доступны
5. Используйте `python db_utils.py check` для диагностики

### OpenRouter API ошибки

- Проверьте API ключ в `.env`
- Убедитесь что у вас есть баланс на OpenRouter
- Проверьте логи в `logs/`

### Ошибки импорта Python

```bash
pip install -r requirements.txt --upgrade
```

### Порт 8000 занят

Измените порт в `app/main.py`:

```python
uvicorn.run(..., port=8001)
```

---

## Полезные команды

### Посмотреть логи

```bash
# Последние логи
tail -f logs/clearity_YYYYMMDD.log

# Windows
type logs\clearity_YYYYMMDD.log
```

### Очистить базу данных

```bash
python db_utils.py reset
```

Или вручную:

```bash
psql -h ваш_хост -U ваш_user -d clearity

DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

\i app/schemas/db_schema.sql
```

---

## Что дальше?

1. Изучите API документацию: http://localhost:8000/docs
2. Посмотрите примеры запросов в `test_api.py`
3. Почитайте основной `README.md` для деталей архитектуры
4. Начинайте разработку фронтенда!

---

## Важные файлы

- `app/main.py` - точка входа приложения
- `app/services/layer1_orchestrator.py` - главная логика
- `app/schemas/db_schema.sql` - схема БД
- `.env` - конфигурация (не коммитить!)
- `logs/` - логи приложения
