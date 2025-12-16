#!/bin/bash
# Congressional Transparency Platform - Production Deployment Script

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
ENV_FILE="$PROJECT_ROOT/.env.production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi

    # Check if required files exist
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Production compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Production environment file not found: $ENV_FILE"
        log_warning "Please create $ENV_FILE with production settings"
        exit 1
    fi

    # Check if backend network exists (for Traefik integration)
    if ! docker network ls | grep -q "backend"; then
        log_warning "Backend network not found. Creating it..."
        docker network create backend || {
            log_error "Failed to create backend network"
            exit 1
        }
    fi

    log_success "Prerequisites check passed"
}

# Function to validate environment variables
validate_environment() {
    log_info "Validating environment configuration..."

    # Source the environment file
    source "$ENV_FILE"

    # Check critical environment variables
    local required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "DATA_GOV_API_KEY"
        "GRAFANA_ADMIN_PASSWORD"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]] || [[ "${!var:-}" == *"CHANGE_ME"* ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing or invalid environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        log_error "Please update $ENV_FILE with production values"
        exit 1
    fi

    log_success "Environment validation passed"
}

# Function to create required directories
create_directories() {
    log_info "Creating required directories..."

    local dirs=(
        "/opt/congress-platform/data/postgres"
        "/opt/congress-platform/data/redis"
        "/opt/congress-platform/data/prometheus"
        "/opt/congress-platform/data/grafana"
        "/opt/congress-platform/backups"
        "/opt/congress-platform/logs"
    )

    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            sudo mkdir -p "$dir"
            sudo chown -R 1001:1001 "$dir"  # Use non-root ownership
            log_info "Created directory: $dir"
        fi
    done

    log_success "Directory creation completed"
}

# Function to build and pull images
prepare_images() {
    log_info "Preparing Docker images..."

    # Change to project root
    cd "$PROJECT_ROOT"

    # Build custom images
    log_info "Building frontend image..."
    docker build -f Dockerfile.frontend --target production -t congress-frontend:latest .

    log_info "Building backend image..."
    docker build -f Dockerfile.backend --target production -t congress-backend:latest .

    # Pull external images
    log_info "Pulling external images..."
    docker-compose -f "$COMPOSE_FILE" pull postgres redis prometheus grafana

    log_success "Image preparation completed"
}

# Function to run database migrations
run_migrations() {
    log_info "Running database migrations..."

    # Start only the database first
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis

    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    timeout=60
    while [[ $timeout -gt 0 ]]; do
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U congress_app -d congress_transparency; then
            break
        fi
        sleep 2
        ((timeout-=2))
    done

    if [[ $timeout -le 0 ]]; then
        log_error "Database failed to become ready within 60 seconds"
        exit 1
    fi

    # Run migrations if migration service is defined
    if docker-compose -f "$COMPOSE_FILE" config --services | grep -q "db-migrate"; then
        log_info "Running database migration..."
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm db-migrate
    fi

    log_success "Database migrations completed"
}

# Function to deploy the application
deploy_application() {
    log_info "Deploying Congressional Transparency Platform..."

    cd "$PROJECT_ROOT"

    # Start all services
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    # Wait for services to be healthy
    log_info "Waiting for services to become healthy..."
    sleep 30

    # Check service health
    local services=("frontend" "backend" "postgres" "redis")
    for service in "${services[@]}"; do
        if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "healthy\|Up"; then
            log_success "$service is running"
        else
            log_warning "$service may not be healthy"
        fi
    done

    log_success "Application deployment completed"
}

# Function to run health checks
run_health_checks() {
    log_info "Running health checks..."

    # Wait a bit for services to fully start
    sleep 10

    # Check frontend health
    if curl -f -s http://localhost:80/health > /dev/null; then
        log_success "Frontend health check passed"
    else
        log_warning "Frontend health check failed"
    fi

    # Check backend health
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log_success "Backend health check passed"
    else
        log_warning "Backend health check failed"
    fi

    # Check database connectivity
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U congress_app; then
        log_success "Database connectivity check passed"
    else
        log_warning "Database connectivity check failed"
    fi

    # Check Redis connectivity
    if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis connectivity check passed"
    else
        log_warning "Redis connectivity check failed"
    fi

    log_success "Health checks completed"
}

# Function to display deployment status
show_status() {
    log_info "Deployment Status:"
    echo
    docker-compose -f "$COMPOSE_FILE" ps
    echo
    log_info "Service URLs:"
    echo "  Frontend: https://congress.local.team-skynet.io"
    echo "  Backend API: https://congress-api.local.team-skynet.io"
    echo "  Grafana Dashboard: https://congress-dashboard.local.team-skynet.io"
    echo "  Prometheus Metrics: https://congress-metrics.local.team-skynet.io"
    echo
    log_info "To view logs: docker-compose -f $COMPOSE_FILE logs -f [service]"
    log_info "To stop: docker-compose -f $COMPOSE_FILE down"
}

# Function to handle deployment rollback
rollback() {
    log_warning "Rolling back deployment..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    log_success "Rollback completed"
}

# Main deployment function
main() {
    local action="${1:-deploy}"

    case "$action" in
        "deploy")
            log_info "Starting Congressional Transparency Platform production deployment..."
            check_prerequisites
            validate_environment
            create_directories
            prepare_images
            run_migrations
            deploy_application
            run_health_checks
            show_status
            log_success "Deployment completed successfully!"
            ;;
        "rollback")
            rollback
            ;;
        "status")
            show_status
            ;;
        "health")
            run_health_checks
            ;;
        *)
            echo "Usage: $0 [deploy|rollback|status|health]"
            echo "  deploy   - Deploy the application (default)"
            echo "  rollback - Roll back the current deployment"
            echo "  status   - Show deployment status"
            echo "  health   - Run health checks"
            exit 1
            ;;
    esac
}

# Trap for cleanup on script interruption
trap 'log_error "Deployment interrupted!"; rollback; exit 1' INT TERM

# Run main function with all arguments
main "$@"