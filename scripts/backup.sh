#!/bin/bash
# PostgreSQL Backup Script for Congressional Transparency Platform

set -e

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="congress_transparency_${DATE}.sql"
RETENTION_DAYS=30

# Database connection (set via environment variables)
DB_HOST=${PGHOST:-postgres}
DB_PORT=${PGPORT:-5432}
DB_NAME=${PGDATABASE:-congress_transparency}
DB_USER=${PGUSER:-congress_app}

echo "Starting backup of database ${DB_NAME} at $(date)"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Create full database backup
pg_dump \
    --host=${DB_HOST} \
    --port=${DB_PORT} \
    --username=${DB_USER} \
    --dbname=${DB_NAME} \
    --format=custom \
    --compress=9 \
    --verbose \
    --file=${BACKUP_DIR}/${BACKUP_FILE}

# Create a text version for easy inspection
pg_dump \
    --host=${DB_HOST} \
    --port=${DB_PORT} \
    --username=${DB_USER} \
    --dbname=${DB_NAME} \
    --format=plain \
    --file=${BACKUP_DIR}/${BACKUP_FILE%.sql}.txt

# Compress the text backup
gzip ${BACKUP_DIR}/${BACKUP_FILE%.sql}.txt

# Create schema-only backup
pg_dump \
    --host=${DB_HOST} \
    --port=${DB_PORT} \
    --username=${DB_USER} \
    --dbname=${DB_NAME} \
    --schema-only \
    --format=plain \
    --file=${BACKUP_DIR}/schema_${DATE}.sql

# Create data-only backup for large tables
pg_dump \
    --host=${DB_HOST} \
    --port=${DB_PORT} \
    --username=${DB_USER} \
    --dbname=${DB_NAME} \
    --data-only \
    --format=custom \
    --compress=9 \
    --table=congress.bills \
    --table=congress.votes \
    --table=congress.member_votes \
    --file=${BACKUP_DIR}/data_only_${DATE}.sql

# Check backup integrity
echo "Verifying backup integrity..."
pg_restore --list ${BACKUP_DIR}/${BACKUP_FILE} > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Backup completed successfully: ${BACKUP_FILE}"

    # Calculate file size
    BACKUP_SIZE=$(du -h ${BACKUP_DIR}/${BACKUP_FILE} | cut -f1)
    echo "Backup size: ${BACKUP_SIZE}"

    # Create checksum
    sha256sum ${BACKUP_DIR}/${BACKUP_FILE} > ${BACKUP_DIR}/${BACKUP_FILE}.sha256

    # Log backup info
    echo "$(date): ${BACKUP_FILE} (${BACKUP_SIZE})" >> ${BACKUP_DIR}/backup.log

else
    echo "❌ Backup verification failed!"
    exit 1
fi

# Cleanup old backups
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find ${BACKUP_DIR} -name "congress_transparency_*.sql" -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR} -name "congress_transparency_*.txt.gz" -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR} -name "schema_*.sql" -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR} -name "data_only_*.sql" -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR} -name "*.sha256" -mtime +${RETENTION_DAYS} -delete

echo "Backup process completed at $(date)"