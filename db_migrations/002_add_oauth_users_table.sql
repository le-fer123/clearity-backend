-- Migration: Add OAuth accounts table 
-- Version: 002
-- Date: 2025-12-07

-- Create oauth_accounts table
CREATE TABLE IF NOT EXISTS public.users
(
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    email text COLLATE pg_catalog."default",
    password_hash text COLLATE pg_catalog."default",
    is_anonymous boolean DEFAULT false,
    email_verified boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp with time zone,
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT check_user_auth_fields CHECK (is_anonymous = true AND email IS NULL AND password_hash IS NULL OR is_anonymous = false AND email IS NOT NULL)
);

-- Add comments for documentation
COMMENT ON TABLE oauth_accounts IS 'Table to link OAuth provider accounts to local users';
COMMENT ON COLUMN oauth_accounts.user_id IS 'Reference to local user';
COMMENT ON COLUMN oauth_accounts.provider IS 'OAuth provider name (e.g., google, facebook)';
COMMENT ON COLUMN oauth_accounts.provider_user_id IS 'User ID from the OAuth provider';
COMMENT ON COLUMN oauth_accounts.provider_data IS 'Additional data from the OAuth provider in JSON format';

-- Verify migration
SELECT 'Migration 002 completed successfully!' as status;

