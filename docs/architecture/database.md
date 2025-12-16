# Database Setup and Migration Guide

This guide covers the PostgreSQL database setup, migration from JSON files, and ongoing database operations for the Congressional Transparency Platform.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ with pipenv
- Make (for convenient commands)

### Environment Setup

1. **Copy environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies:**
   ```bash
   make install
   # or
   pipenv install
   ```

3. **Start database environment:**
   ```bash
   make db-start
   ```

4. **Complete database setup:**
   ```bash
   make db-full-setup
   ```

## 📊 Database Architecture

### Schema Design

The database uses a multi-schema design optimized for congressional data:

- **`congress`**: Core congressional data (members, bills, votes, committees)
- **`senate`**: Senate-specific data (lobbying registrations and reports)
- **`analysis`**: Computed metrics and aggregated analytics
- **`metadata`**: System metadata, migrations, and operational tracking

### Key Features

✅ **Optimized for Read-Heavy Queries**: Extensive indexing and materialized views
✅ **ACID Compliance**: Full transaction support with rollback capabilities
✅ **Horizontal Scalability**: Designed for future sharding and replication
✅ **Data Integrity**: Comprehensive constraints and foreign key relationships
✅ **Performance Monitoring**: Built-in slow query and table size tracking
✅ **Backup & Recovery**: Automated backup scripts with point-in-time recovery

## 🛠 Database Operations

### Development Environment

```bash
# Start PostgreSQL + Redis
make db-start

# View database logs
make db-logs

# Connect to database shell
make db-shell

# Open pgAdmin (web interface)
make db-admin
# Available at: http://localhost:8080
```

### Schema Management

```bash
# Create initial schema
make db-create-schema

# Drop and recreate schema (destructive!)
make db-drop-schema

# Run migrations
make db-migrate

# Refresh materialized views
make db-refresh-views
```

### Data Migration

```bash
# Migrate all JSON data to PostgreSQL
make db-migrate-data

# Validate migrated data integrity
make db-validate

# Show database statistics
make db-stats

# Complete setup: schema + migration + validation
make db-full-setup
```

### Backup & Restore

```bash
# Create backup
make db-backup

# Restore from backup
make db-restore FILE=backups/congress_transparency_20240922_120000.sql

# Cleanup old backups (keeps last 30 days)
make db-cleanup
```

### Development & Testing

```bash
# Test database connection
make db-test

# Reset database to clean state
make db-reset

# Load sample data for development
make db-sample
```

## 📈 Performance Optimization

### Materialized Views

The database includes several materialized views for common analytics:

- **`analysis.party_unity_summary`**: Party unity scores by congress
- **`analysis.bill_success_by_party_category`**: Bill success rates by party and topic
- **`analysis.bipartisan_trends`**: Bipartisan cooperation trends over time
- **`analysis.state_effectiveness`**: State delegation legislative effectiveness
- **`analysis.committee_activity`**: Committee activity and success rates

Refresh views after major data updates:
```bash
make db-refresh-views
```

### Query Performance

```sql
-- View slow queries
SELECT * FROM metadata.slow_queries;

-- Monitor table sizes
SELECT * FROM metadata.table_sizes;

-- Check database performance
SELECT * FROM metadata.performance_metrics;
```

### Indexes

The schema includes optimized indexes for common query patterns:

- **Composite indexes** for multi-column queries
- **Partial indexes** for filtered queries (e.g., current members only)
- **GIN indexes** for array and text search
- **Function-based indexes** for computed values

## 🔄 Migration Details

### Migration Process

The migration system handles the transfer of JSON data to PostgreSQL with:

1. **Batch Processing**: Configurable batch sizes for memory efficiency
2. **Transaction Safety**: Each batch is a separate transaction with rollback
3. **Parallel Processing**: Multi-threaded migration for performance
4. **Error Recovery**: Automatic retry with exponential backoff
5. **Data Validation**: Comprehensive integrity checks post-migration
6. **Progress Tracking**: Real-time progress monitoring and logging

### Migration Order

Due to foreign key constraints, data is migrated in dependency order:

1. Congress sessions → Members → Member terms
2. Committees → Bills → Bill subjects/sponsors
3. Votes → Member votes → Committee relationships
4. Lobbying registrations → Reports → Issues → Lobbyists
5. Analysis tables → Category mappings

### Configuration

Adjust migration performance via environment variables:

```bash
# Batch size (records per transaction)
MIGRATION_BATCH_SIZE=1000

# Parallel workers
MIGRATION_MAX_WORKERS=4

# Retry configuration
MIGRATION_RETRY_ATTEMPTS=3
MIGRATION_RETRY_DELAY=5
```

## 📊 Data Models

### Core Tables

#### Congress Schema

```sql
-- Members with historical terms
congress.members (440+ records)
congress.member_terms (term history)

-- Bills and legislation
congress.bills (10,000+ records)
congress.bill_subjects (topic classifications)
congress.bill_sponsors (sponsorship relationships)

-- Voting records
congress.votes (vote sessions)
congress.member_votes (individual positions)

-- Committee structure
congress.committees (committees and subcommittees)
congress.committee_memberships (member assignments)
congress.bill_committees (bill committee activities)
```

#### Senate Schema

```sql
-- Lobbying data
senate.lobbying_registrations (LD-1 forms)
senate.lobbying_reports (LD-2 quarterly reports)
senate.lobbying_issues (specific lobbying activities)
senate.lobbyists (individual lobbyist records)
```

#### Analysis Schema

```sql
-- Computed analytics
analysis.bill_categories (topic classifications)
analysis.bill_category_mappings (bill-topic relationships)
analysis.member_party_unity (loyalty scores)
analysis.bipartisan_votes (cooperation analysis)
analysis.state_delegation_patterns (geographic patterns)
```

### Relationships

```
Members (1:N) Member Terms
Members (1:N) Bills (sponsor)
Members (1:N) Member Votes
Members (1:N) Committee Memberships

Bills (1:N) Bill Subjects
Bills (1:N) Bill Sponsors
Bills (1:N) Votes

Votes (1:N) Member Votes
Committees (1:N) Committee Memberships
Committees (1:N) Bill Committees
```

## 🔍 Querying Examples

### Common Queries

```sql
-- Party unity scores for current congress
SELECT m.name, m.party, m.state_code, pu.unity_score
FROM congress.members m
JOIN analysis.member_party_unity pu ON m.bioguide_id = pu.bioguide_id
WHERE pu.congress_number = 118
ORDER BY pu.unity_score DESC;

-- Bipartisan bills by category
SELECT bc.name as category, COUNT(*) as bipartisan_bills
FROM congress.bills b
JOIN analysis.bill_category_mappings bcm ON b.bill_id = bcm.bill_id
JOIN analysis.bill_categories bc ON bcm.category_id = bc.id
JOIN congress.votes v ON b.bill_id = v.bill_id
JOIN analysis.bipartisan_votes bv ON v.vote_id = bv.vote_id
WHERE bv.is_bipartisan = true
GROUP BY bc.name
ORDER BY bipartisan_bills DESC;

-- State delegation effectiveness
SELECT state_code, delegation_size, bills_sponsored,
       legislative_success_rate
FROM analysis.state_effectiveness
WHERE congress_number = 118
ORDER BY legislative_success_rate DESC;

-- Most active committees
SELECT committee_name, chamber, bills_handled, success_rate_pct
FROM analysis.committee_activity
WHERE congress_number = 118
ORDER BY bills_handled DESC;
```

### Performance Queries

```sql
-- Find slow queries
SELECT query, calls, mean_time, total_time
FROM metadata.slow_queries
ORDER BY total_time DESC LIMIT 10;

-- Table sizes and growth
SELECT schemaname, tablename, size, size_bytes
FROM metadata.table_sizes
ORDER BY size_bytes DESC;

-- Index usage statistics
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE schemaname IN ('congress', 'senate', 'analysis')
ORDER BY idx_scan DESC;
```

## 🚨 Troubleshooting

### Common Issues

#### Connection Issues
```bash
# Check if database is running
docker-compose ps postgres

# Check logs for errors
make db-logs

# Test connection
make db-test
```

#### Migration Failures
```bash
# Check migration logs
tail -f database_migration.log

# Validate existing data
make db-validate

# Reset and retry
make db-reset
make db-migrate-data
```

#### Performance Issues
```bash
# Check slow queries
make db-shell
\x
SELECT * FROM metadata.slow_queries LIMIT 5;

# Update table statistics
SELECT refresh_table_statistics();

# Refresh materialized views
make db-refresh-views
```

#### Storage Issues
```bash
# Check table sizes
SELECT * FROM metadata.table_sizes;

# Clean up old backups
make db-cleanup

# Vacuum and analyze
VACUUM ANALYZE;
```

### Recovery Procedures

#### Full Database Recovery
```bash
# Stop database
make db-stop

# Remove corrupted data
rm -rf docker-volumes/postgres

# Restart and restore
make db-start
make db-restore FILE=backups/latest_backup.sql
```

#### Partial Data Recovery
```bash
# Restore specific schema
pg_restore -U congress_app -d congress_transparency \
  --schema=congress --clean backups/backup.sql

# Refresh materialized views
make db-refresh-views
```

## 🔒 Security Considerations

### Development Environment

- Default passwords are for development only
- Change all passwords in production
- Use SSL/TLS for production connections
- Restrict network access appropriately

### Production Recommendations

```sql
-- Create read-only user for analytics
CREATE ROLE congress_readonly;
GRANT USAGE ON SCHEMA congress, senate, analysis TO congress_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA congress, senate, analysis TO congress_readonly;

-- Create backup user
CREATE ROLE congress_backup WITH LOGIN;
GRANT USAGE ON SCHEMA congress, senate, analysis, metadata TO congress_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA congress, senate, analysis, metadata TO congress_backup;
```

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy ORM Guide](https://docs.sqlalchemy.org/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Congressional Data APIs](https://api.congress.gov/)

## 🤝 Contributing

When modifying the database schema:

1. Create migration scripts in `db/migrations/`
2. Update SQLAlchemy models in `database_setup.py`
3. Add appropriate indexes and constraints
4. Update this documentation
5. Test migration on sample data
6. Validate performance impact

## 📞 Support

For database-related issues:

1. Check the troubleshooting section above
2. Review database logs: `make db-logs`
3. Test basic connectivity: `make db-test`
4. Open an issue with relevant logs and error messages