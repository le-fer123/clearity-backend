# Simplified JWT Authentication

## Архитектура

### Анонимный режим
- **Не отправляешь JWT токен** вообще
- Сохраняешь `session_id` в localStorage
- При потере `session_id` → данные утеряны (это норма для анонима)

### Зарегистрированный режим
- `POST /api/auth/register` → получаешь JWT
- `POST /api/auth/login` → получаешь JWT
- Используешь JWT в заголовке: `Authorization: Bearer {token}`
- Все твои сессии привязаны к `user_id` из JWT

---

## API Endpoints

### `POST /api/auth/register`
**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": "uuid",
  "email": "user@example.com"
}
```

### `POST /api/auth/login`
**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "user_id": "uuid",
  "email": "user@example.com"
}
```

### `GET /api/auth/me`
Требует JWT токен

**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "is_anonymous": false,
  "email_verified": false,
  "created_at": "2025-12-06T...",
  "last_login": "2025-12-06T..."
}
```

### `POST /api/chat`
**Anonymous (без JWT):**
```json
{
  "session_id": "uuid-or-null",
  "message": "Hello"
}
```

**Authenticated (с JWT):**
```http
POST /api/chat
Authorization: Bearer eyJhbGc...

{
  "message": "Hello"
}
```

---

## Тестирование

```bash
python test_auth.py
```

Тест проверяет:
1. Анонимный режим (без JWT)
2. Продолжение анонимной сессии
3. Регистрация
4. Login
5. Аутентифицированный чат
