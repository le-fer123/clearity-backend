-- Clearity Database Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE,
    password_hash TEXT,
    is_anonymous BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    -- Allow three states:
    -- 1) anonymous users (no email or password)
    -- 2) registered users with password
    -- 3) registered OAuth users with email but no password (password_hash NULL)
    CONSTRAINT check_user_auth_fields CHECK (
        (is_anonymous = TRUE AND email IS NULL AND password_hash IS NULL) OR
        (is_anonymous = FALSE AND email IS NOT NULL)
    )
);

-- Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mind Maps
CREATE TABLE IF NOT EXISTS mind_maps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    map_name TEXT NOT NULL,
    central_theme TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Predefined Fields (fields of life)
CREATE TABLE IF NOT EXISTS fields (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL
);

INSERT INTO fields (id, label) VALUES
    ('startups', 'Startups'),
    ('career', 'Career'),
    ('education', 'Education'),
    ('health', 'Health'),
    ('mental_health', 'Mental Health'),
    ('relationships', 'Relationships'),
    ('money', 'Money'),
    ('family', 'Family'),
    ('personal_growth', 'Personal Growth')
ON CONFLICT (id) DO NOTHING;

-- Projects (includes both projects and nodes in a hierarchical structure)
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mind_map_id UUID NOT NULL REFERENCES mind_maps(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    emotion TEXT NOT NULL DEFAULT 'grey',
    clarity TEXT,
    issue_severity TEXT DEFAULT 'none',
    status TEXT DEFAULT 'active',
    importance_score DECIMAL(3,2) DEFAULT 0.5,
    is_core_issue BOOLEAN DEFAULT FALSE,
    is_visible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_emotion CHECK (emotion IN ('red', 'orange', 'yellow', 'green', 'blue', 'purple', 'grey')),
    CONSTRAINT check_clarity CHECK (clarity IN ('low', 'medium', 'high')),
    CONSTRAINT check_severity CHECK (issue_severity IN ('none', 'low', 'medium', 'high')),
    CONSTRAINT check_importance CHECK (importance_score BETWEEN 0 AND 1)
);

-- Project-Field associations (many-to-many)
CREATE TABLE IF NOT EXISTS project_fields (
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    field_id TEXT NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    PRIMARY KEY (project_id, field_id)
);

-- Connections between projects/nodes
CREATE TABLE IF NOT EXISTS connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mind_map_id UUID NOT NULL REFERENCES mind_maps(id) ON DELETE CASCADE,
    connection_type TEXT NOT NULL,
    from_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    to_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    strength TEXT NOT NULL DEFAULT 'medium',
    root_cause_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_connection_type CHECK (connection_type IN ('dependency', 'shared_root_cause', 'conflict')),
    CONSTRAINT check_strength CHECK (strength IN ('low', 'medium', 'high'))
);

-- Issues identified by Layer 3
CREATE TABLE IF NOT EXISTS issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mind_map_id UUID NOT NULL REFERENCES mind_maps(id) ON DELETE CASCADE,
    issue_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_issue_severity CHECK (severity IN ('low', 'medium', 'high'))
);

-- Issue-Project associations
CREATE TABLE IF NOT EXISTS issue_projects (
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    PRIMARY KEY (issue_id, project_id)
);

-- Root causes
CREATE TABLE IF NOT EXISTS root_causes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mind_map_id UUID NOT NULL REFERENCES mind_maps(id) ON DELETE CASCADE,
    cause_id TEXT NOT NULL,
    short_explanation TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Root cause - Issue associations
CREATE TABLE IF NOT EXISTS root_cause_issues (
    root_cause_id UUID NOT NULL REFERENCES root_causes(id) ON DELETE CASCADE,
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    PRIMARY KEY (root_cause_id, issue_id)
);

-- Plans (multi-step plans to resolve issues)
CREATE TABLE IF NOT EXISTS plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    steps JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tasks generated by Layer 4
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mind_map_id UUID NOT NULL REFERENCES mind_maps(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    related_issue_id UUID REFERENCES issues(id) ON DELETE SET NULL,
    priority_score DECIMAL(3,2) NOT NULL,
    kpi TEXT NOT NULL,
    subtasks JSONB NOT NULL,
    estimated_time_min INTEGER,
    context_hint TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT check_priority CHECK (priority_score BETWEEN 0 AND 1),
    CONSTRAINT check_task_status CHECK (status IN ('pending', 'in_progress', 'completed'))
);

-- Task-Project associations
CREATE TABLE IF NOT EXISTS task_projects (
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, project_id)
);

-- Snapshots for Layer 5 (long-term memory)
CREATE TABLE IF NOT EXISTS snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    mind_map_id UUID REFERENCES mind_maps(id) ON DELETE SET NULL,
    snapshot_data JSONB NOT NULL,
    progress_notes TEXT,
    unresolved_issues JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages (for conversation history)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_role CHECK (role IN ('user', 'assistant', 'system'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_mind_maps_session_id ON mind_maps(session_id);
CREATE INDEX IF NOT EXISTS idx_projects_mind_map_id ON projects(mind_map_id);
CREATE INDEX IF NOT EXISTS idx_projects_parent_id ON projects(parent_id);
CREATE INDEX IF NOT EXISTS idx_connections_mind_map_id ON connections(mind_map_id);
CREATE INDEX IF NOT EXISTS idx_issues_mind_map_id ON issues(mind_map_id);
CREATE INDEX IF NOT EXISTS idx_tasks_mind_map_id ON tasks(mind_map_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_session_id ON snapshots(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- OAuth accounts (linking external provider identities to local users)
CREATE TABLE IF NOT EXISTS oauth_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    provider_user_id TEXT NOT NULL,
    provider_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (provider, provider_user_id)
);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mind_maps_updated_at BEFORE UPDATE ON mind_maps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
