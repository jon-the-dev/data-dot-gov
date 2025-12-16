-- Congressional Transparency Platform Database Schema
-- PostgreSQL 15+ with optimizations for read-heavy queries

-- Create schemas for logical separation
CREATE SCHEMA IF NOT EXISTS congress;
CREATE SCHEMA IF NOT EXISTS senate;
CREATE SCHEMA IF NOT EXISTS analysis;
CREATE SCHEMA IF NOT EXISTS metadata;

-- Set search path to include all schemas
SET search_path = congress, senate, analysis, metadata, public;

-- ============================================================================
-- CONGRESS SCHEMA: Core congressional data
-- ============================================================================

-- Congressional sessions and metadata
CREATE TABLE congress.sessions (
    congress_number INTEGER PRIMARY KEY,
    start_date DATE NOT NULL,
    end_date DATE,
    session_type VARCHAR(20) DEFAULT 'regular',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Congressional members with historical data
CREATE TABLE congress.members (
    bioguide_id VARCHAR(10) PRIMARY KEY,
    name TEXT NOT NULL,
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    suffix VARCHAR(20),
    party VARCHAR(20) NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    state_name VARCHAR(50) NOT NULL,
    chamber VARCHAR(10) NOT NULL CHECK (chamber IN ('house', 'senate')),
    district INTEGER, -- NULL for senators
    current_member BOOLEAN DEFAULT true,
    image_url TEXT,
    official_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Member terms (historical service periods)
CREATE TABLE congress.member_terms (
    id SERIAL PRIMARY KEY,
    bioguide_id VARCHAR(10) NOT NULL REFERENCES congress.members(bioguide_id),
    congress_number INTEGER NOT NULL,
    chamber VARCHAR(10) NOT NULL CHECK (chamber IN ('house', 'senate')),
    state_code VARCHAR(2) NOT NULL,
    district INTEGER, -- NULL for senators
    start_date DATE NOT NULL,
    end_date DATE,
    member_type VARCHAR(50),
    party VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bioguide_id, congress_number, chamber)
);

-- Bills and legislation
CREATE TABLE congress.bills (
    bill_id VARCHAR(20) PRIMARY KEY, -- e.g., '118_HR_82'
    congress_number INTEGER NOT NULL,
    bill_type VARCHAR(10) NOT NULL, -- HR, S, HJRES, SJRES, etc.
    bill_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    short_title TEXT,
    introduced_date DATE NOT NULL,
    origin_chamber VARCHAR(10) NOT NULL,
    sponsor_bioguide_id VARCHAR(10) REFERENCES congress.members(bioguide_id),
    policy_area TEXT,
    latest_action_date DATE,
    latest_action_text TEXT,
    became_law BOOLEAN DEFAULT false,
    law_number VARCHAR(20),
    law_type VARCHAR(50),
    constitutional_authority_text TEXT,
    summary TEXT,
    cbo_cost_estimate_url TEXT,
    legislation_url TEXT,
    actions_count INTEGER DEFAULT 0,
    amendments_count INTEGER DEFAULT 0,
    committees_count INTEGER DEFAULT 0,
    cosponsors_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(congress_number, bill_type, bill_number)
);

-- Bill subjects and topics
CREATE TABLE congress.bill_subjects (
    id SERIAL PRIMARY KEY,
    bill_id VARCHAR(20) NOT NULL REFERENCES congress.bills(bill_id),
    subject TEXT NOT NULL,
    subject_type VARCHAR(50), -- policy area, legislative subject, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bill_id, subject)
);

-- Bill sponsors and cosponsors
CREATE TABLE congress.bill_sponsors (
    id SERIAL PRIMARY KEY,
    bill_id VARCHAR(20) NOT NULL REFERENCES congress.bills(bill_id),
    bioguide_id VARCHAR(10) NOT NULL REFERENCES congress.members(bioguide_id),
    sponsor_type VARCHAR(20) NOT NULL CHECK (sponsor_type IN ('sponsor', 'cosponsor')),
    sponsorship_date DATE,
    withdrawn_date DATE,
    is_original_cosponsor BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bill_id, bioguide_id)
);

-- Votes (House and Senate)
CREATE TABLE congress.votes (
    vote_id VARCHAR(50) PRIMARY KEY, -- e.g., '118_house_367'
    congress_number INTEGER NOT NULL,
    session INTEGER NOT NULL,
    chamber VARCHAR(10) NOT NULL CHECK (chamber IN ('house', 'senate')),
    roll_call_number INTEGER NOT NULL,
    vote_date DATE NOT NULL,
    vote_time TIME,
    question TEXT NOT NULL,
    description TEXT,
    vote_type VARCHAR(50),
    result VARCHAR(20) NOT NULL,
    bill_id VARCHAR(20) REFERENCES congress.bills(bill_id),
    amendment_number TEXT,
    total_votes INTEGER,
    yea_votes INTEGER DEFAULT 0,
    nay_votes INTEGER DEFAULT 0,
    present_votes INTEGER DEFAULT 0,
    not_voting INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(congress_number, chamber, roll_call_number, session)
);

-- Individual member vote positions
CREATE TABLE congress.member_votes (
    id SERIAL PRIMARY KEY,
    vote_id VARCHAR(50) NOT NULL REFERENCES congress.votes(vote_id),
    bioguide_id VARCHAR(10) NOT NULL REFERENCES congress.members(bioguide_id),
    vote_position VARCHAR(20) NOT NULL CHECK (vote_position IN ('Yea', 'Nay', 'Present', 'Not Voting')),
    voted_with_party BOOLEAN,
    vote_cast_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(vote_id, bioguide_id)
);

-- Committees
CREATE TABLE congress.committees (
    committee_code VARCHAR(10) PRIMARY KEY,
    name TEXT NOT NULL,
    chamber VARCHAR(10) NOT NULL CHECK (chamber IN ('house', 'senate', 'joint')),
    committee_type VARCHAR(50),
    parent_committee_code VARCHAR(10) REFERENCES congress.committees(committee_code),
    is_subcommittee BOOLEAN DEFAULT false,
    url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Committee memberships
CREATE TABLE congress.committee_memberships (
    id SERIAL PRIMARY KEY,
    bioguide_id VARCHAR(10) NOT NULL REFERENCES congress.members(bioguide_id),
    committee_code VARCHAR(10) NOT NULL REFERENCES congress.committees(committee_code),
    congress_number INTEGER NOT NULL,
    rank_in_party INTEGER,
    role VARCHAR(50), -- Chair, Ranking Member, Member
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bioguide_id, committee_code, congress_number)
);

-- Bill-Committee relationships
CREATE TABLE congress.bill_committees (
    id SERIAL PRIMARY KEY,
    bill_id VARCHAR(20) NOT NULL REFERENCES congress.bills(bill_id),
    committee_code VARCHAR(10) NOT NULL REFERENCES congress.committees(committee_code),
    activity_type VARCHAR(50), -- referred, reported, etc.
    activity_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bill_id, committee_code, activity_type)
);

-- ============================================================================
-- SENATE SCHEMA: Senate-specific data (lobbying, etc.)
-- ============================================================================

-- Lobbying registrations (LD-1 forms)
CREATE TABLE senate.lobbying_registrations (
    id SERIAL PRIMARY KEY,
    filing_uuid VARCHAR(100) UNIQUE,
    filing_date DATE NOT NULL,
    registrant_name TEXT NOT NULL,
    registrant_address TEXT,
    client_name TEXT NOT NULL,
    client_address TEXT,
    contact_name TEXT,
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    registration_type VARCHAR(50),
    affiliated_organizations TEXT[],
    foreign_entity_info JSONB,
    effective_date DATE,
    termination_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lobbying quarterly reports (LD-2 forms)
CREATE TABLE senate.lobbying_reports (
    id SERIAL PRIMARY KEY,
    filing_uuid VARCHAR(100) UNIQUE,
    registration_id INTEGER REFERENCES senate.lobbying_registrations(id),
    filing_date DATE NOT NULL,
    reporting_period_start DATE NOT NULL,
    reporting_period_end DATE NOT NULL,
    income_amount DECIMAL(15,2),
    expense_amount DECIMAL(15,2),
    terminated BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lobbying issues and activities
CREATE TABLE senate.lobbying_issues (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES senate.lobbying_reports(id),
    issue_code VARCHAR(10),
    specific_issue TEXT NOT NULL,
    houses_and_agencies TEXT[],
    foreign_entity_involvement BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lobbyist information
CREATE TABLE senate.lobbyists (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    suffix VARCHAR(20),
    covered_position TEXT,
    new_lobbyist BOOLEAN DEFAULT false,
    registrant_name TEXT,
    client_name TEXT,
    filing_year INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(first_name, last_name, registrant_name, client_name, filing_year)
);

-- ============================================================================
-- ANALYSIS SCHEMA: Computed metrics and aggregations
-- ============================================================================

-- Bill categories (topics)
CREATE TABLE analysis.bill_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    keywords TEXT[],
    committee_codes VARCHAR(10)[],
    policy_areas TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bill-category mappings
CREATE TABLE analysis.bill_category_mappings (
    bill_id VARCHAR(20) NOT NULL REFERENCES congress.bills(bill_id),
    category_id INTEGER NOT NULL REFERENCES analysis.bill_categories(id),
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    classification_method VARCHAR(50), -- keyword, committee, ml, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (bill_id, category_id)
);

-- Member party unity scores
CREATE TABLE analysis.member_party_unity (
    id SERIAL PRIMARY KEY,
    bioguide_id VARCHAR(10) NOT NULL REFERENCES congress.members(bioguide_id),
    congress_number INTEGER NOT NULL,
    total_votes INTEGER NOT NULL,
    party_line_votes INTEGER NOT NULL,
    unity_score DECIMAL(5,2) NOT NULL, -- percentage 0.00 to 100.00
    rank_in_party INTEGER,
    rank_in_chamber INTEGER,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bioguide_id, congress_number)
);

-- Bipartisan vote analysis
CREATE TABLE analysis.bipartisan_votes (
    vote_id VARCHAR(50) NOT NULL REFERENCES congress.votes(vote_id),
    is_bipartisan BOOLEAN NOT NULL,
    party_split_score DECIMAL(5,2), -- measure of how split parties were
    democratic_support_pct DECIMAL(5,2),
    republican_support_pct DECIMAL(5,2),
    independent_support_pct DECIMAL(5,2),
    crossover_democrats INTEGER DEFAULT 0,
    crossover_republicans INTEGER DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (vote_id)
);

-- State delegation analysis
CREATE TABLE analysis.state_delegation_patterns (
    id SERIAL PRIMARY KEY,
    state_code VARCHAR(2) NOT NULL,
    congress_number INTEGER NOT NULL,
    democratic_members INTEGER DEFAULT 0,
    republican_members INTEGER DEFAULT 0,
    independent_members INTEGER DEFAULT 0,
    unity_score DECIMAL(5,2), -- how often delegation votes together
    partisan_index DECIMAL(5,2), -- measure of partisan behavior
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(state_code, congress_number)
);

-- ============================================================================
-- METADATA SCHEMA: System metadata and tracking
-- ============================================================================

-- Data source tracking
CREATE TABLE metadata.data_sources (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    source_url TEXT,
    api_version VARCHAR(20),
    rate_limit_per_hour INTEGER,
    terms_of_service_url TEXT,
    data_citation_required BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Migration tracking
CREATE TABLE metadata.migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_time_ms INTEGER,
    records_migrated INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    checksum VARCHAR(64)
);

-- Data freshness tracking
CREATE TABLE metadata.data_freshness (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    schema_name VARCHAR(50) NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL,
    record_count INTEGER,
    data_source_id INTEGER REFERENCES metadata.data_sources(id),
    update_frequency_hours INTEGER, -- expected update frequency
    is_stale BOOLEAN GENERATED ALWAYS AS (
        CASE
            WHEN update_frequency_hours IS NULL THEN false
            ELSE last_updated < NOW() - (update_frequency_hours || ' hours')::INTERVAL
        END
    ) STORED,
    UNIQUE(schema_name, table_name)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Members indexes
CREATE INDEX idx_members_party ON congress.members(party);
CREATE INDEX idx_members_state ON congress.members(state_code);
CREATE INDEX idx_members_chamber ON congress.members(chamber);
CREATE INDEX idx_members_current ON congress.members(current_member) WHERE current_member = true;

-- Member terms indexes
CREATE INDEX idx_member_terms_congress ON congress.member_terms(congress_number);
CREATE INDEX idx_member_terms_member ON congress.member_terms(bioguide_id);
CREATE INDEX idx_member_terms_chamber ON congress.member_terms(chamber);

-- Bills indexes
CREATE INDEX idx_bills_congress ON congress.bills(congress_number);
CREATE INDEX idx_bills_date ON congress.bills(introduced_date);
CREATE INDEX idx_bills_sponsor ON congress.bills(sponsor_bioguide_id);
CREATE INDEX idx_bills_policy_area ON congress.bills(policy_area);
CREATE INDEX idx_bills_became_law ON congress.bills(became_law) WHERE became_law = true;
CREATE INDEX idx_bills_type ON congress.bills(bill_type);

-- Votes indexes
CREATE INDEX idx_votes_congress ON congress.votes(congress_number);
CREATE INDEX idx_votes_chamber ON congress.votes(chamber);
CREATE INDEX idx_votes_date ON congress.votes(vote_date);
CREATE INDEX idx_votes_bill ON congress.votes(bill_id);

-- Member votes indexes
CREATE INDEX idx_member_votes_member ON congress.member_votes(bioguide_id);
CREATE INDEX idx_member_votes_vote ON congress.member_votes(vote_id);
CREATE INDEX idx_member_votes_position ON congress.member_votes(vote_position);
CREATE INDEX idx_member_votes_party_line ON congress.member_votes(voted_with_party);

-- Bill sponsors indexes
CREATE INDEX idx_bill_sponsors_bill ON congress.bill_sponsors(bill_id);
CREATE INDEX idx_bill_sponsors_member ON congress.bill_sponsors(bioguide_id);
CREATE INDEX idx_bill_sponsors_type ON congress.bill_sponsors(sponsor_type);
CREATE INDEX idx_bill_sponsors_date ON congress.bill_sponsors(sponsorship_date);

-- Committee indexes
CREATE INDEX idx_committees_chamber ON congress.committees(chamber);
CREATE INDEX idx_committees_type ON congress.committees(committee_type);
CREATE INDEX idx_committee_memberships_member ON congress.committee_memberships(bioguide_id);
CREATE INDEX idx_committee_memberships_congress ON congress.committee_memberships(congress_number);

-- Lobbying indexes
CREATE INDEX idx_lobbying_registrations_date ON senate.lobbying_registrations(filing_date);
CREATE INDEX idx_lobbying_registrations_client ON senate.lobbying_registrations(client_name);
CREATE INDEX idx_lobbying_reports_period ON senate.lobbying_reports(reporting_period_start, reporting_period_end);
CREATE INDEX idx_lobbying_issues_code ON senate.lobbying_issues(issue_code);

-- Analysis indexes
CREATE INDEX idx_party_unity_congress ON analysis.member_party_unity(congress_number);
CREATE INDEX idx_party_unity_score ON analysis.member_party_unity(unity_score);
CREATE INDEX idx_bipartisan_votes_bipartisan ON analysis.bipartisan_votes(is_bipartisan);
CREATE INDEX idx_bill_categories_name ON analysis.bill_categories(name);

-- Composite indexes for common queries
CREATE INDEX idx_member_votes_member_congress ON congress.member_votes(bioguide_id, vote_id);
CREATE INDEX idx_bills_congress_type ON congress.bills(congress_number, bill_type);
CREATE INDEX idx_votes_congress_chamber ON congress.votes(congress_number, chamber);

-- ============================================================================
-- CONSTRAINTS AND TRIGGERS
-- ============================================================================

-- Update timestamps trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to relevant tables
CREATE TRIGGER update_members_updated_at BEFORE UPDATE ON congress.members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON congress.bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_votes_updated_at BEFORE UPDATE ON congress.votes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_committees_updated_at BEFORE UPDATE ON congress.committees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lobbying_registrations_updated_at BEFORE UPDATE ON senate.lobbying_registrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lobbying_reports_updated_at BEFORE UPDATE ON senate.lobbying_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Check constraints
ALTER TABLE congress.member_party_unity ADD CONSTRAINT check_unity_score_range
    CHECK (unity_score >= 0.00 AND unity_score <= 100.00);

ALTER TABLE analysis.bipartisan_votes ADD CONSTRAINT check_support_pct_range
    CHECK (democratic_support_pct >= 0.00 AND democratic_support_pct <= 100.00 AND
           republican_support_pct >= 0.00 AND republican_support_pct <= 100.00 AND
           independent_support_pct >= 0.00 AND independent_support_pct <= 100.00);

-- ============================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- ============================================================================

-- Party unity summary by congress
CREATE MATERIALIZED VIEW analysis.party_unity_summary AS
SELECT
    congress_number,
    party,
    COUNT(*) as member_count,
    AVG(unity_score) as avg_unity_score,
    MIN(unity_score) as min_unity_score,
    MAX(unity_score) as max_unity_score,
    STDDEV(unity_score) as unity_score_stddev
FROM analysis.member_party_unity mpu
JOIN congress.members m ON mpu.bioguide_id = m.bioguide_id
GROUP BY congress_number, party;

CREATE UNIQUE INDEX idx_party_unity_summary_unique ON analysis.party_unity_summary(congress_number, party);

-- Bill success rates by party and category
CREATE MATERIALIZED VIEW analysis.bill_success_by_party_category AS
SELECT
    b.congress_number,
    m.party as sponsor_party,
    bc.name as category_name,
    COUNT(*) as total_bills,
    COUNT(*) FILTER (WHERE b.became_law = true) as bills_became_law,
    ROUND(
        COUNT(*) FILTER (WHERE b.became_law = true) * 100.0 / COUNT(*), 2
    ) as success_rate_pct
FROM congress.bills b
JOIN congress.members m ON b.sponsor_bioguide_id = m.bioguide_id
JOIN analysis.bill_category_mappings bcm ON b.bill_id = bcm.bill_id
JOIN analysis.bill_categories bc ON bcm.category_id = bc.id
GROUP BY b.congress_number, m.party, bc.name
HAVING COUNT(*) >= 5; -- Only include categories with at least 5 bills

CREATE INDEX idx_bill_success_congress_party ON analysis.bill_success_by_party_category(congress_number, sponsor_party);

-- Bipartisan cooperation trends
CREATE MATERIALIZED VIEW analysis.bipartisan_trends AS
SELECT
    DATE_TRUNC('month', v.vote_date) as month,
    v.congress_number,
    v.chamber,
    COUNT(*) as total_votes,
    COUNT(*) FILTER (WHERE bv.is_bipartisan = true) as bipartisan_votes,
    ROUND(
        COUNT(*) FILTER (WHERE bv.is_bipartisan = true) * 100.0 / COUNT(*), 2
    ) as bipartisan_pct
FROM congress.votes v
JOIN analysis.bipartisan_votes bv ON v.vote_id = bv.vote_id
GROUP BY DATE_TRUNC('month', v.vote_date), v.congress_number, v.chamber
ORDER BY month, congress_number, chamber;

CREATE INDEX idx_bipartisan_trends_month ON analysis.bipartisan_trends(month);

-- State delegation effectiveness
CREATE MATERIALIZED VIEW analysis.state_effectiveness AS
SELECT
    m.state_code,
    m.state_name,
    b.congress_number,
    COUNT(DISTINCT m.bioguide_id) as delegation_size,
    COUNT(DISTINCT b.bill_id) as bills_sponsored,
    COUNT(DISTINCT b.bill_id) FILTER (WHERE b.became_law = true) as laws_enacted,
    ROUND(
        COUNT(DISTINCT b.bill_id) FILTER (WHERE b.became_law = true) * 100.0 /
        NULLIF(COUNT(DISTINCT b.bill_id), 0), 2
    ) as legislative_success_rate
FROM congress.members m
LEFT JOIN congress.bills b ON m.bioguide_id = b.sponsor_bioguide_id
GROUP BY m.state_code, m.state_name, b.congress_number
ORDER BY m.state_code, b.congress_number;

CREATE INDEX idx_state_effectiveness_state ON analysis.state_effectiveness(state_code, congress_number);

-- Committee activity summary
CREATE MATERIALIZED VIEW analysis.committee_activity AS
SELECT
    c.committee_code,
    c.name as committee_name,
    c.chamber,
    bc.congress_number,
    COUNT(DISTINCT bc.bill_id) as bills_handled,
    COUNT(DISTINCT bc.bill_id) FILTER (WHERE b.became_law = true) as bills_became_law,
    COUNT(DISTINCT cm.bioguide_id) as member_count,
    ROUND(
        COUNT(DISTINCT bc.bill_id) FILTER (WHERE b.became_law = true) * 100.0 /
        NULLIF(COUNT(DISTINCT bc.bill_id), 0), 2
    ) as success_rate_pct
FROM congress.committees c
LEFT JOIN congress.bill_committees bc ON c.committee_code = bc.committee_code
LEFT JOIN congress.bills b ON bc.bill_id = b.bill_id
LEFT JOIN congress.committee_memberships cm ON c.committee_code = cm.committee_code
    AND cm.congress_number = bc.congress_number
GROUP BY c.committee_code, c.name, c.chamber, bc.congress_number
ORDER BY c.chamber, c.committee_code, bc.congress_number;

CREATE INDEX idx_committee_activity_committee ON analysis.committee_activity(committee_code, congress_number);

-- Refresh materialized views function
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY analysis.party_unity_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY analysis.bill_success_by_party_category;
    REFRESH MATERIALIZED VIEW CONCURRENTLY analysis.bipartisan_trends;
    REFRESH MATERIALIZED VIEW CONCURRENTLY analysis.state_effectiveness;
    REFRESH MATERIALIZED VIEW CONCURRENTLY analysis.committee_activity;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA SETUP
-- ============================================================================

-- Insert common bill categories
INSERT INTO analysis.bill_categories (name, description, keywords) VALUES
('Healthcare', 'Healthcare policy, medical research, public health', ARRAY['health', 'medical', 'medicare', 'medicaid', 'hospital', 'doctor', 'patient', 'disease']),
('Defense & Military', 'Defense spending, military operations, veterans affairs', ARRAY['defense', 'military', 'veteran', 'armed forces', 'army', 'navy', 'air force', 'pentagon']),
('Technology & Innovation', 'Technology policy, innovation, research and development', ARRAY['technology', 'innovation', 'research', 'development', 'cyber', 'digital', 'internet', 'ai']),
('Education', 'Education policy, student aid, school funding', ARRAY['education', 'school', 'student', 'teacher', 'university', 'college', 'academic']),
('Environment & Energy', 'Environmental protection, energy policy, climate change', ARRAY['environment', 'energy', 'climate', 'pollution', 'renewable', 'oil', 'gas', 'carbon']),
('Economy & Finance', 'Economic policy, banking, financial regulation', ARRAY['economy', 'economic', 'bank', 'financial', 'finance', 'budget', 'tax', 'fiscal']),
('Transportation', 'Transportation infrastructure, aviation, maritime', ARRAY['transport', 'highway', 'aviation', 'railroad', 'maritime', 'infrastructure', 'bridge']),
('Agriculture', 'Agricultural policy, food safety, rural development', ARRAY['agriculture', 'farm', 'food', 'rural', 'crop', 'livestock', 'agricultural']),
('Immigration', 'Immigration policy, border security, refugee policy', ARRAY['immigration', 'immigrant', 'border', 'refugee', 'visa', 'citizenship', 'asylum']),
('Justice & Crime', 'Criminal justice, law enforcement, civil rights', ARRAY['justice', 'crime', 'police', 'court', 'prison', 'civil rights', 'law enforcement']);

-- Insert data sources
INSERT INTO metadata.data_sources (source_name, source_url, api_version, rate_limit_per_hour, terms_of_service_url) VALUES
('Congress.gov API', 'https://api.congress.gov/', 'v3', 1000, 'https://www.congress.gov/help/terms-of-service'),
('Senate LDA API', 'https://lda.senate.gov/api/', 'v1', 120, 'https://lda.senate.gov/system/public/resources/xml/README.txt');

-- Set up data freshness tracking for key tables
INSERT INTO metadata.data_freshness (table_name, schema_name, last_updated, update_frequency_hours) VALUES
('bills', 'congress', NOW() - INTERVAL '1 day', 24),
('votes', 'congress', NOW() - INTERVAL '1 day', 6),
('members', 'congress', NOW() - INTERVAL '7 days', 168),
('lobbying_registrations', 'senate', NOW() - INTERVAL '1 day', 24),
('lobbying_reports', 'senate', NOW() - INTERVAL '1 day', 24);

-- Grant permissions for application user (to be created)
-- Note: This will be executed after user creation in database_setup.py

-- Comments for documentation
COMMENT ON SCHEMA congress IS 'Core congressional data including members, bills, votes, and committees';
COMMENT ON SCHEMA senate IS 'Senate-specific data including lobbying registrations and reports';
COMMENT ON SCHEMA analysis IS 'Computed analytics and aggregated metrics';
COMMENT ON SCHEMA metadata IS 'System metadata and operational tracking';

COMMENT ON TABLE congress.members IS 'Congressional members with current and historical information';
COMMENT ON TABLE congress.bills IS 'Bills and legislation with full metadata and tracking';
COMMENT ON TABLE congress.votes IS 'Roll call votes from House and Senate';
COMMENT ON TABLE congress.member_votes IS 'Individual member voting positions on each roll call';
COMMENT ON TABLE analysis.member_party_unity IS 'Party loyalty scores for each member by congress';
COMMENT ON TABLE analysis.bipartisan_votes IS 'Analysis of bipartisan cooperation on votes';

-- Performance monitoring view
CREATE VIEW metadata.performance_metrics AS
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY schemaname, tablename;

COMMENT ON VIEW metadata.performance_metrics IS 'Table performance and maintenance statistics';