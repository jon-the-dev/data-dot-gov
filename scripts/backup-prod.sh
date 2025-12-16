#!/bin/bash
# Congressional Transparency Platform - Production Backup Script

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
S3_BUCKET="${S3_BUCKET:-congress-platform-backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_HOST="${PGHOST:-postgres}"
DB_NAME="${PGDATABASE:-congress_transparency}"
DB_USER="${PGUSER:-congress_app}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking backup prerequisites..."

    # Check if backup directory exists
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        log_info "Created backup directory: $BACKUP_DIR"
    fi

    # Check if PostgreSQL client is available
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump not found. PostgreSQL client tools required."
        exit 1
    fi

    # Check if AWS CLI is available (optional)
    if command -v aws &> /dev/null; then
        log_info "AWS CLI found - S3 backup enabled"
    else
        log_warning "AWS CLI not found - S3 backup disabled"
    fi

    # Test database connectivity
    if ! pg_isready -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME"; then
        log_error "Cannot connect to database at $DB_HOST"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Function to create database backup
backup_database() {
    log_info "Creating database backup..."

    local backup_file="$BACKUP_DIR/postgres_${DB_NAME}_${TIMESTAMP}.sql.gz"
    local backup_schema_file="$BACKUP_DIR/postgres_${DB_NAME}_schema_${TIMESTAMP}.sql"

    # Create full database backup
    if pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --clean --create --if-exists \
        --format=custom --compress=9 \
        --file="$backup_file.custom"; then

        log_success "Database custom format backup created: $backup_file.custom"
    else
        log_error "Failed to create database custom backup"
        return 1
    fi

    # Create plain SQL backup (compressed)
    if pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --clean --create --if-exists \
        --format=plain | gzip > "$backup_file"; then

        log_success "Database SQL backup created: $backup_file"
    else
        log_error "Failed to create database SQL backup"
        return 1
    fi

    # Create schema-only backup
    if pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --schema-only --clean --create --if-exists \
        --format=plain --file="$backup_schema_file"; then

        log_success "Database schema backup created: $backup_schema_file"
    else
        log_warning "Failed to create database schema backup"
    fi

    # Get backup file sizes
    local size_custom=$(du -h "$backup_file.custom" | cut -f1)
    local size_sql=$(du -h "$backup_file" | cut -f1)

    log_info "Backup sizes - Custom: $size_custom, SQL: $size_sql"

    echo "$backup_file"
}

# Function to backup application data
backup_application_data() {
    log_info "Creating application data backup..."

    local data_backup_file="$BACKUP_DIR/app_data_${TIMESTAMP}.tar.gz"

    # Backup data directory if it exists
    if [[ -d "/app/data" ]]; then
        if tar -czf "$data_backup_file" -C /app data/; then
            local size=$(du -h "$data_backup_file" | cut -f1)
            log_success "Application data backup created: $data_backup_file ($size)"
            echo "$data_backup_file"
        else
            log_warning "Failed to create application data backup"
        fi
    else
        log_warning "Application data directory not found"
    fi
}

# Function to backup logs
backup_logs() {
    log_info "Creating logs backup..."

    local logs_backup_file="$BACKUP_DIR/logs_${TIMESTAMP}.tar.gz"
    local log_dirs=("/var/log/nginx" "/app/logs" "/var/log/postgresql")

    # Find existing log directories
    local existing_dirs=()
    for dir in "${log_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            existing_dirs+=("$dir")
        fi
    done

    if [[ ${#existing_dirs[@]} -gt 0 ]]; then
        if tar -czf "$logs_backup_file" "${existing_dirs[@]}" 2>/dev/null; then
            local size=$(du -h "$logs_backup_file" | cut -f1)
            log_success "Logs backup created: $logs_backup_file ($size)"
            echo "$logs_backup_file"
        else
            log_warning "Failed to create logs backup"
        fi
    else
        log_warning "No log directories found to backup"
    fi
}

# Function to upload to S3
upload_to_s3() {
    local file="$1"

    if ! command -v aws &> /dev/null; then
        log_warning "AWS CLI not available, skipping S3 upload for $file"
        return 0
    fi

    if [[ -z "${AWS_ACCESS_KEY_ID:-}" ]] || [[ -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
        log_warning "AWS credentials not set, skipping S3 upload for $file"
        return 0
    fi

    log_info "Uploading $(basename "$file") to S3..."

    local s3_key="congress-platform/$(date +%Y/%m/%d)/$(basename "$file")"

    if aws s3 cp "$file" "s3://$S3_BUCKET/$s3_key" \
        --storage-class STANDARD_IA \
        --metadata "backup-timestamp=$TIMESTAMP,backup-type=automated"; then

        log_success "Uploaded to S3: s3://$S3_BUCKET/$s3_key"

        # Add lifecycle tag
        aws s3api put-object-tagging \
            --bucket "$S3_BUCKET" \
            --key "$s3_key" \
            --tagging "TagSet=[{Key=backup-type,Value=automated},{Key=retention-days,Value=$RETENTION_DAYS}]" \
            2>/dev/null || log_warning "Failed to add tags to S3 object"
    else
        log_error "Failed to upload to S3: $file"
        return 1
    fi
}

# Function to clean up old backups
cleanup_old_backups() {
    log_info "Cleaning up local backups older than $RETENTION_DAYS days..."

    # Clean up local backups
    if find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null; then
        log_info "Cleaned up old local SQL backups"
    fi

    if find "$BACKUP_DIR" -name "*.custom" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null; then
        log_info "Cleaned up old local custom backups"
    fi

    if find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null; then
        log_info "Cleaned up old local archive backups"
    fi

    # Clean up S3 backups (if AWS CLI available)
    if command -v aws &> /dev/null && [[ -n "${AWS_ACCESS_KEY_ID:-}" ]]; then
        log_info "Cleaning up S3 backups older than $RETENTION_DAYS days..."

        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)

        aws s3api list-objects-v2 \
            --bucket "$S3_BUCKET" \
            --prefix "congress-platform/" \
            --query "Contents[?LastModified<'$cutoff_date'].Key" \
            --output text 2>/dev/null | while read -r key; do
                if [[ -n "$key" && "$key" != "None" ]]; then
                    aws s3 rm "s3://$S3_BUCKET/$key" && \
                        log_info "Deleted old S3 backup: $key"
                fi
            done || log_warning "Failed to clean up S3 backups"
    fi

    log_success "Cleanup completed"
}

# Function to verify backup integrity
verify_backup() {
    local backup_file="$1"

    log_info "Verifying backup integrity: $(basename "$backup_file")"

    if [[ "$backup_file" == *.sql.gz ]]; then
        # Verify gzip integrity
        if gzip -t "$backup_file" 2>/dev/null; then
            log_success "Backup file integrity verified"
        else
            log_error "Backup file is corrupted: $backup_file"
            return 1
        fi
    elif [[ "$backup_file" == *.custom ]]; then
        # Verify pg_dump custom format
        if pg_restore --list "$backup_file" >/dev/null 2>&1; then
            log_success "Custom backup format verified"
        else
            log_error "Custom backup is corrupted: $backup_file"
            return 1
        fi
    fi
}

# Function to create backup manifest
create_manifest() {
    local manifest_file="$BACKUP_DIR/backup_manifest_${TIMESTAMP}.json"

    log_info "Creating backup manifest..."

    cat > "$manifest_file" << EOF
{
  "backup_timestamp": "$TIMESTAMP",
  "backup_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "database": {
    "host": "$DB_HOST",
    "name": "$DB_NAME",
    "user": "$DB_USER"
  },
  "retention_days": $RETENTION_DAYS,
  "s3_bucket": "$S3_BUCKET",
  "files": [
EOF

    # Add backup files to manifest
    local files=()
    for file in "$BACKUP_DIR"/*_${TIMESTAMP}.*; do
        if [[ -f "$file" ]]; then
            local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "unknown")
            local checksum=$(sha256sum "$file" 2>/dev/null | cut -d' ' -f1 || echo "unknown")

            files+=("    {")
            files+=("      \"filename\": \"$(basename "$file")\",")
            files+=("      \"size_bytes\": $size,")
            files+=("      \"sha256\": \"$checksum\"")
            files+=("    }")
        fi
    done

    # Join array elements with commas
    printf '%s\n' "${files[@]}" | sed '$!s/$/,/' >> "$manifest_file"

    cat >> "$manifest_file" << EOF
  ]
}
EOF

    log_success "Backup manifest created: $manifest_file"
    echo "$manifest_file"
}

# Function to send notification
send_notification() {
    local status="$1"
    local message="$2"

    # Log the notification
    if [[ "$status" == "success" ]]; then
        log_success "$message"
    else
        log_error "$message"
    fi

    # Send Slack notification if webhook is configured
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="good"
        [[ "$status" != "success" ]] && color="danger"

        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"Congressional Transparency Platform Backup\",
                    \"text\": \"$message\",
                    \"ts\": $(date +%s)
                }]
            }" 2>/dev/null || log_warning "Failed to send Slack notification"
    fi
}

# Main backup function
main() {
    local action="${1:-backup}"

    case "$action" in
        "backup")
            log_info "Starting Congressional Transparency Platform backup..."

            check_prerequisites

            # Create backups
            local backup_files=()

            if db_backup=$(backup_database); then
                backup_files+=("$db_backup")
                backup_files+=("$db_backup.custom")
                verify_backup "$db_backup"
                verify_backup "$db_backup.custom"
            fi

            if data_backup=$(backup_application_data); then
                backup_files+=("$data_backup")
            fi

            if logs_backup=$(backup_logs); then
                backup_files+=("$logs_backup")
            fi

            # Create manifest
            if manifest=$(create_manifest); then
                backup_files+=("$manifest")
            fi

            # Upload to S3
            for file in "${backup_files[@]}"; do
                if [[ -f "$file" ]]; then
                    upload_to_s3 "$file"
                fi
            done

            # Clean up old backups
            cleanup_old_backups

            # Send success notification
            send_notification "success" "Backup completed successfully with ${#backup_files[@]} files"

            log_success "Backup process completed successfully!"
            ;;

        "restore")
            log_error "Restore functionality not implemented in this script"
            log_info "To restore from backup:"
            log_info "1. Stop the application containers"
            log_info "2. Use pg_restore with the .custom backup file"
            log_info "3. Extract and restore application data if needed"
            log_info "4. Restart the application"
            exit 1
            ;;

        "verify")
            log_info "Verifying latest backups..."
            for file in "$BACKUP_DIR"/*.sql.gz "$BACKUP_DIR"/*.custom; do
                if [[ -f "$file" ]]; then
                    verify_backup "$file"
                fi
            done
            ;;

        "cleanup")
            cleanup_old_backups
            ;;

        *)
            echo "Usage: $0 [backup|restore|verify|cleanup]"
            echo "  backup  - Create full backup (default)"
            echo "  restore - Show restore instructions"
            echo "  verify  - Verify backup integrity"
            echo "  cleanup - Clean up old backups"
            exit 1
            ;;
    esac
}

# Trap for cleanup on script interruption
trap 'log_error "Backup interrupted!"; exit 1' INT TERM

# Run main function with all arguments
main "$@"