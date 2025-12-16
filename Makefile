# Senate.gov and Congress.gov Data Collection Makefile
# Provides convenient targets for data collection and analysis

# Variables
PYTHON := pipenv run python
DATA_DIR := data
POLLER_DIR := poller
MAX_RESULTS := 1000000
MAX_MEMBERS := 5000000
MAX_VOTES := 1000000
CONGRESS := 118

# Maximum data collection variables (for fetch-everything)
MAX_RESULTS_ALL := 1000000
MAX_MEMBERS_ALL := 1000000
MAX_VOTES_ALL :=   5000000
MAX_BILLS_ALL :=   1000000

# Docker variables
DOCKER_COMPOSE_DEV := docker-compose -f docker-compose.yml -f docker-compose.override.yml
DOCKER_COMPOSE_PROD := docker-compose -f docker-compose.yml

# Default target
.PHONY: help
help:
	@echo "Senate & Congress Data Collection Targets"
	@echo "========================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install Python dependencies"
	@echo "  make clean           - Remove all downloaded data"
	@echo ""
	@echo "Quick Data Collection:"
	@echo "  make quick-fetch     - Fetch small sample of all data types (5 records each)"
	@echo "  make fetch-members   - Fetch Congressional members with party affiliations"
	@echo "  make fetch-bills     - Fetch recent bills from Congress"
	@echo "  make fetch-votes     - Fetch House votes with party breakdowns"
	@echo "  make fetch-lobbying  - Fetch Senate lobbying filings and lobbyists"
	@echo ""
	@echo "Comprehensive Collection:"
	@echo "  make fetch-all       - Fetch all data types (25 records each)"
	@echo "  make fetch-large     - Fetch larger dataset (100 records each)"
	@echo "  make smart-fetch     - Smart fetch: only downloads new/missing data"
	@echo "  make fetch-everything - Force fetch ALL data (ignores existing)"
	@echo "  make everything      - Smart fetch and analyze ALL data"
	@echo "  make transparency-mission - Complete smart transparency pipeline"
	@echo ""
	@echo "Historical Data Collection (Congresses 113-117):"
	@echo "  make historical-summary   - Show historical data collection summary"
	@echo "  make historical-jobs      - Create historical collection jobs"
	@echo "  make historical-fetch     - Run historical data collection (all congresses)"
	@echo "  make historical-resume    - Resume interrupted historical collection"
	@echo "  make historical-congress CONGRESS=116 - Fetch data for specific congress"
	@echo "  make historical-bills     - Fetch only historical bills data"
	@echo "  make historical-members   - Fetch only historical members data"
	@echo "  make historical-votes     - Fetch only historical votes data"
	@echo ""
	@echo "Analysis:"
	@echo "  make analyze         - Run party voting analysis on existing data"
	@echo "  make comprehensive   - Fetch data and run comprehensive analysis"
	@echo "  make report          - Generate analysis report from existing data"
	@echo ""
	@echo "Advanced Analysis:"
	@echo "  make analyze-sponsors    - Analyze bill sponsorship and bipartisanship"
	@echo "  make analyze-bipartisan  - Analyze cross-party cooperation patterns"
	@echo "  make fetch-vote-details  - Fetch individual member voting records"
	@echo "  make categorize-bills    - Categorize bills by topic/issue area"
	@echo "  make analyze-consistency - Track member party unity scores"
	@echo "  make analyze-timeline    - Analyze temporal patterns and trends"
	@echo "  make analyze-states      - Analyze state delegation patterns"
	@echo ""
	@echo "Trend Analysis:"
	@echo "  make analyze-legislative-activity - Analyze legislative activity trends"
	@echo "  make analyze-trends      - Run all trend analyses (legislative, bipartisan, consistency)"
	@echo ""
	@echo "Committee Analysis:"
	@echo "  make fetch-committees    - Fetch committee and subcommittee data"
	@echo "  make analyze-committees  - Analyze committee structure and activity"
	@echo ""
	@echo "Combined Analysis Pipelines:"
	@echo "  make quick-analysis  - Quick analysis with sample data"
	@echo "  make full-analysis   - Complete analysis pipeline"
	@echo "  make deep-analysis   - Deep comprehensive analysis with all data"
	@echo ""
	@echo "Utilities:"
	@echo "  make test           - Test API connections with minimal data"
	@echo "  make stats          - Show statistics about downloaded data"
	@echo "  make backup         - Create backup of current data"
	@echo ""
	@echo "Viewer (React App):"
	@echo "  make viewer          - Start the Congressional Transparency Portal"
	@echo "  make start           - Alias for 'make viewer'"
	@echo "  make viewer-build    - Build viewer for production"
	@echo "  make viewer-install  - Install viewer dependencies"
	@echo ""
	@echo "Code Quality & Linting:"
	@echo "  make lint-python     - Run all Python linters"
	@echo "  make lint-frontend   - Run all JavaScript/TypeScript linters"
	@echo "  make lint-all        - Run all linters (Python + Frontend)"
	@echo "  make format          - Auto-fix all formatting issues"
	@echo "  make format-python   - Format Python code (black, isort)"
	@echo "  make format-frontend - Format frontend code (prettier)"
	@echo "  make type-check      - Run TypeScript type checking"
	@echo "  make pre-commit      - Run pre-commit hooks on all files"
	@echo "  make install-hooks   - Install pre-commit git hooks"
	@echo ""
	@echo "Variables (override with make VAR=value):"
	@echo "  CONGRESS=$(CONGRESS)     - Congress number to fetch"
	@echo "  MAX_RESULTS=$(MAX_RESULTS)  - Maximum records per category (default)"
	@echo "  MAX_MEMBERS=$(MAX_MEMBERS)  - Maximum members to fetch (default)"
	@$(MAKE) db-help
	@echo "  MAX_VOTES=$(MAX_VOTES)    - Maximum votes to fetch (default)"
	@echo ""
	@echo "Maximum Collection Variables (used by fetch-everything):"
	@echo "  MAX_RESULTS_ALL=$(MAX_RESULTS_ALL) - Maximum records for full collection"
	@echo "  MAX_MEMBERS_ALL=$(MAX_MEMBERS_ALL)  - Maximum members for full collection"
	@echo "  MAX_VOTES_ALL=$(MAX_VOTES_ALL)   - Maximum votes for full collection"
	@echo "  MAX_BILLS_ALL=$(MAX_BILLS_ALL)  - Maximum bills for full collection"

# Setup targets
.PHONY: install
install:
	@echo "Installing Python dependencies..."
	pipenv install requests python-dotenv

.PHONY: clean
clean:
	@echo "Cleaning data directory..."
	rm -rf $(DATA_DIR)/*
	@echo "Data directory cleaned."

# Quick fetch targets
.PHONY: quick-fetch
quick-fetch:
	@echo "Quick fetch: Getting 5 records of each type..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --all --max-results 5
	cd $(POLLER_DIR) && $(PYTHON) fetch_members_votes.py --members --votes --max-members 5 --max-votes 5

.PHONY: fetch-members
fetch-members:
	@echo "Fetching $(MAX_MEMBERS) Congressional members..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_members_votes.py --members --congress $(CONGRESS) --max-members $(MAX_MEMBERS)

.PHONY: fetch-bills
fetch-bills:
	@echo "Fetching $(MAX_RESULTS) bills from Congress $(CONGRESS)..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --congress-bills --congress $(CONGRESS) --max-results $(MAX_RESULTS)

.PHONY: fetch-votes
fetch-votes:
	@echo "Fetching $(MAX_VOTES) House votes with party breakdowns..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_members_votes.py --votes --congress $(CONGRESS) --max-votes $(MAX_VOTES)

.PHONY: fetch-lobbying
fetch-lobbying:
	@echo "Fetching $(MAX_RESULTS) lobbying records..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --senate-filings --senate-lobbyists --max-results $(MAX_RESULTS)

# Comprehensive collection targets
.PHONY: fetch-all
fetch-all:
	@echo "Fetching all data types ($(MAX_RESULTS) records each)..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --all --congress $(CONGRESS) --max-results $(MAX_RESULTS)
	cd $(POLLER_DIR) && $(PYTHON) fetch_members_votes.py --members --votes --congress $(CONGRESS) \
		--max-members $(MAX_MEMBERS) --max-votes $(MAX_VOTES)

.PHONY: fetch-large
fetch-large:
	@echo "Fetching large dataset (100 records each)..."
	$(MAKE) fetch-all MAX_RESULTS=100 MAX_MEMBERS=200 MAX_VOTES=50

# Analysis targets
.PHONY: analyze
analyze:
	@echo "Running party voting analysis..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_members_votes.py --votes --analyze --congress $(CONGRESS)

.PHONY: comprehensive
comprehensive:
	@echo "Running comprehensive data collection and analysis..."
	cd $(POLLER_DIR) && $(PYTHON) comprehensive_analyzer.py --fetch --analyze --congress $(CONGRESS) --max-items $(MAX_RESULTS)

.PHONY: report
report:
	@echo "Generating analysis report from existing data..."
	cd $(POLLER_DIR) && $(PYTHON) comprehensive_analyzer.py --analyze

# Committee Targets
.PHONY: fetch-committees
fetch-committees:
	@echo "Fetching committee and subcommittee data..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_committees.py --congress $(CONGRESS) --fetch-bills --max-bills $(MAX_RESULTS)

.PHONY: analyze-committees
analyze-committees:
	@echo "Analyzing committee structure and activity..."
	cd $(POLLER_DIR) && $(PYTHON) analyze_committees.py --congress $(CONGRESS)

# Lobbying Targets
.PHONY: fetch-lobbying
fetch-lobbying:
	@echo "Fetching $(MAX_RESULTS) lobbying disclosure filings..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_lobbying.py --all --max-results $(MAX_RESULTS) --individual-files
	@echo "Also fetching lobbyist records..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --senate-lobbyists --max-results $(MAX_RESULTS)

.PHONY: fetch-ld1
fetch-ld1:
	@echo "Fetching LD-1 Registration forms..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_lobbying.py --ld1 --max-results $(MAX_RESULTS) --individual-files

.PHONY: fetch-ld2
fetch-ld2:
	@echo "Fetching LD-2 Activity reports..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_lobbying.py --ld2 --max-results $(MAX_RESULTS) --individual-files

# New Analysis Scripts
.PHONY: analyze-sponsors
analyze-sponsors:
	@echo "Analyzing bill sponsorship patterns..."
	cd $(POLLER_DIR) && $(PYTHON) analyze_bill_sponsors.py --congress $(CONGRESS) --max-bills $(MAX_RESULTS)

.PHONY: analyze-bipartisan
analyze-bipartisan:
	@echo "Analyzing bipartisan cooperation patterns..."
	cd $(POLLER_DIR) && $(PYTHON) analyze_bipartisan_cooperation.py --congress $(CONGRESS) --verbose

.PHONY: analyze-bipartisan-cooperation
analyze-bipartisan-cooperation:
	@echo "Analyzing bipartisan cooperation patterns..."
	cd $(POLLER_DIR) && $(PYTHON) analyze_bipartisan_cooperation.py --congress $(CONGRESS) --verbose

.PHONY: fetch-vote-details
fetch-vote-details:
	@echo "Fetching detailed voting records..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_voting_records.py --congress $(CONGRESS) --max-votes $(MAX_VOTES)

.PHONY: categorize-bills
categorize-bills:
	@echo "Categorizing bills by topic..."
	cd $(POLLER_DIR) && $(PYTHON)categorize_bills.py --congress $(CONGRESS) --max-bills $(MAX_RESULTS) --save-categories

.PHONY: analyze-consistency
analyze-consistency:
	@echo "Analyzing member voting consistency..."
	cd $(POLLER_DIR) && $(PYTHON) analyze_member_consistency.py --max-members $(MAX_MEMBERS)

.PHONY: analyze-timeline
analyze-timeline:
	@echo "Analyzing temporal patterns..."
	cd $(POLLER_DIR) && $(PYTHON)analyze_timeline.py --max-bills $(MAX_RESULTS)

.PHONY: analyze-states
analyze-states:
	@echo "Analyzing state delegation patterns..."
	cd $(POLLER_DIR) && $(PYTHON) analyze_state_patterns.py

# Trend Analysis Targets
.PHONY: analyze-legislative-activity
analyze-legislative-activity:
	@echo "Analyzing legislative activity trends..."
	cd $(POLLER_DIR) && $(PYTHON) analyze_legislative_activity.py

.PHONY: analyze-trends
analyze-trends: analyze-legislative-activity analyze-bipartisan-cooperation analyze-consistency
	@echo "✅ All trend analyses complete"

# Combined Analysis Targets
.PHONY: full-analysis
full-analysis: fetch-all fetch-committees analyze-sponsors analyze-bipartisan fetch-vote-details categorize-bills analyze-trends analyze-timeline analyze-states analyze-committees
	@echo "Full analysis pipeline completed!"

.PHONY: quick-analysis
quick-analysis: quick-fetch analyze-sponsors analyze-bipartisan categorize-bills analyze-trends
	@echo "Quick analysis completed with sample data!"

.PHONY: deep-analysis
deep-analysis: comprehensive analyze-sponsors analyze-bipartisan fetch-vote-details categorize-bills analyze-trends analyze-timeline analyze-states report
	@echo "Deep comprehensive analysis completed!"

# Smart Fetch - Only fetch new or missing data
.PHONY: smart-fetch
smart-fetch:
	@echo "=================================================================================="
	@echo "SMART FETCH - Checking existing data before fetching"
	@echo "=================================================================================="
	@$(PYTHON) smart_fetch.py --check-only
	@echo ""
	@echo "Fetching only new or missing data..."
	@echo ""
	@echo "Stage 1: Fetching all Congressional data if needed..."
	@if [ ! -d "$(DATA_DIR)/congress_bills/118" ] || [ $$(find $(DATA_DIR)/congress_bills/118 -name "*.json" 2>/dev/null | wc -l) -lt 100 ]; then \
		cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --congress-bills --congress-votes \
			--congress $(CONGRESS) --max-results $(MAX_BILLS_ALL); \
	else \
		echo "  Skipping - Congressional bills already exist"; \
	fi
	@echo ""
	@echo "Stage 2: Fetching all Senate lobbying data if needed..."
	@if [ ! -d "$(DATA_DIR)/senate_filings" ] || [ $$(find $(DATA_DIR)/senate_filings -name "*.json" 2>/dev/null | wc -l) -lt 10 ]; then \
		cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --senate-filings --senate-lobbyists \
			--max-results $(MAX_RESULTS_ALL); \
	else \
		echo "  Skipping - Senate lobbying data already exists"; \
	fi
	@echo ""
	@echo "Stage 3: Fetching all member data if needed..."
	@if [ ! -d "$(DATA_DIR)/members" ] || [ $$(find $(DATA_DIR)/members -name "*.json" 2>/dev/null | wc -l) -lt 50 ]; then \
		cd $(POLLER_DIR) && $(PYTHON) fetch_members_votes.py --members --congress $(CONGRESS) \
			--max-members $(MAX_MEMBERS_ALL); \
	else \
		echo "  Skipping - Member data already exists"; \
	fi
	@echo ""
	@echo "Stage 4: Fetching detailed voting records if needed..."
	@if [ ! -d "$(DATA_DIR)/votes/118/house" ] || [ $$(find $(DATA_DIR)/votes/118/house -name "*.json" 2>/dev/null | wc -l) -lt 10 ]; then \
		cd $(POLLER_DIR) && $(PYTHON)fetch_voting_records.py --congress $(CONGRESS) \
			--max-votes $(MAX_VOTES_ALL); \
	else \
		echo "  Skipping - Voting records already exist"; \
	fi
	@echo ""
	@echo "Stage 5: Fetching bill details and sponsors if needed..."
	@if [ ! -d "$(DATA_DIR)/bill_sponsors" ] || [ $$(find $(DATA_DIR)/bill_sponsors -name "*.json" 2>/dev/null | wc -l) -lt 10 ]; then \
		cd $(POLLER_DIR) && $(PYTHON)analyze_bill_sponsors.py --congress $(CONGRESS) \
			--max-bills $(MAX_BILLS_ALL); \
	else \
		echo "  Skipping - Bill sponsor data already exists"; \
	fi
	@echo ""
	@echo "Stage 6: Fetching committee data if needed..."
	@if [ ! -d "$(DATA_DIR)/committees/$(CONGRESS)" ] || [ $$(find $(DATA_DIR)/committees/$(CONGRESS) -name "*.json" 2>/dev/null | wc -l) -lt 10 ]; then \
		cd $(POLLER_DIR) && $(PYTHON)fetch_committees.py --congress $(CONGRESS) \
			--fetch-bills --max-bills 100; \
	else \
		echo "  Skipping - Committee data already exists"; \
	fi
	@echo ""
	@echo "SMART FETCH COMPLETE!"

# Maximum Data Collection - Fetch EVERYTHING available (forces refetch)
.PHONY: fetch-everything
fetch-everything:
	@echo "=================================================================================="
	@echo "FETCHING ALL AVAILABLE DATA - THIS WILL TAKE A LONG TIME!"
	@echo "=================================================================================="
	@echo "Fetching up to $(MAX_BILLS_ALL) bills, $(MAX_MEMBERS_ALL) members, $(MAX_VOTES_ALL) votes..."
	@echo ""
	@echo "Stage 1: Fetching all Congressional data..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --congress-bills --congress-votes \
		--congress $(CONGRESS) --max-results $(MAX_BILLS_ALL)
	@echo ""
	@echo "Stage 2: Fetching all Senate lobbying data..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --senate-filings --senate-lobbyists \
		--max-results $(MAX_RESULTS_ALL)
	@echo ""
	@echo "Stage 3: Fetching all member data..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_members_votes.py --members --congress $(CONGRESS) \
		--max-members $(MAX_MEMBERS_ALL)
	@echo ""
	@echo "Stage 4: Fetching detailed voting records..."
	cd $(POLLER_DIR) && $(PYTHON)fetch_voting_records.py --congress $(CONGRESS) \
		--max-votes $(MAX_VOTES_ALL)
	@echo ""
	@echo "Stage 5: Fetching bill details and sponsors..."
	cd $(POLLER_DIR) && $(PYTHON)analyze_bill_sponsors.py --congress $(CONGRESS) \
		--max-bills $(MAX_BILLS_ALL)
	@echo ""
	@echo "ALL DATA FETCHING COMPLETE!"

# Force refetch of everything
.PHONY: fetch-everything-force
fetch-everything-force: clean fetch-everything
	@echo "Forced refetch complete!"

.PHONY: analyze-everything
analyze-everything:
	@echo "=================================================================================="
	@echo "ANALYZING ALL AVAILABLE DATA"
	@echo "=================================================================================="
	@echo ""
	@echo "Stage 1: Categorizing all bills..."
	cd $(POLLER_DIR) && $(PYTHON)categorize_bills.py --congress $(CONGRESS) \
		--max-bills $(MAX_BILLS_ALL) --save-categories
	@echo ""
	@echo "Stage 2: Analyzing member consistency..."
	cd $(POLLER_DIR) && $(PYTHON)analyze_member_consistency.py --max-members $(MAX_MEMBERS_ALL)
	@echo ""
	@echo "Stage 3: Analyzing timeline patterns..."
	cd $(POLLER_DIR) && $(PYTHON)analyze_timeline.py --max-bills $(MAX_BILLS_ALL)
	@echo ""
	@echo "Stage 4: Analyzing state patterns..."
	cd $(POLLER_DIR) && $(PYTHON) analyze_state_patterns.py
	@echo ""
	@echo "Stage 5: Analyzing legislative activity trends..."
	cd $(POLLER_DIR) && $(PYTHON) analyze_legislative_activity.py
	@echo ""
	@echo "Stage 6: Running comprehensive analysis..."
	cd $(POLLER_DIR) && $(PYTHON) comprehensive_analyzer.py --analyze
	@echo ""
	@echo "ALL ANALYSIS COMPLETE!"

.PHONY: everything
everything: smart-fetch analyze-everything
	@echo "=================================================================================="
	@echo "COMPLETE DATA COLLECTION AND ANALYSIS FINISHED!"
	@echo "=================================================================================="
	@echo "All data has been fetched and analyzed."
	@echo "Run 'make viewer' to explore the data in the web interface."
	@echo "Run 'make stats' to see statistics about the collected data."

.PHONY: transparency-mission
transparency-mission: smart-fetch analyze-everything
	@echo "=================================================================================="
	@echo "CONGRESSIONAL TRANSPARENCY MISSION COMPLETE!"
	@echo "=================================================================================="
	@echo "✓ All available congressional data collected"
	@echo "✓ All bills categorized and analyzed"
	@echo "✓ All voting records processed"
	@echo "✓ All member consistency tracked"
	@echo "✓ All state patterns analyzed"
	@echo "✓ All temporal trends identified"
	@echo ""
	@echo "The data is ready for public transparency!"
	@echo "Start the viewer with: make viewer"
	@echo "View statistics with: make stats"

# Utility targets
.PHONY: test
test:
	@echo "Testing API connections..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --congress-bills --max-results 2
	@echo "Test successful! APIs are working."

.PHONY: stats
stats:
	@echo "Data Statistics:"
	@echo "================"
	@find $(DATA_DIR) -name "*.json" -not -name "index.json" -not -name "summary.json" | wc -l | xargs echo "Total JSON files:"
	@echo ""
	@echo "By category:"
	@for dir in $(DATA_DIR)/*/; do \
		if [ -d "$$dir" ]; then \
			count=$$(find "$$dir" -name "*.json" -not -name "index.json" -not -name "summary.json" | wc -l); \
			name=$$(basename "$$dir"); \
			echo "  $$name: $$count files"; \
		fi \
	done
	@echo ""
	@du -sh $(DATA_DIR) | cut -f1 | xargs echo "Total size:"

.PHONY: backup
backup:
	@echo "Creating backup of data directory..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	tar -czf "data_backup_$$timestamp.tar.gz" $(DATA_DIR)/; \
	echo "Backup created: data_backup_$$timestamp.tar.gz"

# Development targets
.PHONY: dev-senate
dev-senate:
	@echo "Fetching Senate data for development..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --senate-filings --senate-lobbyists --max-results 10

.PHONY: dev-congress
dev-congress:
	@echo "Fetching Congress data for development..."
	cd $(POLLER_DIR) && $(PYTHON) fetch_data.py --congress-bills --congress-votes --max-results 10

.PHONY: dev-analyze
dev-analyze: dev-senate dev-congress
	@echo "Running development analysis..."
	cd $(POLLER_DIR) && $(PYTHON) comprehensive_analyzer.py --analyze

# Viewer targets
.PHONY: viewer
viewer:
	@echo "Starting Congressional Transparency Portal..."
	@echo "Open http://localhost:5173 in your browser"
	@cd frontend && npm run dev

.PHONY: viewer-build
viewer-build:
	@echo "Building Congressional Transparency Portal for production..."
	@cd frontend && pnpm run build

.PHONY: viewer-install
viewer-install:
	@echo "Installing viewer dependencies..."
	@cd congress-viewer && npm install

.PHONY: sync-viewer-data
sync-viewer-data:
	@echo "Syncing analysis data to viewer..."
	@$(PYTHON) sync_viewer_data.py

.PHONY: viewer-with-data
viewer-with-data: sync-viewer-data viewer
	@echo "Viewer started with real data!"

.PHONY: start
start: viewer

# Clean specific data types
.PHONY: clean-bills
clean-bills:
	rm -rf $(DATA_DIR)/congress_bills/

.PHONY: clean-votes
clean-votes:
	rm -rf $(DATA_DIR)/house_votes*/ $(DATA_DIR)/senate_votes/

.PHONY: clean-members
clean-members:
	rm -rf $(DATA_DIR)/members/

.PHONY: clean-lobbying
clean-lobbying:
	rm -rf $(DATA_DIR)/senate_filings/ $(DATA_DIR)/senate_lobbyists/

.PHONY: clean-analysis
clean-analysis:
	rm -rf $(DATA_DIR)/analysis/

# Historical Data Collection Targets (Congresses 113-117)
HISTORICAL_CONGRESSES := 117 116 115 114 113

.PHONY: historical-summary
historical-summary:
	@echo "Historical Data Collection Summary:"
	@echo "=================================="
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --summary

.PHONY: historical-jobs
historical-jobs:
	@echo "Creating historical data collection jobs..."
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --create-jobs-only
	@echo "Jobs created. Run 'make historical-fetch' to start collection."

.PHONY: historical-fetch
historical-fetch:
	@echo "=================================================================================="
	@echo "HISTORICAL DATA COLLECTION - Congresses 113-117 (2013-2023)"
	@echo "=================================================================================="
	@echo "This will collect 10+ years of congressional data. This may take several hours."
	@echo "Collection will be done in parallel with progress tracking and resumable downloads."
	@echo ""
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --max-workers 2
	@echo ""
	@echo "Historical data collection completed!"
	@$(MAKE) historical-summary

.PHONY: historical-resume
historical-resume:
	@echo "Resuming historical data collection from existing queue..."
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --resume --max-workers 8

.PHONY: historical-congress
historical-congress:
	@echo "Fetching historical data for Congress $(CONGRESS)..."
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --congresses $(CONGRESS) --max-workers 6

.PHONY: historical-bills
historical-bills:
	@echo "Fetching historical bills data (congresses 113-117)..."
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --data-types bills --max-workers 8

.PHONY: historical-members
historical-members:
	@echo "Fetching historical members data (congresses 113-117)..."
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --data-types members --max-workers 6

.PHONY: historical-votes
historical-votes:
	@echo "Fetching historical votes data (congresses 113-117)..."
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --data-types house_votes senate_votes --max-workers 8

.PHONY: historical-fresh
historical-fresh:
	@echo "Starting fresh historical data collection (clears existing queue)..."
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --no-resume --max-workers 8

.PHONY: historical-quick
historical-quick:
	@echo "Quick historical test (Congress 117 only)..."
	cd $(POLLER_DIR) && $(PYTHON) historical_data_fetcher.py --congresses 117 --max-workers 4

.PHONY: clean-historical
clean-historical:
	@echo "Cleaning historical data directory..."
	rm -rf $(DATA_DIR)/historical/
	@echo "Historical data directory cleaned."

# ============================================================================
# DATABASE OPERATIONS (PostgreSQL)
# ============================================================================

# Database Configuration
DB_COMPOSE_FILE := docker-compose.yml
DB_CONTAINER := congress_postgres
DB_NAME := congress_transparency
DB_USER := congress_app
MIGRATION_BATCH_SIZE := 1000

.PHONY: db-help
db-help:
	@echo ""
	@echo "Database Operations:"
	@echo "==================="
	@echo ""
	@echo "Development Environment:"
	@echo "  make db-start         - Start PostgreSQL development environment"
	@echo "  make db-stop          - Stop database containers"
	@echo "  make db-restart       - Restart database containers"
	@echo "  make db-logs          - Show database container logs"
	@echo "  make db-shell         - Connect to database shell"
	@echo "  make db-admin         - Open pgAdmin web interface"
	@echo ""
	@echo "Schema Management:"
	@echo "  make db-create-schema - Create database schema"
	@echo "  make db-drop-schema   - Drop and recreate database schema"
	@echo "  make db-migrate       - Run database migrations"
	@echo "  make db-refresh-views - Refresh materialized views"
	@echo ""
	@echo "Data Migration:"
	@echo "  make db-migrate-data  - Migrate JSON data to database"
	@echo "  make db-validate      - Validate migrated data"
	@echo "  make db-stats         - Show database statistics"
	@echo "  make db-full-setup    - Complete database setup and migration"
	@echo ""
	@echo "Backup & Restore:"
	@echo "  make db-backup        - Create database backup"
	@echo "  make db-restore FILE= - Restore from backup file"
	@echo "  make db-cleanup       - Clean up old backups"
	@echo ""
	@echo "Development & Testing:"
	@echo "  make db-test          - Run database tests"
	@echo "  make db-reset         - Reset database to clean state"
	@echo "  make db-sample        - Load sample data for development"

# Development Environment
.PHONY: db-start
db-start:
	@echo "Starting PostgreSQL development environment..."
	@mkdir -p docker-volumes/postgres docker-volumes/redis docker-volumes/pgadmin
	docker-compose -f $(DB_COMPOSE_FILE) up -d postgres redis
	@echo "Waiting for database to be ready..."
	@timeout 60 sh -c 'until docker-compose -f $(DB_COMPOSE_FILE) exec postgres pg_isready -U $(DB_USER) -d $(DB_NAME); do sleep 2; done'
	@echo "✅ Database is ready!"
	@echo ""
	@echo "Connection details:"
	@echo "  Host: localhost"
	@echo "  Port: 5432"
	@echo "  Database: $(DB_NAME)"
	@echo "  Username: $(DB_USER)"

.PHONY: db-stop
db-stop:
	@echo "Stopping database containers..."
	docker-compose -f $(DB_COMPOSE_FILE) down

.PHONY: db-restart
db-restart: db-stop db-start

.PHONY: db-logs
db-logs:
	docker-compose -f $(DB_COMPOSE_FILE) logs -f postgres

.PHONY: db-shell
db-shell:
	@echo "Connecting to database shell..."
	docker-compose -f $(DB_COMPOSE_FILE) exec postgres psql -U $(DB_USER) -d $(DB_NAME)

.PHONY: db-admin
db-admin:
	@echo "Starting pgAdmin..."
	docker-compose -f $(DB_COMPOSE_FILE) --profile development up -d pgadmin
	@echo "pgAdmin available at: http://localhost:8080"
	@echo "Email: admin@congress-transparency.local"
	@echo "Password: admin_password_change_in_production"

# Schema Management
.PHONY: db-create-schema
db-create-schema:
	@echo "Creating database schema..."
	cd $(POLLER_DIR) && $(PYTHON)database_setup.py --create-schema

.PHONY: db-drop-schema
db-drop-schema:
	@echo "Dropping and recreating database schema..."
	cd $(POLLER_DIR) && $(PYTHON)database_setup.py --create-schema --drop-schema

.PHONY: db-migrate
db-migrate:
	@echo "Running database migrations..."
	docker-compose -f $(DB_COMPOSE_FILE) exec postgres psql -U $(DB_USER) -d $(DB_NAME) -f /docker-entrypoint-initdb.d/02-initial_migration.sql

.PHONY: db-refresh-views
db-refresh-views:
	@echo "Refreshing materialized views..."
	docker-compose -f $(DB_COMPOSE_FILE) exec postgres psql -U $(DB_USER) -d $(DB_NAME) -c "SELECT refresh_all_materialized_views();"

# Data Migration
.PHONY: db-migrate-data
db-migrate-data:
	@echo "Migrating JSON data to PostgreSQL..."
	@echo "This may take several minutes depending on data size..."
	cd $(POLLER_DIR) && $(PYTHON)database_setup.py --migrate-data --batch-size $(MIGRATION_BATCH_SIZE)

.PHONY: db-validate
db-validate:
	@echo "Validating migrated data..."
	cd $(POLLER_DIR) && $(PYTHON)database_setup.py --validate-data

.PHONY: db-stats
db-stats:
	@echo "Database Statistics:"
	@echo "==================="
	@docker-compose -f $(DB_COMPOSE_FILE) exec postgres psql -U $(DB_USER) -d $(DB_NAME) -c "\
		SELECT schemaname, tablename, n_live_tup as rows \
		FROM pg_stat_user_tables \
		WHERE schemaname IN ('congress', 'senate', 'analysis') \
		ORDER BY schemaname, n_live_tup DESC;"
	@echo ""
	@echo "Table Sizes:"
	@docker-compose -f $(DB_COMPOSE_FILE) exec postgres psql -U $(DB_USER) -d $(DB_NAME) -c "\
		SELECT * FROM metadata.table_sizes LIMIT 20;"

.PHONY: db-full-setup
db-full-setup: db-start db-create-schema db-migrate-data db-validate
	@echo "✅ Complete database setup completed!"
	@$(MAKE) db-stats

# Backup & Restore
.PHONY: db-backup
db-backup:
	@echo "Creating database backup..."
	@mkdir -p backups
	docker-compose -f $(DB_COMPOSE_FILE) --profile backup up postgres-backup

.PHONY: db-restore
db-restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify backup file with FILE=path/to/backup.sql"; \
		echo "Usage: make db-restore FILE=backups/congress_transparency_20240922_120000.sql"; \
		exit 1; \
	fi
	@echo "Restoring database from $(FILE)..."
	@if [ ! -f "$(FILE)" ]; then \
		echo "Error: Backup file $(FILE) not found"; \
		exit 1; \
	fi
	docker-compose -f $(DB_COMPOSE_FILE) exec postgres pg_restore -U $(DB_USER) -d $(DB_NAME) --clean --if-exists --verbose $(FILE)

.PHONY: db-cleanup
db-cleanup:
	@echo "Cleaning up old backups (keeping last 30 days)..."
	find backups/ -name "congress_transparency_*.sql" -mtime +30 -delete 2>/dev/null || true
	find backups/ -name "*.txt.gz" -mtime +30 -delete 2>/dev/null || true
	@echo "Backup cleanup completed."

# Development & Testing
.PHONY: db-test
db-test:
	@echo "Running database tests..."
	cd $(POLLER_DIR) && $(PYTHON)database_setup.py --test-connection

.PHONY: db-reset
db-reset:
	@echo "Resetting database to clean state..."
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		$(MAKE) db-drop-schema; \
		$(MAKE) db-create-schema; \
		echo "✅ Database reset completed"; \
	else \
		echo ""; \
		echo "Database reset cancelled"; \
	fi

.PHONY: db-sample
db-sample: db-reset
	@echo "Loading sample data for development..."
	$(MAKE) quick-fetch
	$(MAKE) db-migrate-data

# Combined Database + Data Collection Targets
.PHONY: full-transparency-setup
full-transparency-setup: install db-start db-create-schema fetch-all db-migrate-data analyze
	@echo "🎉 COMPLETE TRANSPARENCY PLATFORM SETUP COMPLETED!"
	@echo ""
	@echo "✅ Dependencies installed"
	@echo "✅ Database environment started"
	@echo "✅ Database schema created"
	@echo "✅ Congressional data collected"
	@echo "✅ Data migrated to PostgreSQL"
	@echo "✅ Analysis pipeline executed"
	@echo ""
	@echo "Your transparency platform is ready!"
	@echo "Database: http://localhost:8080 (pgAdmin)"
	@echo "Data location: $(DATA_DIR)/"
	@$(MAKE) db-stats

.PHONY: transparency-db-mission
transparency-db-mission: transparency-mission db-migrate-data
	@echo "🚀 TRANSPARENCY DATABASE MISSION COMPLETED!"
	@echo "All data collected AND migrated to PostgreSQL database"
	@$(MAKE) db-stats

# ============================================================================
# CODE QUALITY & LINTING
# ============================================================================

# Python Code Quality
.PHONY: lint-python
lint-python:
	@echo "Running Python linters..."
	@echo "========================="
	@echo ""
	@echo "1. Running ruff (fast linter)..."
	cd $(POLLER_DIR) && $(PYTHON) -m ruff check . --fix
	@echo ""
	@echo "2. Running flake8 (style checker)..."
	cd $(POLLER_DIR) && $(PYTHON) -m flake8 .
	@echo ""
	@echo "3. Running pylint (comprehensive analysis)..."
	cd $(POLLER_DIR) && $(PYTHON) -m pylint --rcfile=.pylintrc *.py
	@echo ""
	@echo "4. Running mypy (type checker)..."
	cd $(POLLER_DIR) && $(PYTHON) -m mypy . --ignore-missing-imports
	@echo ""
	@echo "5. Running bandit (security checker)..."
	cd $(POLLER_DIR) && $(PYTHON) -m bandit -r . -x tests/,migrations/,node_modules/,.venv/,venv/
	@echo ""
	@echo "✅ Python linting completed!"

.PHONY: format-python
format-python:
	@echo "Formatting Python code..."
	@echo "========================="
	@echo ""
	@echo "1. Running isort (import sorting)..."
	cd $(POLLER_DIR) && $(PYTHON) -m isort . --profile black
	@echo ""
	@echo "2. Running black (code formatting)..."
	cd $(POLLER_DIR) && $(PYTHON) -m black . --line-length 88
	@echo ""
	@echo "✅ Python formatting completed!"

# Frontend Code Quality
.PHONY: lint-frontend
lint-frontend:
	@echo "Running Frontend linters..."
	@echo "=========================="
	@echo ""
	@echo "Checking if frontend directory exists..."
	@if [ -d "frontend" ]; then \
		echo "Frontend directory found. Running linters..."; \
		cd frontend && echo "1. Running ESLint..." && npm run lint; \
		cd frontend && echo "2. Running Prettier check..." && npm run format:check; \
		cd frontend && echo "3. Running TypeScript check..." && npm run type-check; \
		echo "✅ Frontend linting completed!"; \
	else \
		echo "⚠️  Frontend directory not found. Skipping frontend linting."; \
	fi

.PHONY: format-frontend
format-frontend:
	@echo "Formatting Frontend code..."
	@echo "=========================="
	@echo ""
	@if [ -d "frontend" ]; then \
		echo "Frontend directory found. Running formatters..."; \
		cd frontend && echo "1. Running Prettier..." && npm run format; \
		cd frontend && echo "2. Running ESLint --fix..." && npm run lint:fix; \
		echo "✅ Frontend formatting completed!"; \
	else \
		echo "⚠️  Frontend directory not found. Skipping frontend formatting."; \
	fi

# Combined Linting
.PHONY: lint-all
lint-all: lint-python lint-frontend
	@echo ""
	@echo "🎉 ALL LINTING COMPLETED!"
	@echo "========================"
	@echo "✅ Python code quality checked"
	@echo "✅ Frontend code quality checked"
	@echo "Ready for commit!"

# Combined Formatting
.PHONY: format
format: format-python format-frontend
	@echo ""
	@echo "🎉 ALL FORMATTING COMPLETED!"
	@echo "============================"
	@echo "✅ Python code formatted"
	@echo "✅ Frontend code formatted"
	@echo "Ready for commit!"

# Type Checking
.PHONY: type-check
type-check:
	@echo "Running Type Checking..."
	@echo "======================="
	@echo ""
	@echo "1. Python type checking (mypy)..."
	cd $(POLLER_DIR) && $(PYTHON) -m mypy . --ignore-missing-imports
	@echo ""
	@if [ -d "frontend" ]; then \
		echo "2. TypeScript type checking..."; \
		cd frontend && npm run type-check; \
	else \
		echo "⚠️  Frontend directory not found. Skipping TypeScript checking."; \
	fi
	@echo ""
	@echo "✅ Type checking completed!"

# Pre-commit Hooks
.PHONY: install-hooks
install-hooks:
	@echo "Installing pre-commit hooks..."
	@echo "============================="
	cd $(POLLER_DIR) && $(PYTHON) -m pre_commit install
	cd $(POLLER_DIR) && $(PYTHON) -m pre_commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed!"

.PHONY: pre-commit
pre-commit:
	@echo "Running pre-commit hooks on all files..."
	@echo "======================================="
	cd $(POLLER_DIR) && $(PYTHON) -m pre_commit run --all-files

# Code Quality Reports
.PHONY: quality-report
quality-report:
	@echo "Generating Code Quality Report..."
	@echo "================================"
	@echo ""
	@echo "Python Files:"
	@find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*" -not -path "./node_modules/*" | wc -l | xargs echo "  Total Python files:"
	@echo ""
	@if [ -d "frontend" ]; then \
		echo "Frontend Files:"; \
		find frontend/src -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | wc -l | xargs echo "  Total TypeScript/JavaScript files:"; \
	fi
	@echo ""
	@echo "Running quality checks..."
	@echo "========================"
	-$(PYTHON) -m ruff check . --statistics 2>/dev/null || echo "Ruff not available"
	@if [ -d "frontend" ]; then \
		echo "Frontend metrics:"; \
		cd frontend && npm run lint --silent 2>/dev/null | tail -5 || echo "ESLint metrics not available"; \
	fi

# Development Quality Targets
.PHONY: dev-quality
dev-quality: format-python lint-python
	@echo "Development quality check completed for Python code!"

.PHONY: dev-quality-frontend
dev-quality-frontend: format-frontend lint-frontend
	@echo "Development quality check completed for frontend code!"

.PHONY: commit-ready
commit-ready: format lint-all type-check
	@echo ""
	@echo "🚀 CODE IS COMMIT-READY!"
	@echo "======================="
	@echo "✅ All code formatted"
	@echo "✅ All linting passed"
	@echo "✅ Type checking passed"
	@echo ""
	@echo "Ready to commit your changes!"

# CI/CD Quality Targets
.PHONY: ci-quality
ci-quality: lint-all type-check
	@echo "CI/CD quality pipeline completed!"

# Quick Quality Check (for development)
.PHONY: quick-lint
quick-lint:
	@echo "Quick quality check..."
	@echo "====================="
	cd $(POLLER_DIR) && $(PYTHON) -m ruff check . --fix
	cd $(POLLER_DIR) && $(PYTHON) -m black --check . --diff
	@if [ -d "frontend" ]; then \
		cd frontend && npm run lint --silent; \
	fi
	@echo "✅ Quick lint completed!"

# ============================================================================
# DOCKER COMMANDS
# ============================================================================

# Development Docker Commands
.PHONY: dev
dev:
	$(DOCKER_COMPOSE_DEV) up -d
	@echo "Development services started"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

.PHONY: dev-build
dev-build:
	$(DOCKER_COMPOSE_DEV) up -d --build

.PHONY: dev-logs
dev-logs:
	$(DOCKER_COMPOSE_DEV) logs -f

.PHONY: dev-stop
dev-stop:
	$(DOCKER_COMPOSE_DEV) stop

.PHONY: dev-down
dev-down:
	$(DOCKER_COMPOSE_DEV) down

# Production Docker Commands
.PHONY: prod
prod:
	$(DOCKER_COMPOSE_PROD) up -d
	@echo "Production services started"

.PHONY: prod-build
prod-build:
	$(DOCKER_COMPOSE_PROD) up -d --build

.PHONY: prod-logs
prod-logs:
	$(DOCKER_COMPOSE_PROD) logs -f

.PHONY: prod-stop
prod-stop:
	$(DOCKER_COMPOSE_PROD) stop

.PHONY: prod-down
prod-down:
	$(DOCKER_COMPOSE_PROD) down

# Docker Status
.PHONY: docker-status
docker-status:
	@echo "Docker services status:"
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Shortcuts
.PHONY: up
up: dev

.PHONY: down
down: dev-down

.PHONY: logs
logs: dev-logs
