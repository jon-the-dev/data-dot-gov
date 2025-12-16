-- Performance Tuning and Optimization Scripts
-- Applied after initial schema creation

-- Enable query plan analysis
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create additional performance indexes based on common query patterns

-- Composite indexes for complex queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_congress_sponsor_date
ON congress.bills(congress_number, sponsor_bioguide_id, introduced_date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_member_votes_member_date
ON congress.member_votes(bioguide_id, (
    SELECT vote_date FROM congress.votes v WHERE v.vote_id = member_votes.vote_id
));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_votes_congress_chamber_date
ON congress.votes(congress_number, chamber, vote_date DESC);

-- Partial indexes for common filtered queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_became_law_true
ON congress.bills(congress_number, introduced_date) WHERE became_law = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_current_members
ON congress.members(party, state_code) WHERE current_member = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bipartisan_votes_true
ON analysis.bipartisan_votes(vote_id) WHERE is_bipartisan = true;

-- GIN indexes for array and text search
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bill_categories_keywords_gin
ON analysis.bill_categories USING GIN(keywords);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lobbying_issues_agencies_gin
ON senate.lobbying_issues USING GIN(houses_and_agencies);

-- Text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_title_search
ON congress.bills USING GIN(to_tsvector('english', title));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bills_summary_search
ON congress.bills USING GIN(to_tsvector('english', COALESCE(summary, '')));

-- Function-based indexes for computed values
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_votes_year_month
ON congress.votes(EXTRACT(YEAR FROM vote_date), EXTRACT(MONTH FROM vote_date));

-- Update table statistics for better query planning
ANALYZE congress.members;
ANALYZE congress.bills;
ANALYZE congress.votes;
ANALYZE congress.member_votes;
ANALYZE congress.bill_sponsors;
ANALYZE senate.lobbying_registrations;
ANALYZE analysis.member_party_unity;

-- Configure autovacuum settings for high-activity tables
ALTER TABLE congress.member_votes SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

ALTER TABLE congress.votes SET (
    autovacuum_vacuum_scale_factor = 0.2,
    autovacuum_analyze_scale_factor = 0.1
);

-- Create function to refresh statistics
CREATE OR REPLACE FUNCTION refresh_table_statistics()
RETURNS VOID AS $$
BEGIN
    ANALYZE congress.members;
    ANALYZE congress.bills;
    ANALYZE congress.votes;
    ANALYZE congress.member_votes;
    ANALYZE congress.bill_sponsors;
    ANALYZE congress.committee_memberships;
    ANALYZE senate.lobbying_registrations;
    ANALYZE senate.lobbying_reports;
    ANALYZE analysis.member_party_unity;
    ANALYZE analysis.bipartisan_votes;

    RAISE NOTICE 'Table statistics refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Create monitoring view for slow queries
CREATE OR REPLACE VIEW metadata.slow_queries AS
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE calls > 10
ORDER BY total_time DESC
LIMIT 50;

COMMENT ON VIEW metadata.slow_queries IS 'Monitor slow queries for performance optimization';

-- Create view for table size monitoring
CREATE OR REPLACE VIEW metadata.table_sizes AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname IN ('congress', 'senate', 'analysis', 'metadata')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

COMMENT ON VIEW metadata.table_sizes IS 'Monitor table sizes for storage optimization';