-- Migration: Add authentication fields to users table
-- Version: 001
-- Date: 2025-12-07 (Updated)

-- Add authentication columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_anonymous BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;

-- Set existing users as anonymous (safe for existing data)
UPDATE users SET is_anonymous = TRUE WHERE is_anonymous IS NULL OR is_anonymous = FALSE;

-- Add unique constraint on email
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_email_key') THEN
        ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email);
    END IF;
END $$;

-- Add check constraint for authentication fields
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_user_auth_fields') THEN
        ALTER TABLE users ADD CONSTRAINT check_user_auth_fields CHECK (
            (is_anonymous = TRUE AND email IS NULL AND password_hash IS NULL) OR
            (is_anonymous = FALSE AND email IS NOT NULL AND password_hash IS NOT NULL)
        );
    END IF;
END $$;

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN users.email IS 'User email address (NULL for anonymous users)';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password';
COMMENT ON COLUMN users.is_anonymous IS 'TRUE if user has not registered with email';
COMMENT ON COLUMN users.email_verified IS 'TRUE if email has been verified';
COMMENT ON COLUMN users.last_login IS 'Timestamp of last successful login';

-- Verify migration
SELECT 'Migration 001 completed successfully!' as status;
SELECT COUNT(*) as total_users, 
       COUNT(*) FILTER (WHERE is_anonymous = TRUE) as anonymous_users,
       COUNT(*) FILTER (WHERE is_anonymous = FALSE) as registered_users
FROM users;
