-- Migration: 001_initial_schema.sql
-- Description: Initial database schema setup for Congressional Transparency Platform
-- Date: 2025-09-22
-- Author: Database Migration System

BEGIN;

-- Record migration start
INSERT INTO metadata.migrations (migration_name, executed_at)
VALUES ('001_initial_schema', NOW());

-- Create application database user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'congress_app') THEN
        CREATE ROLE congress_app WITH LOGIN PASSWORD 'secure_password_change_in_production';
    END IF;
END
$$;

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA congress TO congress_app;
GRANT USAGE ON SCHEMA senate TO congress_app;
GRANT USAGE ON SCHEMA analysis TO congress_app;
GRANT USAGE ON SCHEMA metadata TO congress_app;

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA congress TO congress_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA senate TO congress_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analysis TO congress_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA metadata TO congress_app;

-- Grant sequence permissions for auto-incrementing IDs
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA congress TO congress_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA senate TO congress_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analysis TO congress_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA metadata TO congress_app;

-- Grant permissions on materialized views
GRANT SELECT ON ALL TABLES IN SCHEMA analysis TO congress_app;

-- Allow refreshing materialized views
GRANT EXECUTE ON FUNCTION refresh_all_materialized_views() TO congress_app;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA congress GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO congress_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA senate GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO congress_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA analysis GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO congress_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA metadata GRANT SELECT, INSERT, UPDATE ON TABLES TO congress_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA congress GRANT USAGE, SELECT ON SEQUENCES TO congress_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA senate GRANT USAGE, SELECT ON SEQUENCES TO congress_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA analysis GRANT USAGE, SELECT ON SEQUENCES TO congress_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA metadata GRANT USAGE, SELECT ON SEQUENCES TO congress_app;

-- Create extension for better text search if not exists
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Update migration record with success
UPDATE metadata.migrations
SET
    execution_time_ms = EXTRACT(EPOCH FROM (NOW() - executed_at)) * 1000,
    success = true,
    records_migrated = (
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema IN ('congress', 'senate', 'analysis', 'metadata')
    )
WHERE migration_name = '001_initial_schema';

COMMIT;