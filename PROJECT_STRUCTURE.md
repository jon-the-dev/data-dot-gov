# Project Structure - Congressional Transparency Platform

## Overview

The project has been reorganized into a microservices architecture with three main services:

1. **Frontend** - React application for visualization
2. **Backend** - FastAPI service for data access
3. **Poller** - Python service for data collection

## Directory Structure

```
senate-gov/
├── frontend/               # React frontend application
│   ├── src/               # React source code
│   ├── public/             # Static assets
│   ├── package.json        # Node dependencies
│   ├── pnpm-lock.yaml      # Lock file
│   └── Dockerfile          # Frontend container
│
├── backend/                # FastAPI backend service
│   ├── main.py            # API endpoints
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container
│
├── poller/                 # Data collection service
│   ├── core/              # Core models and APIs
│   │   ├── api/           # Congress.gov/Senate.gov APIs
│   │   ├── models/        # Pydantic data models
│   │   └── storage/       # Storage backends
│   ├── fetchers/          # Data fetching modules
│   ├── analyzers/         # Analysis modules
│   ├── tests/             # Test files
│   ├── *.py               # Main fetcher/analyzer scripts
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Poller container
│
├── data/                   # Data storage (gitignored)
│   ├── congress_bills/    # Bill records
│   ├── members/           # Member profiles
│   ├── house_votes_detailed/ # Voting records
│   ├── senate_filings/    # Lobbying data
│   └── analysis/          # Analysis results
│
├── docs/                   # Documentation
├── config/                 # Configuration files
├── db/                     # Database schemas
├── docker/                 # Docker utilities
├── scripts/                # Utility scripts
│
├── docker-compose.yml      # Production orchestration
├── docker-compose.dev.yml  # Development orchestration
├── Makefile               # Command shortcuts
└── README.md              # Project documentation
```

## Service Architecture

### Frontend Service
- **Technology**: React 19 with Vite
- **Port**: 3000 (dev), 80 (prod)
- **Purpose**: User interface for data visualization
- **Dependencies**: Tailwind CSS, Recharts, Lucide Icons

### Backend Service
- **Technology**: FastAPI
- **Port**: 8000
- **Purpose**: REST API for data access
- **Endpoints**:
  - `/api/v1/members/{congress}` - Congressional members
  - `/api/v1/bills/{congress}` - Bills data
  - `/api/v1/votes/{congress}` - Voting records
  - `/api/v1/analysis/*` - Analysis results
  - `/api/v1/categories/*` - Bill categories

### Poller Service
- **Technology**: Python with schedule
- **Purpose**: Scheduled data collection
- **Components**:
  - Data fetchers (Congress.gov, Senate.gov)
  - Analysis engines
  - Scheduled jobs (daily comprehensive, hourly incremental)

## Docker Commands

### Development
```bash
make dev          # Start all services
make dev-build    # Build and start
make dev-logs     # View logs
make dev-stop     # Stop services
make dev-down     # Remove containers
```

### Production
```bash
make prod         # Start production
make prod-build   # Build production
make prod-logs    # View logs
make prod-stop    # Stop services
make prod-down    # Remove containers
```

### Data Collection
```bash
make fetch-quick  # Quick test (100 records)
make fetch-full   # Full collection
make analyze      # Run analysis
```

## Environment Variables

Create a `.env` file with:

```env
# API Keys
DATA_GOV_API_KEY=your_key_here
SENATE_GOV_USERNAME=your_username
SENATE_GOV_PASSWORD=your_password

# Database
POSTGRES_PASSWORD=secure_password
REDIS_PASSWORD=secure_password

# Secrets
SECRET_KEY=your_secret_key
```

## Getting Started

1. Install dependencies:
   ```bash
   make install
   ```

2. Start development environment:
   ```bash
   make dev
   ```

3. Access services:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Data Flow

1. **Poller** fetches data from government APIs
2. Data stored in `./data/` directory as JSON files
3. **Backend** serves data via REST API
4. **Frontend** visualizes data for users

## Testing

```bash
make test-backend   # Backend tests
make test-frontend  # Frontend tests
make test-poller    # Poller tests
make lint          # Run all linters
```

## Deployment

The production setup uses:
- Traefik for reverse proxy and SSL
- PostgreSQL for persistent storage
- Redis for caching
- Docker Compose for orchestration

See `docker-compose.yml` for production configuration.