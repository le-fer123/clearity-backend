-- Quick database setup script
-- Run this after creating the database

-- Connect to your database first:
-- psql -U your_user -d clearity

-- Then execute this file:
-- \i setup_db.sql

-- Or from command line:
-- psql -U your_user -d clearity -f setup_db.sql

\i app/schemas/db_schema.sql

-- Verify setup
SELECT 'Database setup complete!' as status;

-- Show tables
\dt

-- Show fields
SELECT * FROM fields;
