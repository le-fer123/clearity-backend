-- Migration: Add authentication fields to users table
-- Version: 001
-- Date: 2025-12-06

-- Add authentication columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_anonymous BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;

-- Set existing users as anonymous (safe for existing data)
UPDATE users SET is_anonymous = TRUE WHERE email IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN users.email IS 'User email address (NULL for anonymous users)';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password';
COMMENT ON COLUMN users.is_anonymous IS 'TRUE if user has not registered with email';
COMMENT ON COLUMN users.email_verified IS 'TRUE if email has been verified';
COMMENT ON COLUMN users.last_login IS 'Timestamp of last successful login';
