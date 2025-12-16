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

# Install React viewer dependencies
make viewer-install
# or
cd congress-viewer && pnpm install
```

### Running Tests & API Validation

```bash
# Test API connections with minimal data
make test

# Quick validation with 5 records
make quick-fetch
```

### Data Collection

```bash
# Quick sample data (5-25 records)
make fetch-all MAX_RESULTS=25 CONGRESS=118

# Complete data collection (10,000+ records)
make fetch-everything

# Full transparency mission (fetch + analyze all)
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
```

### Viewer Application

```bash
# Start the React viewer (localhost:5173)
make viewer
# or
cd congress-viewer && pnpm run dev

# Build for production
make viewer-build

# Lint the React code
cd congress-viewer && pnpm run lint
```

## Architecture Overview

### Data Pipeline Architecture

The system uses a multi-stage pipeline:

1. **Data Fetchers**: Multiple Python scripts fetch from different API endpoints
2. **Individual Record Storage**: Each record saved as separate JSON for efficient queries
3. **Analysis Layer**: Scripts process raw data into insights
4. **Viewer Layer**: React app visualizes the analyzed data

### Key Python Modules

- **gov_data_downloader_v2.py**: Downloads bills & lobbying data, saves individual records
- **gov_data_analyzer.py**: Fetches member data & votes with party breakdowns
- **comprehensive_analyzer.py**: Orchestrates all data sources and generates unified reports
- **categorize_bills.py**: Topic classification using keywords, committees, policy areas
- **analyze_bill_sponsors.py**: Bipartisanship metrics through co-sponsorship patterns
- **analyze_member_consistency.py**: Tracks party unity scores
- **fetch_voting_records.py**: Gets detailed individual voting positions

### Data Storage Pattern

```
data/
├── congress_bills/[congress]/     # Individual bill JSONs
├── house_votes_detailed/[congress]/ # Vote records with member positions
├── members/[congress]/            # Member profiles with party affiliation
├── senate_filings/ld-1|ld-2/     # Lobbying registrations & reports
├── bill_categories/               # Bills grouped by topic
├── bill_sponsors/                 # Sponsor/cosponsor data
└── analysis/                      # Generated analysis reports
```

Each directory contains:

- Individual record files (e.g., `118_HR_82.json`)
- Index/summary files for quick lookups
- Incremental fetching support (resumes interrupted downloads)

### React Viewer (congress-viewer/)

- **Framework**: React 19 with Vite
- **Styling**: Tailwind CSS
- **Build Tool**: Vite with pnpm package manager
- **Data Visualization**: Recharts library
- **Icons**: Lucide React

## API Integration Details

### Rate Limits

- **Congress.gov**: 1000 req/hour with API key
- **Senate.gov**: 120 req/min (authenticated), 15 req/min (anonymous)

### Environment Variables (.env)

```env
DATA_GOV_API_KEY=your_api_key_here
SENATE_GOV_USERNAME=your_username  # Optional
SENATE_GOV_PASSWORD=your_password  # Optional
```

### Parallel Processing

Scripts use ThreadPoolExecutor for concurrent downloads. Adjust workers:

```python
CongressGovAPI(max_workers=10)
```

## Key Analysis Features

The platform tracks:

- **Party Unity Scores**: How often members vote with their party
- **Bipartisan Cooperation**: Cross-party bill co-sponsorship rates
- **Topic Focus by Party**: Which party introduces more bills per category
- **Lobbying Influence**: Correlation between lobbying activity and votes
- **State Delegation Patterns**: Regional voting behaviors
- **Temporal Trends**: Policy focus changes over time

## Mission Statement

@README.md

This transparency project aims to shed light on Congress and Senate activities, showing the American people how their elected officials represent them through voting patterns, party alignment, and lobbying influences.