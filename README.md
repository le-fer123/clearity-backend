# Clearity Backend

AI clarity engine for people who feel mentally overloaded, scattered, or stuck.

## Architecture

Clearity implements a **4-layer architecture**:

1. **Layer 1 - Support & Orchestrator**: User-facing layer, coordinates all others
2. **Layer 2 - Visualization / Mind Map Builder**: Builds living mind maps
3. **Layer 4 - Reasoning & Actions**: Analyzes issues, identifies root causes, and generates concrete ADHD-friendly tasks (merged Layer 3 + 4)
4. **Layer 5 - Memory & Retrieval**: Long-term session memory

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (no ORM)
- **AI**: OpenRouter.ai (GPT-4o-mini for fast tasks, GPT-4o for deep reasoning)
- **Python**: 3.11+

## Project Structure

```
ClearityBackend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration & environment
│   ├── database.py             # Database connection pool
│   ├── logging_config.py       # Logging setup
│   ├── api/
│   │   └── routes/            # API endpoints
│   │       ├── chat.py        # Main chat endpoint
│   │       ├── session.py     # Session management
│   │       └── mindmap.py     # Mind map & tasks endpoints
│   ├── services/              # Business logic layers
│   │   ├── layer1_orchestrator.py
│   │   ├── layer2_mindmap.py
│   │   ├── layer4_actions.py     # Merged Layer 3 + 4: Reasoning & Actions
│   │   ├── layer5_memory.py
│   │   └── ai_client.py
│   ├── repositories/          # Database access layer
│   │   ├── session_repository.py
│   │   ├── mindmap_repository.py
│   │   ├── project_repository.py
│   │   ├── task_repository.py
│   │   └── message_repository.py
│   ├── models/                # Pydantic models
│   │   ├── requests.py
│   │   └── responses.py
│   └── schemas/
│       └── db_schema.sql      # Database schema
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your external PostgreSQL connection:

```env
DATABASE_URL=postgresql://your_user:your_password@your_host:5432/clearity
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 3. Initialize Database

```bash
python db_utils.py init
```

Or manually with psql:

```bash
psql -h your_host -U your_user -d clearity -f app/schemas/db_schema.sql
```

Verify setup:

```bash
python db_utils.py check
```

### 4. Run the Application

**Recommended:**

```bash
uvicorn app.main:app --reload
```

**Or:**

```bash
python -m app.main
```

**Windows:**

```bash
run.bat
```

The API will be available at `http://localhost:55110`

API documentation: `http://localhost:55110/docs`

## API Endpoints

### Chat

- `POST /api/chat` - Send a message (creates session if needed)

### Sessions

- `POST /api/sessions` - Create a new session
- `GET /api/sessions/{session_id}` - Get session info
- `GET /api/users/{user_id}/snapshots` - Get user's previous sessions

### Mind Map

- `GET /api/sessions/{session_id}/mindmap` - Get current mind map
- `GET /api/sessions/{session_id}/tasks` - Get suggested tasks

### Health

- `GET /health` - Health check (includes database status)

## How It Works

1. **User sends a message** → Layer 1 receives it
2. **Layer 1 analyzes context** → emotion, intent, session stage
3. **Layer 5 loads memory** → retrieves previous snapshots if available
4. **Layer 2 builds/updates mind map** → projects, nodes, emotions, connections
5. **Layer 4 analyzes and acts** → identifies issues, root causes, plans, and generates concrete ADHD-friendly tasks
6. **Layer 1 responds** → warm, human message with insights and suggestions
7. **Layer 5 stores snapshot** → for future sessions

## Database Schema

Key tables:

- `users` - User accounts
- `sessions` - Chat sessions
- `mind_maps` - Mind map states
- `fields` - Predefined life fields (Startups, Career, Health, etc.)
- `projects` - Hierarchical projects and nodes
- `connections` - Dependencies, conflicts, shared root causes
- `issues` - Identified problems
- `root_causes` - Why users are stuck
- `tasks` - Concrete action steps
- `snapshots` - Long-term memory snapshots
- `messages` - Conversation history

## Logging

Logs are stored in `logs/` directory with daily rotation.

Log format:

```
YYYY-MM-DD HH:MM:SS | LEVEL | module:function:line | message
```

Adjust log level in `.env`:

```env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## Development

### Code Structure Principles

- **Separation of concerns**: Each layer has a single responsibility
- **No ORM**: Direct SQL queries for transparency and performance
- **Type safety**: Pydantic models for all API contracts
- **Async throughout**: All I/O operations are async
- **Comprehensive logging**: Every important operation is logged

### Adding New Features

1. **Database**: Add tables/columns in `app/schemas/db_schema.sql`
2. **Repository**: Add data access methods in `app/repositories/`
3. **Service**: Add business logic in appropriate layer service
4. **API**: Add endpoint in `app/api/routes/`
5. **Models**: Add request/response models in `app/models/`

## License

Proprietary
