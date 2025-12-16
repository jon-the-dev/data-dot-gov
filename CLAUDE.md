# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Congressional transparency platform that collects and analyzes U.S. government data to show how elected officials vote along party lines, handle lobbying influence, and represent their constituents. The project fetches voting records, lobbying data, and member information from Congress.gov and Senate.gov APIs.

## Development Commands

### Environment Setup

```bash
# Install Python dependencies
make install
# or
pipenv install

# Install Frontend dependencies
make viewer-install
# or
cd frontend && pnpm install

# Copy and configure environment variables
cp .env.example .env
# Add DATA_GOV_API_KEY from https://api.data.gov/signup/
```

### Testing & Validation

```bash
# Test API connections with minimal data
make test

# Run Python linters
make lint-python

# Run Frontend linters
make lint-frontend

# Run all linters before commit
make lint-all

# Format code automatically
make format
```

### Data Collection Commands

```bash
# Quick sample data (5 records)
make quick-fetch

# Standard data collection (25 records per category)
make fetch-all MAX_RESULTS=25 CONGRESS=118

# Smart fetch - only downloads new/missing data
make smart-fetch

# Complete data collection (10,000+ records)
make fetch-everything

# Full transparency mission (smart fetch + analyze all)
make transparency-mission
```

### Analysis Commands

```bash
# Run party voting analysis
make analyze

# Complete analysis pipeline
make full-analysis

# Deep comprehensive analysis
make deep-analysis

# Individual analysis components
make analyze-sponsors      # Bill sponsorship patterns
make categorize-bills      # Topic classification
make analyze-consistency   # Member party unity scores
make analyze-timeline      # Temporal patterns
make analyze-states        # State delegation patterns
```

### Frontend Viewer

```bash
# Start development server (localhost:5173)
make viewer
# or
cd frontend && pnpm run dev

# Build for production
make viewer-build

# Run Playwright tests
cd frontend && pnpm run test:e2e
```

### Docker Operations

```bash
# Development environment
make dev              # Start all services
make dev-logs        # View logs
make dev-stop        # Stop services

# Production deployment
make prod            # Deploy production
make prod-logs       # View production logs
```

### Database Operations

```bash
# PostgreSQL management
make db-start        # Start database
make db-create-schema # Create schema
make db-migrate-data # Migrate JSON to PostgreSQL
make db-stats        # Show statistics
make db-full-setup   # Complete setup
```

## Architecture Overview

### Three-Tier Architecture

1. **Data Layer (poller/)**
   - Python scripts for API data collection
   - Core package with unified APIs and models
   - Individual JSON file storage for efficient queries
   - PostgreSQL migration support

2. **API Layer (backend/)**
   - FastAPI backend service
   - RESTful endpoints for data access
   - CORS-enabled for frontend communication
   - Docker containerized deployment

3. **Presentation Layer (frontend/)**
   - React 19 with Vite build system
   - Tailwind CSS for styling
   - Recharts for data visualization
   - Responsive design for all devices

### Core Package Structure

```
poller/core/
├── api/
│   ├── congress.py      # Congress.gov API wrapper
│   ├── senate.py        # Senate.gov API wrapper
│   └── rate_limiter.py  # API rate limiting
├── models/
│   ├── bill.py          # Pydantic v2 models
│   ├── member.py
│   ├── vote.py
│   ├── committee.py
│   └── lobbying.py
└── storage/
    ├── file_storage.py  # JSON file operations
    ├── database.py      # PostgreSQL operations
    └── compressed.py    # Compression utilities
```

### Data Storage Pattern

```
data/
├── congress_bills/[congress]/        # Individual bill records
├── house_votes_detailed/[congress]/  # Detailed voting records
├── members/[congress]/               # Member profiles
├── senate_filings/ld-1|ld-2/        # Lobbying data
├── bill_categories/                  # Topic classifications
├── bill_sponsors/                    # Sponsorship data
├── committees/[congress]/            # Committee data
└── analysis/                         # Generated reports
```

Each directory uses individual JSON files for:
- Efficient incremental fetching
- Resumable downloads
- Parallel processing support
- Quick lookups via index files

### Key Data Fetchers

- **gov_data_downloader_v2.py**: Main data fetcher (deprecated, use core APIs)
- **gov_data_analyzer.py**: Member and vote analysis
- **comprehensive_analyzer.py**: Multi-source orchestration
- **historical_data_fetcher.py**: Parallel historical data collection
- **fetch_voting_records.py**: Detailed individual voting positions
- **fetch_committees.py**: Committee structure and bills

### Analysis Pipeline

1. **Data Collection**: Parallel fetching from multiple APIs
2. **Storage**: Individual JSON records with indexes
3. **Analysis**: Multiple analyzers process raw data
4. **Aggregation**: Comprehensive analyzer combines insights
5. **Visualization**: Frontend displays analyzed data

## API Integration

### Rate Limits
- **Congress.gov**: 1000 requests/hour with API key
- **Senate.gov**: 120 requests/min (authenticated), 15/min (anonymous)

### Parallel Processing
Scripts use ThreadPoolExecutor for concurrent operations:
```python
CongressGovAPI(max_workers=10)  # Adjust based on needs
```

### Environment Variables
Required in `.env`:
```env
DATA_GOV_API_KEY=your_api_key_here
SENATE_GOV_USERNAME=optional_username
SENATE_GOV_PASSWORD=optional_password
```

## Key Analysis Features

- **Party Unity Scores**: Member voting alignment with party
- **Bipartisan Metrics**: Cross-party bill co-sponsorship
- **Topic Analysis**: Policy focus by party and time period
- **Lobbying Correlation**: Influence patterns on votes
- **State Patterns**: Regional voting behaviors
- **Temporal Trends**: Policy evolution over time
- **Committee Activity**: Leadership and bill flow

## Docker Deployment

The project uses Docker Compose with:
- **Frontend**: Nginx serving React build
- **Backend**: FastAPI with uvicorn
- **Database**: PostgreSQL with pgAdmin
- **Cache**: Redis for performance
- **Proxy**: Traefik for SSL termination

Traefik labels configure automatic HTTPS at:
- Frontend: `congress.local.team-skynet.io`
- API: `congress-api.local.team-skynet.io`

## Testing Strategy

### Frontend Validation (IMPORTANT)
**ALWAYS use the Playwright MCP Server and tools to validate ALL frontend changes through production URLs:**
- After any frontend changes, use Playwright MCP to test `https://congress.local.team-skynet.io`
- Take screenshots for visual validation across desktop, tablet, and mobile viewports
- Test interactive features like filtering, sorting, and navigation
- Verify API data loading and error states
- Check responsive design at key breakpoints (1920x1080, 768x1024, 375x812)

Example Playwright validation workflow:
```javascript
// Navigate to production URL
await mcp__playwright__browser_navigate({ url: "https://congress.local.team-skynet.io" });
// Take snapshot for accessibility
await mcp__playwright__browser_snapshot();
// Screenshot at different viewports
await mcp__playwright__browser_resize({ width: 1920, height: 1080 });
await mcp__playwright__browser_take_screenshot({ filename: "desktop-validation.png" });
await mcp__playwright__browser_resize({ width: 375, height: 812 });
await mcp__playwright__browser_take_screenshot({ filename: "mobile-validation.png" });
```

### Other Testing Tools
- **API Tests**: `make test` validates connections
- **Python Linting**: ruff, flake8, pylint, mypy, bandit
- **Frontend Tests**: Playwright E2E, ESLint, TypeScript
- **Pre-commit Hooks**: `make install-hooks` for automation

## Common Development Tasks

```bash
# Add new data fetcher
1. Create script in poller/
2. Use core.api classes for API access
3. Use core.storage for data persistence
4. Add Makefile target for easy execution

# Add new analysis
1. Create analyzer in poller/analyzers/
2. Import data from storage
3. Generate reports in data/analysis/
4. Update comprehensive_analyzer.py

# Add frontend feature
1. Create component in frontend/src/components/
2. Add route in frontend/src/App.jsx
3. Use dataService for API calls
4. Follow existing Tailwind patterns
```

## Performance Optimization

- **Incremental Fetching**: Scripts resume from last successful record
- **Parallel Downloads**: ThreadPoolExecutor with configurable workers
- **Individual File Storage**: No large JSON parsing overhead
- **Index Files**: Quick lookups without scanning directories
- **Materialized Views**: PostgreSQL views for complex queries
- **Redis Caching**: API response caching in production

## Mission

This transparency project aims to shed light on Congress and Senate activities, showing the American people how their elected officials represent them through voting patterns, party alignment, and lobbying influences.