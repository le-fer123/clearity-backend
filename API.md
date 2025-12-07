# Clearity API Documentation

## Base URL

```
http://localhost:55110
```

---

## Endpoints

### Health Check

#### `GET /health`

Check API and database health.

**Response:**

```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## Authentication

Clearity supports **3 authentication modes**:

### 1. Anonymous Mode (No Auth)

No JWT token needed. Just send messages and save `session_id`.

```bash
curl -X POST http://localhost:55110/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### 2. JWT Authentication (Email + Password)

**Step 1: Register or Login**

```bash
# Register
curl -X POST http://localhost:55110/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure123"}'

# Or Login
curl -X POST http://localhost:55110/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secure123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJI...",
  "user_id": "uuid",
  "email": "user@example.com"
}
```

**Step 2: Use JWT in requests**

```bash
curl -X POST http://localhost:55110/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJI..." \
  -d '{"message": "Hello"}'
```

### 3. Google OAuth

**Step 1: Get auth URL**

```bash
curl http://localhost:55110/api/auth/google/login
# Returns: {"auth_url": "https://accounts.google.com/o/oauth2/v2/auth?..."}
```

**Step 2: Redirect user to auth_url**

**Step 3: Google redirects to callback** → returns JWT

See full documentation in `AUTH.md`



## Chat Endpoints

### Send Message

#### `POST /api/chat`

Send a message and receive AI-powered clarity insights.

**Request Body:**

```json
{
  "session_id": "uuid (optional)",
  "user_id": "uuid (optional)",
  "message": "I'm feeling overwhelmed with too many projects"
}
```

**Notes:**

- If `session_id` is omitted, a new session will be created
- If both `session_id` and `user_id` are omitted, a new user and session will be created
- First message in a session triggers full 5-layer processing

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "I hear you - feeling overwhelmed by multiple projects is really draining...",
  "mind_map": {
    "map_name": "Overwhelmed by Multiple Projects",
    "central_theme": "Too many parallel commitments causing decision paralysis",
    "fields": [
      {"id": "startups", "label": "Startups"},
      {"id": "career", "label": "Career"}
    ],
    "projects": [
      {
        "id": "uuid",
        "label": "Clearity",
        "fields": ["startups", "career"],
        "emotion": "purple",
        "clarity": "medium",
        "issue_severity": "high",
        "status": "active",
        "nodes": [
          {
            "id": "uuid",
            "label": "Needs market validation",
            "emotion": "yellow",
            "importance_score": 0.9,
            "is_core_issue": true,
            "parent_id": "parent-uuid",
            "fields": ["startups"]
          }
        ]
      }
    ],
    "connections": [
      {
        "type": "conflict",
        "from_id": "uuid",
        "to_id": "uuid",
        "strength": "high",
        "root_cause_id": "uuid or null"
      }
    ]
  },
  "suggested_tasks": [
    {
      "id": "uuid",
      "name": "Define what 'great founder' means to you",
      "related_issue": null,
      "related_projects": ["uuid"],
      "priority_score": 0.92,
      "kpi": "You have written 5-10 bullet points describing greatness",
      "subtasks": [
        "Open a blank note",
        "Write down 3-5 founders you admire",
        "List 5-10 bullet points starting with 'A great startup for me is...'",
        "Star the 3 most important points"
      ],
      "estimated_time_min": 20,
      "context_hint": "Quiet space, no notifications",
      "status": "pending"
    }
  ],
  "metadata": {
    "emotion": "overwhelm",
    "emotion_intensity": "high",
    "suggested_focus": "focus_conflict"
  }
}
```

---

### Get Session Messages

#### `GET /api/sessions/{session_id}/messages?limit=50`

Get full conversation history for a session.

**Headers (optional):**
```
Authorization: Bearer {jwt}  # For authenticated users
```

**Query Parameters:**

- `limit` (optional): Number of messages to return (default: 50)

**Response:**

```json
[
  {
    "id": "uuid",
    "session_id": "uuid",
    "role": "user",
    "content": "Hello",
    "created_at": "2024-03-15T10:30:00Z"
  },
  {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "Hi there! How can I help?",
    "created_at": "2024-03-15T10:30:05Z"
  }
]
```

---

## Session Endpoints

### Create Session

#### `POST /api/sessions`

Create a new session.

**Request Body:**

```json
{
  "user_id": "uuid (optional)"
}
```

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-03-15T10:30:00Z",
  "updated_at": "2024-03-15T10:30:00Z"
}
```

---

### Get Session

#### `GET /api/sessions/{session_id}`

Get session information.

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-03-15T10:30:00Z",
  "updated_at": "2024-03-15T10:45:00Z"
}
```

---

### Get User Snapshots

#### `GET /api/users/{user_id}/snapshots?limit=3`

Get user's previous session snapshots (for continuing work).

**Query Parameters:**

- `limit` (optional): Number of snapshots to return (default: 3)

**Response:**

```json
[
  {
    "map_id": "uuid",
    "map_name": "Lost Between 3 Startups",
    "last_updated": "2024-03-15T10:45:00Z",
    "summary": "Choosing where to focus as a founder",
    "unresolved_issues": ["focus_conflict", "validation_anxiety"]
  }
]
```

---

## Mind Map Endpoints

### Get Mind Map

#### `GET /api/sessions/{session_id}/mindmap`

Get the current mind map for a session.

**Response:**

```json
{
  "map_name": "Lost Between 3 Startups",
  "central_theme": "Choosing where to focus as a founder",
  "fields": [
    {"id": "startups", "label": "Startups"},
    {"id": "career", "label": "Career"}
  ],
  "projects": [...],
  "connections": [...]
}
```

---

### Get Tasks

#### `GET /api/sessions/{session_id}/tasks?limit=5`

Get suggested tasks for a session.

**Query Parameters:**

- `limit` (optional): Number of tasks to return (default: 5)

**Response:**

```json
[
  {
    "id": "uuid",
    "name": "Define what 'great founder' means to you",
    "related_issue": null,
    "related_projects": ["uuid"],
    "priority_score": 0.92,
    "kpi": "You have written 5-10 bullet points",
    "subtasks": ["Step 1", "Step 2", "Step 3"],
    "estimated_time_min": 20,
    "context_hint": "Quiet space",
    "status": "pending"
  }
]
```

---

## Data Models

### Emotions (Node Colors)

- `red` - overwhelm, anxiety, stress
- `orange` - frustration, chaos, confusion
- `yellow` - uncertainty, doubt, ambivalence
- `green` - hope, progress, clarity
- `blue` - calm, stability, control
- `purple` - excitement, passion, creativity
- `grey` - unknown, insufficient data

### Issue Severity

- `none` - No significant issue
- `low` - Minor concern
- `medium` - Notable problem
- `high` - Major crisis area (large red dot)

### Connection Types

- `dependency` - A must be resolved before B
- `conflict` - A and B are incompatible or competing
- `shared_root_cause` - Both affected by same underlying cause

### Connection Strength

- `low` - Weak relationship
- `medium` - Moderate relationship
- `high` - Strong relationship

### Task Status

- `pending` - Not started
- `in_progress` - Currently working on
- `completed` - Finished

### Clarity Levels

- `low` - Unclear, confusing
- `medium` - Partially clear
- `high` - Very clear

### Fields of Life (Predefined)

- `startups` - Startups
- `career` - Career
- `education` - Education
- `health` - Health
- `mental_health` - Mental Health
- `relationships` - Relationships
- `money` - Money
- `family` - Family
- `personal_growth` - Personal Growth

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid request data"
}
```

### 404 Not Found

```json
{
  "detail": "Session not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Error processing message: [error details]"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. This will be added in production.

---

## Authentication

Clearity supports both anonymous and authenticated modes.

### Anonymous Access

All endpoints (except `/api/auth/*`) work without authentication.
Simply omit the `Authorization` header.

### Authenticated Access

For registered users, include JWT token:

```http
Authorization: Bearer {access_token}
```

**How to get JWT:**
1. Register: `POST /api/auth/register`
2. Login: `POST /api/auth/login`
3. Google OAuth: `GET /api/auth/google/login`

**Full authentication guide:** See `AUTH.md`

---

## Example Flow

### 1. Start a new session

```bash
curl -X POST http://localhost:55110/api/sessions \
  -H "Content-Type: application/json" \
  -d '{}'
```

Response:

```json
{
  "session_id": "abc-123",
  "user_id": "def-456"
}
```

### 2. Send first message

```bash
curl -X POST http://localhost:55110/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "message": "I have three startup ideas but I don't know which to focus on"
  }'
```

### 3. Get mind map

```bash
curl http://localhost:55110/api/sessions/abc-123/mindmap
```

### 4. Get tasks

```bash
curl http://localhost:55110/api/sessions/abc-123/tasks
```

### 5. Continue conversation

```bash
curl -X POST http://localhost:55110/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc-123",
    "message": "I think Clearity is most aligned with my values"
  }'
```

### 6. Later: Resume from snapshot

```bash
# Get user's previous sessions
curl http://localhost:55110/api/users/def-456/snapshots

# Continue in new session with context from previous work
curl -X POST http://localhost:55110/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "def-456",
    "message": "I want to continue working on Clearity"
  }'
```

---

## WebSocket Support (Future)

Real-time updates will be added via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:55110/ws/session/abc-123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time mind map updates
};
```

---

## Interactive API Documentation

Visit http://localhost:55110/docs for interactive Swagger UI documentation where you can test all endpoints directly in
your browser.
