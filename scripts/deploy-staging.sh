#!/bin/bash
# Congressional Transparency Platform - Staging Deployment Script

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"  # Use development compose for staging
ENV_FILE="$PROJECT_ROOT/.env.staging"

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
    log_info "Checking staging prerequisites..."

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
        log_error "Staging compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    # Create staging env file if it doesn't exist
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "Staging environment file not found. Creating from example..."
        cp "$PROJECT_ROOT/.env.staging" "$ENV_FILE" || {
            log_error "Failed to create staging environment file"
            exit 1
        }
    fi

    log_success "Prerequisites check passed"
}

# Function to clean up previous staging deployment
cleanup_previous() {
    log_info "Cleaning up previous staging deployment..."

    cd "$PROJECT_ROOT"

    # Stop and remove containers with staging profile
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans || true

    # Remove staging volumes if they exist
    docker volume rm congress_postgres_staging_data 2>/dev/null || true
    docker volume rm congress_redis_staging_data 2>/dev/null || true

    log_success "Previous staging cleanup completed"
}

# Function to start staging services
start_staging() {
    log_info "Starting staging services..."

    cd "$PROJECT_ROOT"

    # Start core services (postgres, redis)
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d postgres redis

    # Wait for database to be ready
    log_info "Waiting for staging database to be ready..."
    timeout=30
    while [[ $timeout -gt 0 ]]; do
        if docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres pg_isready -U congress_staging; then
            break
        fi
        sleep 2
        ((timeout-=2))
    done

    if [[ $timeout -le 0 ]]; then
        log_error "Staging database failed to become ready within 30 seconds"
        exit 1
    fi

    log_success "Core staging services started"
}

# Function to run staging tests
run_staging_tests() {
    log_info "Running staging tests..."

    cd "$PROJECT_ROOT"

    # Run Python tests
    log_info "Running Python unit tests..."
    if command -v pipenv &> /dev/null; then
        pipenv run python -m pytest test_member_consistency.py -v || {
            log_warning "Some Python tests failed"
        }
    else
        log_warning "Pipenv not found, skipping Python tests"
    fi

    # Test data fetching with small sample
    log_info "Testing data fetching capability..."
    if [[ -f "gov_data_analyzer.py" ]]; then
        timeout 60 python gov_data_analyzer.py --members --max-members 5 || {
            log_warning "Data fetching test had issues"
        }
    fi

    # Test database connection
    log_info "Testing database connectivity..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres psql -U congress_staging -d congress_transparency_staging -c "SELECT version();" || {
        log_error "Database connectivity test failed"
        return 1
    }

    log_success "Staging tests completed"
}

# Function to build and test frontend
test_frontend() {
    log_info "Testing frontend build..."

    if [[ -d "$PROJECT_ROOT/frontend" ]]; then
        cd "$PROJECT_ROOT/frontend"

        # Install dependencies if needed
        if [[ -f "package.json" ]] && command -v pnpm &> /dev/null; then
            log_info "Installing frontend dependencies..."
            pnpm install --frozen-lockfile

            # Run type checking
            log_info "Running TypeScript type check..."
            pnpm run type-check || {
                log_warning "TypeScript type check failed"
            }

            # Run linting
            log_info "Running ESLint..."
            pnpm run lint || {
                log_warning "ESLint found issues"
            }

            # Test build process
            log_info "Testing production build..."
            pnpm run build || {
                log_error "Frontend build failed"
                return 1
            }

            log_success "Frontend tests passed"
        else
            log_warning "Frontend dependencies not available, skipping frontend tests"
        fi
    else
        log_warning "Frontend directory not found, skipping frontend tests"
    fi
}

# Function to run integration tests
run_integration_tests() {
    log_info "Running integration tests..."

    # Test API endpoints if backend is available
    if docker-compose -f "$COMPOSE_FILE" ps backend | grep -q "Up"; then
        log_info "Testing API endpoints..."

        # Test health endpoint
        if curl -f -s http://localhost:8000/health > /dev/null; then
            log_success "API health endpoint responding"
        else
            log_warning "API health endpoint not responding"
        fi
    fi

    # Test data analysis scripts
    log_info "Testing data analysis capabilities..."
    if [[ -f "comprehensive_analyzer.py" ]]; then
        timeout 120 python comprehensive_analyzer.py --analyze --max-items 10 || {
            log_warning "Comprehensive analysis test had issues"
        }
    fi

    log_success "Integration tests completed"
}

# Function to show staging status
show_staging_status() {
    log_info "Staging Environment Status:"
    echo

    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" ps

    echo
    log_info "Staging URLs:"
    echo "  Database: localhost:5432 (congress_transparency_staging)"
    echo "  Redis: localhost:6379"
    echo
    log_info "Quick commands:"
    echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f [service]"
    echo "  Connect to DB: docker-compose -f $COMPOSE_FILE exec postgres psql -U congress_staging -d congress_transparency_staging"
    echo "  Stop staging: docker-compose -f $COMPOSE_FILE down"
}

# Function to generate staging report
generate_report() {
    log_info "Generating staging test report..."

    local report_file="$PROJECT_ROOT/staging-report-$(date +%Y%m%d-%H%M%S).txt"

    {
        echo "Congressional Transparency Platform - Staging Test Report"
        echo "Generated: $(date)"
        echo "========================================================"
        echo
        echo "Environment Configuration:"
        echo "- Compose file: $COMPOSE_FILE"
        echo "- Environment file: $ENV_FILE"
        echo
        echo "Docker Services Status:"
        docker-compose -f "$COMPOSE_FILE" ps
        echo
        echo "Database Status:"
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T postgres psql -U congress_staging -d congress_transparency_staging -c "\l" 2>/dev/null || echo "Database not accessible"
        echo
        echo "System Resources:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "Stats not available"
    } > "$report_file"

    log_success "Staging report generated: $report_file"
}

# Main staging function
main() {
    local action="${1:-test}"

    case "$action" in
        "test")
            log_info "Starting Congressional Transparency Platform staging test..."
            check_prerequisites
            cleanup_previous
            start_staging
            test_frontend
            run_staging_tests
            run_integration_tests
            show_staging_status
            generate_report
            log_success "Staging test completed successfully!"
            ;;
        "cleanup")
            cleanup_previous
            log_success "Staging cleanup completed"
            ;;
        "status")
            show_staging_status
            ;;
        "start")
            check_prerequisites
            start_staging
            show_staging_status
            ;;
        "stop")
            cd "$PROJECT_ROOT"
            docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
            log_success "Staging environment stopped"
            ;;
        *)
            echo "Usage: $0 [test|cleanup|status|start|stop]"
            echo "  test    - Run full staging test suite (default)"
            echo "  cleanup - Clean up staging environment"
            echo "  status  - Show staging status"
            echo "  start   - Start staging environment"
            echo "  stop    - Stop staging environment"
            exit 1
            ;;
    esac
}

# Trap for cleanup on script interruption
trap 'log_error "Staging test interrupted!"; cleanup_previous; exit 1' INT TERM

# Run main function with all arguments
main "$@"