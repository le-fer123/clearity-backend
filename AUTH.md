# Clearity Authentication

Полная документация системы аутентификации Clearity Backend.

---

## Архитектура

Clearity поддерживает **3 режима работы**:

### 1. Анонимный режим
- **Не требует регистрации** и JWT токена
- Сохраняй `session_id` в localStorage фронтенда
- Идеально для быстрого старта без трения
- ⚠️ При потере `session_id` данные утеряны (это норма для анонима)

### 2. Email + Password режим
- Регистрация через `POST /api/auth/register`
- Вход через `POST /api/auth/login`
- Получаешь JWT токен
- Используй JWT в заголовке: `Authorization: Bearer {token}`
- Все сессии привязаны к `user_id` из JWT

### 3. Google OAuth режим
- Авторизация через `GET /api/auth/google/login`
- Google редирект → callback → автоматический вход/регистрация
- Получаешь JWT токен
- Используй JWT так же, как при email регистрации

---

## API Endpoints

### 1. Регистрация (Email + Password)

#### `POST /api/auth/register`

Создание нового пользователя с email и паролем.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

**Errors:**
- `400` - Email уже зарегистрирован
- `500` - Ошибка регистрации

**Rate Limit:** 5 запросов/минуту

---

### 2. Вход (Email + Password)

#### `POST /api/auth/login`

Вход существующего пользователя.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com"
}
```

**Errors:**
- `401` - Неверный email или пароль
- `500` - Ошибка входа

**Rate Limit:** 5 запросов/минуту

---

### 3. Получение информации о пользователе

#### `GET /api/auth/me`

Получение информации о текущем пользователе (требует JWT).

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "is_anonymous": false,
  "email_verified": false,
  "created_at": "2024-12-07T10:30:00Z",
  "last_login": "2024-12-07T15:45:00Z"
}
```

**Errors:**
- `401` - JWT токен отсутствует или невалиден
- `404` - Пользователь не найден

**Rate Limit:** 5 запросов/минуту

---

### 4. Google OAuth - Инициация

#### `GET /api/auth/google/login`

Получение ссылки для авторизации через Google.

**Response (200 OK):**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=..."
}
```

**Errors:**
- `500` - Google OAuth не настроен (отсутствуют `GOOGLE_CLIENT_ID` или `GOOGLE_REDIRECT_URI`)

**Использование:**
```javascript
// Frontend
const response = await fetch('http://localhost:55110/api/auth/google/login');
const data = await response.json();

// Редирект пользователя
window.location.href = data.auth_url;
```

---

### 5. Google OAuth - Callback

#### `GET /api/auth/google/callback`

Обработка callback от Google после авторизации.

**Query Parameters:**
- `code` (required) - Authorization code от Google

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Сценарии:**
1. **Новый пользователь** → создается user → создается oauth_account → возвращается JWT
2. **Существующий OAuth аккаунт** → возвращается JWT
3. **Существующий email** → линкуется oauth_account к существующему user → возвращается JWT

**Errors:**
- `400` - Missing code
- `502` - Ошибка обмена code на token или получения userinfo
- `500` - Google OAuth не настроен

---

## Интеграция на Frontend

### Вариант 1: Анонимный пользователь

```javascript
// Первое сообщение - без auth
const response = await fetch('http://localhost:55110/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "I feel overwhelmed"
  })
});

const data = await response.json();

// Сохрани session_id
localStorage.setItem('sessionId', data.session_id);

// Последующие сообщения
await fetch('http://localhost:55110/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: localStorage.getItem('sessionId'),
    message: "What should I do?"
  })
});
```

---

### Вариант 2: Регистрация + Вход

```javascript
// Регистрация
const registerResponse = await fetch('http://localhost:55110/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'secure123'
  })
});

const { access_token, user_id } = await registerResponse.json();

// Сохрани токен
localStorage.setItem('jwt', access_token);
localStorage.setItem('userId', user_id);

// Теперь отправляй сообщения с JWT
await fetch('http://localhost:55110/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('jwt')}`
  },
  body: JSON.stringify({
    message: "Hello!"
  })
});
```

---

### Вариант 3: Google OAuth

```javascript
// 1. Получи auth URL
const response = await fetch('http://localhost:55110/api/auth/google/login');
const { auth_url } = await response.json();

// 2. Редирект на Google
window.location.href = auth_url;

// 3. После callback Google вернет на GOOGLE_REDIRECT_URI
// Backend обработает callback и вернет JWT
// Frontend должен извлечь JWT из response и сохранить

// Пример callback page:
// http://yourfrontend.com/auth/callback?code=...
// Отправь code на backend или дай backend сделать redirect
```

---

## Environment Variables

Добавь в `.env`:

```env
# JWT
JWT_SECRET=your-super-secret-key-min-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=30

# Google OAuth (опционально)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:55110/api/auth/google/callback
```

### Получение Google OAuth credentials:

1. Перейди в [Google Cloud Console](https://console.cloud.google.com/)
2. Создай проект или выбери существующий
3. Включи Google+ API
4. Credentials → Create Credentials → OAuth 2.0 Client ID
5. Authorized redirect URIs: `http://localhost:55110/api/auth/google/callback`
6. Скопируй Client ID и Client Secret в `.env`

---

## Тестирование

### Автоматический тест

```bash
python test_auth.py
```

Тест проверяет:
1. ✅ Анонимный режим (без JWT)
2. ✅ Продолжение анонимной сессии
3. ✅ Регистрация
4. ✅ Login
5. ✅ Аутентифицированный чат

---

### Ручное тестирование

#### 1. Анонимный чат

```bash
curl -X POST http://localhost:55110/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I feel overwhelmed"}'
```

#### 2. Регистрация

```bash
curl -X POST http://localhost:55110/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "secure123"}'
```

#### 3. Вход

```bash
curl -X POST http://localhost:55110/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "secure123"}'
```

#### 4. Получение профиля

```bash
curl -X GET http://localhost:55110/api/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

#### 5. Аутентифицированный чат

```bash
curl -X POST http://localhost:55110/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -d '{"message": "Hello!"}'
```

---

## FAQ

### В чем разница между анонимным и зарегистрированным режимом?

| Функция | Анонимный | Зарегистрированный |
|---------|-----------|-------------------|
| Требуется email | ❌ Нет | ✅ Да |
| JWT токен | ❌ Нет | ✅ Да |
| Сохранение данных | Только session_id | Все сессии привязаны к user |
| Продолжение на другом устройстве | ❌ Нет | ✅ Да |
| Snapshots пользователя | ❌ Нет | ✅ Да |

### Как перевести анонимного пользователя в зарегистрированного?

В текущей реализации - нельзя напрямую. Пользователь должен зарегистрироваться, и его новые сессии будут привязаны к аккаунту.

**Будущая feature:** endpoint для "claim" анонимной сессии.

### Можно ли использовать только Google OAuth без email/password?

Да! Google OAuth полностью независим. Пользователь может войти только через Google, без создания пароля.

### Где хранятся пароли?

Пароли хранятся в БД в виде bcrypt хешей (используется `passlib[bcrypt]`). Никогда в plain text.

### Сколько живет JWT токен?

По умолчанию **30 дней** (настраивается через `JWT_EXPIRATION_DAYS` в `.env`).

---

## Security Best Practices

1. ✅ **JWT_SECRET** должен быть минимум 32 символа
2. ✅ Используй HTTPS в production
3. ✅ Не храни JWT в localStorage (используй httpOnly cookies) - но для MVP localStorage OK
4. ✅ Реализуй refresh tokens для production
5. ✅ Добавь email verification для production
6. ✅ Включи CORS только для доверенных доменов

---

**Документация актуальна для:** Clearity Backend v1.0.0
