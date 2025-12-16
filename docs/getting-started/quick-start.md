# Quick Start Guide

Welcome to the Congressional Transparency Platform! This guide will get you up and running quickly.

## Prerequisites

- Python 3.8+
- Node.js 18+ (for React viewer)
- Docker (optional, for database)
- Git

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/senate-gov.git
cd senate-gov

# Install Python dependencies
make install
# or
pipenv install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

Add your API keys:
```env
DATA_GOV_API_KEY=your_api_key_here
SENATE_GOV_USERNAME=your_username  # Optional
SENATE_GOV_PASSWORD=your_password  # Optional
```

Get your free API key at: https://api.data.gov/signup/

### 3. Test API Connections

```bash
# Test API connectivity
make test
```

### 4. Fetch Sample Data

```bash
# Fetch sample data (5 records each)
make quick-fetch
```

## Quick Commands

### Data Collection
```bash
# Fetch congressional data
make fetch-all                    # 25 records each type
make fetch-large                  # 100+ records each type
make fetch-everything             # Complete dataset

# Fetch specific data types
make fetch-members               # Congressional members
make fetch-bills                 # Recent bills
make fetch-votes                 # Voting records
make fetch-lobbying              # Lobbying data
```

### Analysis
```bash
# Run analysis
make analyze                     # Basic analysis
make full-analysis               # Complete analysis pipeline
make deep-analysis               # Comprehensive analysis

# Generate reports
make stats                       # Data statistics
make comprehensive               # Full fetch + analysis
```

### React Viewer
```bash
# Install frontend dependencies
make viewer-install

# Start development server
make viewer                      # Starts on localhost:5173

# Build for production
make viewer-build
```

### Database (Optional)
```bash
# Start database
make db-start

# Setup database
make db-full-setup

# View database
make db-admin                    # pgAdmin at localhost:8080
```

## Project Structure

```
senate-gov/
├── docs/                        # Documentation (you are here!)
├── data/                        # Collected congressional data
├── congress-viewer/             # React frontend application
├── core/                        # Core analysis modules
├── fetchers/                    # Data collection scripts
├── analyzers/                   # Analysis scripts
└── scripts/                     # Utility scripts
```

## Next Steps

1. **Explore the Data**: Check the `data/` directory for collected information
2. **Run Analysis**: Use `make analyze` to generate insights
3. **View Results**: Start the React viewer with `make viewer`
4. **Read Documentation**: Explore the `docs/` directory for detailed guides

## Common Issues

### API Rate Limits
```bash
# Reduce workers if hitting rate limits
make fetch-all MAX_WORKERS=2
```

### Permission Errors
```bash
# Fix file permissions
chmod +x scripts/*.sh
```

### Database Issues
```bash
# Reset database if needed
make db-reset
make db-full-setup
```

## Getting Help

- **Documentation**: Browse `./docs/` for detailed guides
- **Issues**: Open an issue on GitHub
- **API Docs**: Check [Congress.gov API](https://api.congress.gov/)

## What's Next?

- [Architecture Overview](../architecture/) - Understand the system design
- [Development Guide](../development/) - Learn about development workflows
- [Features](../features/) - Explore available features
- [API Reference](../api/) - API endpoints and data structures

Happy exploring! 🇺🇸