#!/bin/bash
# Congressional Transparency Platform - Production Restore Script

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
S3_BUCKET="${S3_BUCKET:-congress-platform-backups}"
DB_HOST="${PGHOST:-postgres}"
DB_NAME="${PGDATABASE:-congress_transparency}"
DB_USER="${PGUSER:-congress_app}"
RESTORE_TIMESTAMP=""

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] COMMAND"
    echo
    echo "Commands:"
    echo "  list                    List available backups"
    echo "  restore TIMESTAMP       Restore from specific backup timestamp"
    echo "  restore-latest          Restore from most recent backup"
    echo "  download TIMESTAMP      Download backup from S3"
    echo "  verify TIMESTAMP        Verify backup integrity"
    echo
    echo "Options:"
    echo "  -h, --help             Show this help message"
    echo "  -f, --force            Force restore without confirmation"
    echo "  -d, --data-only        Restore data only (no schema changes)"
    echo "  -s, --schema-only      Restore schema only (no data)"
    echo "  --from-s3              Download backup from S3 before restore"
    echo
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 restore 20241201_143022"
    echo "  $0 restore-latest --force"
    echo "  $0 download 20241201_143022 --from-s3"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking restore prerequisites..."

    # Check if PostgreSQL client is available
    if ! command -v pg_restore &> /dev/null || ! command -v psql &> /dev/null; then
        log_error "PostgreSQL client tools not found (pg_restore, psql required)"
        exit 1
    fi

    # Check if backup directory exists
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        log_info "Created backup directory: $BACKUP_DIR"
    fi

    # Test database connectivity
    if ! pg_isready -h "$DB_HOST" -U "$DB_USER" -q; then
        log_error "Cannot connect to database at $DB_HOST"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Function to list available backups
list_backups() {
    log_info "Available local backups:"

    if ls "$BACKUP_DIR"/*.custom >/dev/null 2>&1; then
        echo
        echo "Local backups:"
        for backup in "$BACKUP_DIR"/*.custom; do
            local timestamp=$(basename "$backup" | sed 's/.*_\([0-9]*_[0-9]*\)\.custom/\1/')
            local size=$(du -h "$backup" | cut -f1)
            local date=$(echo "$timestamp" | sed 's/_/ /' | xargs -I {} date -d "{}" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "Invalid date")
            echo "  $timestamp - $size - $date"
        done
    else
        echo "  No local backups found"
    fi

    # List S3 backups if AWS CLI is available
    if command -v aws &> /dev/null && [[ -n "${AWS_ACCESS_KEY_ID:-}" ]]; then
        log_info "Checking S3 backups..."
        echo
        echo "S3 backups:"

        aws s3 ls "s3://$S3_BUCKET/congress-platform/" --recursive 2>/dev/null | \
        grep "\.custom$" | \
        sort -r | \
        head -20 | \
        while read -r line; do
            local file=$(echo "$line" | awk '{print $4}')
            local size=$(echo "$line" | awk '{print $3}')
            local date=$(echo "$line" | awk '{print $1, $2}')
            local timestamp=$(basename "$file" | sed 's/.*_\([0-9]*_[0-9]*\)\.custom/\1/')
            echo "  $timestamp - ${size}B - $date (S3)"
        done || echo "  No S3 backups found or access denied"
    fi
}

# Function to download backup from S3
download_from_s3() {
    local timestamp="$1"

    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not available for S3 download"
        return 1
    fi

    if [[ -z "${AWS_ACCESS_KEY_ID:-}" ]] || [[ -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
        log_error "AWS credentials not set"
        return 1
    fi

    log_info "Downloading backup from S3: $timestamp"

    # Find the backup file in S3
    local s3_files=(
        "postgres_${DB_NAME}_${timestamp}.custom"
        "app_data_${timestamp}.tar.gz"
        "logs_${timestamp}.tar.gz"
        "backup_manifest_${timestamp}.json"
    )

    for file in "${s3_files[@]}"; do
        local s3_key=$(aws s3 ls "s3://$S3_BUCKET/congress-platform/" --recursive 2>/dev/null | \
                      grep "$file" | \
                      head -1 | \
                      awk '{print $4}')

        if [[ -n "$s3_key" ]]; then
            log_info "Downloading $file from S3..."
            if aws s3 cp "s3://$S3_BUCKET/$s3_key" "$BACKUP_DIR/$file"; then
                log_success "Downloaded: $file"
            else
                log_warning "Failed to download: $file"
            fi
        else
            log_warning "File not found in S3: $file"
        fi
    done
}

# Function to verify backup integrity
verify_backup() {
    local timestamp="$1"
    local backup_file="$BACKUP_DIR/postgres_${DB_NAME}_${timestamp}.custom"

    log_info "Verifying backup integrity: $timestamp"

    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    # Verify pg_dump custom format
    if pg_restore --list "$backup_file" >/dev/null 2>&1; then
        log_success "Backup integrity verified"

        # Show backup contents summary
        local table_count=$(pg_restore --list "$backup_file" | grep "TABLE DATA" | wc -l)
        local size=$(du -h "$backup_file" | cut -f1)

        log_info "Backup contains $table_count tables, size: $size"
        return 0
    else
        log_error "Backup file is corrupted or invalid"
        return 1
    fi
}

# Function to get confirmation
get_confirmation() {
    local message="$1"
    local force="${2:-false}"

    if [[ "$force" == "true" ]]; then
        log_warning "Force mode enabled - skipping confirmation"
        return 0
    fi

    echo
    log_warning "$message"
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirmation

    if [[ "$confirmation" != "yes" ]]; then
        log_info "Operation cancelled by user"
        exit 0
    fi
}

# Function to stop application services
stop_application() {
    log_info "Stopping application services..."

    local compose_file="$1"

    if [[ -f "$compose_file" ]]; then
        # Stop application containers but keep database running
        docker-compose -f "$compose_file" stop frontend backend data-fetcher 2>/dev/null || {
            log_warning "Some services were not running"
        }
    else
        log_warning "Compose file not found: $compose_file"
    fi

    log_success "Application services stopped"
}

# Function to start application services
start_application() {
    log_info "Starting application services..."

    local compose_file="$1"

    if [[ -f "$compose_file" ]]; then
        docker-compose -f "$compose_file" up -d frontend backend data-fetcher 2>/dev/null || {
            log_warning "Failed to start some services"
        }
    else
        log_warning "Compose file not found: $compose_file"
    fi

    log_success "Application services started"
}

# Function to restore database
restore_database() {
    local timestamp="$1"
    local data_only="${2:-false}"
    local schema_only="${3:-false}"

    local backup_file="$BACKUP_DIR/postgres_${DB_NAME}_${timestamp}.custom"

    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    log_info "Restoring database from: $backup_file"

    # Prepare restore options
    local restore_options=()
    restore_options+=("--host=$DB_HOST")
    restore_options+=("--username=$DB_USER")
    restore_options+=("--dbname=$DB_NAME")
    restore_options+=("--verbose")
    restore_options+=("--clean")
    restore_options+=("--if-exists")
    restore_options+=("--no-owner")
    restore_options+=("--no-privileges")

    if [[ "$data_only" == "true" ]]; then
        restore_options+=("--data-only")
        log_info "Restoring data only (no schema changes)"
    elif [[ "$schema_only" == "true" ]]; then
        restore_options+=("--schema-only")
        log_info "Restoring schema only (no data)"
    fi

    # Create a pre-restore backup
    log_info "Creating pre-restore backup..."
    local pre_restore_backup="$BACKUP_DIR/pre_restore_$(date +%Y%m%d_%H%M%S).custom"
    if pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" \
        --format=custom --compress=9 --file="$pre_restore_backup"; then
        log_success "Pre-restore backup created: $pre_restore_backup"
    else
        log_warning "Failed to create pre-restore backup"
    fi

    # Perform the restore
    if pg_restore "${restore_options[@]}" "$backup_file" 2>&1 | tee "$BACKUP_DIR/restore_${timestamp}.log"; then
        log_success "Database restore completed"

        # Verify restore
        if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\dt" > /dev/null 2>&1; then
            log_success "Database connectivity verified after restore"
        else
            log_error "Database connectivity check failed after restore"
            return 1
        fi
    else
        log_error "Database restore failed"
        return 1
    fi
}

# Function to restore application data
restore_application_data() {
    local timestamp="$1"
    local data_backup_file="$BACKUP_DIR/app_data_${timestamp}.tar.gz"

    if [[ ! -f "$data_backup_file" ]]; then
        log_warning "Application data backup not found: $data_backup_file"
        return 0
    fi

    log_info "Restoring application data from: $data_backup_file"

    # Create backup of current data
    if [[ -d "/app/data" ]]; then
        local current_backup="/app/data_backup_$(date +%Y%m%d_%H%M%S)"
        if cp -r "/app/data" "$current_backup"; then
            log_info "Current data backed up to: $current_backup"
        fi
    fi

    # Extract application data
    if tar -xzf "$data_backup_file" -C /app/; then
        log_success "Application data restored"

        # Set proper permissions
        chown -R 1001:1001 /app/data 2>/dev/null || log_warning "Failed to set data permissions"
    else
        log_error "Failed to restore application data"
        return 1
    fi
}

# Function to find latest backup
find_latest_backup() {
    local latest_backup=""
    local latest_timestamp=0

    for backup in "$BACKUP_DIR"/*.custom; do
        if [[ -f "$backup" ]]; then
            local timestamp=$(basename "$backup" | sed 's/.*_\([0-9]*_[0-9]*\)\.custom/\1/')
            local epoch=$(date -d "$(echo "$timestamp" | sed 's/_/ /')" +%s 2>/dev/null || echo 0)

            if [[ $epoch -gt $latest_timestamp ]]; then
                latest_timestamp=$epoch
                latest_backup="$timestamp"
            fi
        fi
    done

    echo "$latest_backup"
}

# Main restore function
main() {
    local action=""
    local timestamp=""
    local force=false
    local data_only=false
    local schema_only=false
    local from_s3=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -f|--force)
                force=true
                shift
                ;;
            -d|--data-only)
                data_only=true
                shift
                ;;
            -s|--schema-only)
                schema_only=true
                shift
                ;;
            --from-s3)
                from_s3=true
                shift
                ;;
            list|restore|restore-latest|download|verify)
                action="$1"
                shift
                ;;
            *)
                if [[ -z "$timestamp" && "$action" != "list" && "$action" != "restore-latest" ]]; then
                    timestamp="$1"
                fi
                shift
                ;;
        esac
    done

    # Validate arguments
    if [[ -z "$action" ]]; then
        log_error "No action specified"
        show_usage
        exit 1
    fi

    if [[ "$action" != "list" && "$action" != "restore-latest" && -z "$timestamp" ]]; then
        log_error "Timestamp required for action: $action"
        show_usage
        exit 1
    fi

    check_prerequisites

    case "$action" in
        "list")
            list_backups
            ;;

        "download")
            download_from_s3 "$timestamp"
            ;;

        "verify")
            verify_backup "$timestamp"
            ;;

        "restore-latest")
            local latest=$(find_latest_backup)
            if [[ -z "$latest" ]]; then
                log_error "No local backups found"
                exit 1
            fi
            log_info "Found latest backup: $latest"
            timestamp="$latest"
            ;&  # Fall through to restore

        "restore")
            # Download from S3 if requested
            if [[ "$from_s3" == "true" ]]; then
                download_from_s3 "$timestamp"
            fi

            # Verify backup exists and is valid
            if ! verify_backup "$timestamp"; then
                exit 1
            fi

            # Get confirmation
            get_confirmation "This will restore the database and application data from backup $timestamp" "$force"

            # Find compose file
            local compose_file=""
            for file in "docker-compose.prod.yml" "docker-compose.yml"; do
                if [[ -f "$file" ]]; then
                    compose_file="$file"
                    break
                fi
            done

            # Stop application
            if [[ -n "$compose_file" ]]; then
                stop_application "$compose_file"
            fi

            # Restore database
            if restore_database "$timestamp" "$data_only" "$schema_only"; then
                log_success "Database restore completed"
            else
                log_error "Database restore failed"
                exit 1
            fi

            # Restore application data (if not schema-only)
            if [[ "$schema_only" != "true" ]]; then
                restore_application_data "$timestamp"
            fi

            # Start application
            if [[ -n "$compose_file" ]]; then
                start_application "$compose_file"
            fi

            log_success "Restore process completed successfully!"
            log_info "Please verify that the application is working correctly"
            ;;

        *)
            log_error "Unknown action: $action"
            show_usage
            exit 1
            ;;
    esac
}

# Trap for cleanup on script interruption
trap 'log_error "Restore interrupted!"; exit 1' INT TERM

# Run main function with all arguments
main "$@"