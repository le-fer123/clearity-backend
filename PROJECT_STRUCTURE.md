# Clearity Backend - Project Structure

## Complete File Tree

```
ClearityBackend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   ├── config.py                        # Settings and environment configuration
│   ├── database.py                      # Database connection pool
│   ├── logging_config.py                # Logging configuration
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── chat.py                  # POST /api/chat - Main chat endpoint
│   │       ├── session.py               # Session management endpoints
│   │       └── mindmap.py               # Mind map and tasks endpoints
│   │
│   ├── services/                        # Business logic (5 layers)
│   │   ├── __init__.py
│   │   ├── ai_client.py                 # OpenRouter API client
│   │   ├── layer1_orchestrator.py       # Layer 1: User-facing orchestrator
│   │   ├── layer2_mindmap.py            # Layer 2: Mind map builder
│   │   ├── layer3_reasoning.py          # Layer 3: Issue analysis engine
│   │   ├── layer4_actions.py            # Layer 4: Task generator
│   │   └── layer5_memory.py             # Layer 5: Long-term memory
│   │
│   ├── repositories/                    # Database access layer
│   │   ├── __init__.py
│   │   ├── session_repository.py        # Sessions & users CRUD
│   │   ├── mindmap_repository.py        # Mind maps CRUD
│   │   ├── project_repository.py        # Projects, nodes, connections CRUD
│   │   ├── task_repository.py           # Tasks, issues, plans CRUD
│   │   └── message_repository.py        # Messages & snapshots CRUD
│   │
│   ├── models/                          # Pydantic models
│   │   ├── __init__.py
│   │   ├── requests.py                  # API request models
│   │   └── responses.py                 # API response models
│   │
│   └── schemas/
│       ├── __init__.py
│       └── db_schema.sql                # PostgreSQL database schema
│
├── logs/                                # Log files (auto-created)
│   └── clearity_YYYYMMDD.log
│
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment variables template
├── .env                                 # Environment variables (DO NOT COMMIT)
├── .gitignore                           # Git ignore rules
│
├── README.md                            # Main documentation
├── QUICKSTART.md                        # Quick start guide
├── API.md                               # API documentation
├── PROJECT_STRUCTURE.md                 # This file
│
├── run.bat                              # Windows run script
├── test_api.py                          # API test script
├── db_utils.py                          # Database utility CLI
│
├── setup_db.sql                         # Database setup helper
├── SETUP_EXTERNAL_DB.md                 # External DB setup guide
├── docker-compose.yml                   # Optional: Local PostgreSQL via Docker
└── Dockerfile                           # Optional: App containerization

```

---

## File Descriptions

### Core Application Files

- **app/main.py**: FastAPI application with CORS, lifespan events, route registration
- **app/config.py**: Pydantic Settings for environment variables
- **app/database.py**: AsyncPG connection pool manager
- **app/logging_config.py**: Logging setup with file and console handlers

### API Routes

- **app/api/routes/chat.py**: Main chat endpoint - processes messages through all 5 layers
- **app/api/routes/session.py**: Session creation and management
- **app/api/routes/mindmap.py**: Mind map and task retrieval endpoints

### Services (5-Layer Architecture)

- **app/services/ai_client.py**: Wrapper for OpenRouter API calls
- **app/services/layer1_orchestrator.py**: Orchestrates all layers, talks to user
- **app/services/layer2_mindmap.py**: Builds and updates mind maps
- **app/services/layer3_reasoning.py**: Analyzes issues and root causes
- **app/services/layer4_actions.py**: Generates ADHD-friendly tasks
- **app/services/layer5_memory.py**: Manages snapshots and long-term memory

### Repositories (Data Access)

- **app/repositories/session_repository.py**: Users and sessions
- **app/repositories/mindmap_repository.py**: Mind maps
- **app/repositories/project_repository.py**: Projects, nodes, connections
- **app/repositories/task_repository.py**: Tasks, issues, root causes, plans
- **app/repositories/message_repository.py**: Messages and snapshots

### Models

- **app/models/requests.py**: Pydantic request schemas
- **app/models/responses.py**: Pydantic response schemas

### Database

- **app/schemas/db_schema.sql**: Complete PostgreSQL schema with:
    - 16 tables
    - Constraints and indexes
    - Triggers for auto-updating timestamps
    - Predefined fields (Startups, Career, Health, etc.)

### Configuration & Setup

- **requirements.txt**: Python package dependencies
- **.env.example**: Template for environment variables
- **.gitignore**: Git ignore rules for logs, .env, pycache, etc.

### Documentation

- **README.md**: Complete project documentation
- **QUICKSTART.md**: Step-by-step setup guide
- **API.md**: Detailed API reference with examples
- **PROJECT_STRUCTURE.md**: This file

### Utilities

- **run.bat**: Windows batch script to start server
- **test_api.py**: Automated API testing script
- **db_utils.py**: CLI for database management (check/init/stats/reset)
- **setup_db.sql**: Quick database initialization script

### Optional Docker Files

- **docker-compose.yml**: Optional local PostgreSQL setup (not required)
- **Dockerfile**: Optional app containerization (for future production deployment)
- **SETUP_EXTERNAL_DB.md**: Guide for setting up external PostgreSQL database

---

## Directory Conventions

### Naming

- **snake_case**: All Python files and directories
- **kebab-case**: Markdown documentation files (except README)
- **UPPERCASE**: Environment and config files (.ENV, DOCKERFILE)

### Import Structure

```python
# Standard library
import logging
from typing import Dict, Any

# Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# Local app imports
from app.config import settings
from app.database import db
from app.services.layer1_orchestrator import layer1_orchestrator
```

### Code Organization

1. **Repositories**: Pure data access, no business logic
2. **Services**: Business logic, calls repositories and AI
3. **Routes**: HTTP handling, calls services
4. **Models**: Data validation and serialization only

---

## Key Design Decisions

### No ORM

- Direct SQL queries via asyncpg
- Better performance and transparency
- Easier to debug and optimize

### Repository Pattern

- Centralized data access
- Easy to mock for testing
- Clear separation from business logic

### 5-Layer Architecture

- Each layer has single responsibility
- Only Layer 1 talks to users
- Layers 2-5 output structured data only
- Clear orchestration flow

### Async Throughout

- All I/O operations are async
- Better concurrency
- Scales well under load

### Comprehensive Logging

- Every important operation logged
- Structured log format
- Daily log rotation
- Both file and console output

---

## Database Schema Highlights

### Core Tables

- **users**: User accounts (UUID primary keys)
- **sessions**: Chat sessions linked to users
- **mind_maps**: Mind map metadata (name, theme)
- **projects**: Hierarchical projects and nodes
- **connections**: Relationships between projects/nodes

### Analysis Tables

- **issues**: Identified problems (from Layer 3)
- **root_causes**: Why users are stuck
- **plans**: Multi-step resolution plans
- **tasks**: Concrete action items (from Layer 4)

### Memory Tables

- **snapshots**: Serialized mind map states for long-term memory
- **messages**: Conversation history

### Predefined Data

- **fields**: 9 life fields (Startups, Career, Health, etc.)
    - Inserted automatically on schema creation

---

## Environment Variables

Required in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/clearity

# OpenRouter API
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# AI Models
FAST_MODEL=openai/gpt-4o-mini      # Quick tasks
DEEP_MODEL=openai/gpt-4o            # Deep reasoning

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Logging
LOG_LEVEL=INFO
```

---

## Next Steps

1. **Setup**: Follow QUICKSTART.md
2. **Explore API**: Check API.md
3. **Test**: Run test_api.py
4. **Build Frontend**: Use API endpoints to build UI
5. **Deploy**: Use Dockerfile for production

---

## Support

For questions or issues:

1. Check README.md for architecture details
2. Check QUICKSTART.md for setup help
3. Check API.md for endpoint reference
4. Check logs/ for debugging
