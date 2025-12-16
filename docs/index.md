# Senate.gov & Congress.gov Data Collection Platform

A comprehensive data collection and analysis platform for U.S. government transparency. This project fetches and analyzes voting records, lobbying data, and Congressional member information to show how elected officials vote along party lines and represent their constituents.

## 🎯 Project Goal

Build a transparency website that shows U.S. residents:
- How their representatives (R/D/I) vote on legislation
- Party voting patterns and bipartisanship metrics
- Lobbying activity and influence
- Individual member voting records
- State-by-state representation

## 📚 Documentation Navigation

### Getting Started
- **[Installation & Setup](getting-started/installation.md)** - Get up and running quickly
- **[Quick Start Guide](getting-started/quick-start.md)** - First steps and basic usage

### Development
- **[Development Guide](development/development-guide.md)** - Development workflow and best practices
- **[Testing Guide](development/testing-guide.md)** - Running tests and validation
- **[Code Quality](development/code-quality.md)** - Linting, formatting, and standards
- **[Contributing](development/contributing.md)** - How to contribute to the project

### Features & Analysis
- **[Data Collection](features/data-collection.md)** - How we collect government data
- **[Party Analysis](features/party-analysis.md)** - Voting patterns and party alignment
- **[Bill Categorization](features/bill-categorization.md)** - Topic classification and analysis
- **[Lobbying Analysis](features/lobbying-analysis.md)** - Lobbying influence tracking
- **[Frontend Viewer](features/frontend-viewer.md)** - React application for data visualization

### Architecture & Deployment
- **[System Architecture](architecture/system-architecture.md)** - High-level system design
- **[Deployment Guide](deployment/deployment-guide.md)** - Production deployment instructions

### API & Reference
- **[API Reference](api/api-reference.md)** - Complete API documentation
- **[Data Schema](reference/data-schema.md)** - Data structure and formats
- **[Make Commands](reference/make-commands.md)** - Available make targets

### Reports & Analysis
- **[Consolidation Report](reports/consolidation-report.md)** - Code consolidation results
- **[Voting Analysis](reports/voting-analysis-summary.md)** - Comprehensive voting pattern analysis
- **[Data Validation](reports/react-viewer-validation-report.md)** - Frontend validation results

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pipenv
- API keys (optional but recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/senate-gov.git
cd senate-gov

# Install dependencies
make install
# or
pipenv install requests python-dotenv
```

### Configuration

Create a `.env` file with your API credentials:

```env
# Congress.gov API (via data.gov)
DATA_GOV_API_KEY=your_api_key_here

# Senate.gov API (optional - for authenticated access)
SENATE_GOV_USERNAME=your_username
SENATE_GOV_PASSWORD=your_password
```

Get your free API key at: https://api.data.gov/signup/

### Quick Test

```bash
# Test API connections
make test

# Fetch sample data (5 records each)
make quick-fetch
```

## 📊 Data Collection

### Using Make Commands

```bash
# Fetch all data types (25 records each)
make fetch-all

# Fetch specific data types
make fetch-members   # Congressional members with party affiliations
make fetch-bills     # Recent bills
make fetch-votes     # House votes with party breakdowns
make fetch-lobbying  # Senate lobbying filings

# Fetch larger datasets
make fetch-large     # 100+ records per category

# Custom parameters
make fetch-all MAX_RESULTS=50 CONGRESS=117
```

### Using Python Scripts Directly

#### 1. **Individual Record Storage** (`gov_data_downloader_v2.py`)

Saves each record as a separate JSON file for efficient querying:

```bash
# Download bills
pipenv run python gov_data_downloader_v2.py --congress-bills --max-results 25

# Download lobbying data
pipenv run python gov_data_downloader_v2.py --senate-filings --senate-lobbyists --max-results 50

# Download everything
pipenv run python gov_data_downloader_v2.py --max-results 25
```

#### 2. **Party Voting Analysis** (`gov_data_analyzer.py`)

Fetches detailed voting records with party breakdowns:

```bash
# Fetch members and votes
pipenv run python gov_data_analyzer.py --members --votes --max-members 100 --max-votes 50

# Analyze voting patterns
pipenv run python gov_data_analyzer.py --analyze

# Specific congress
pipenv run python gov_data_analyzer.py --congress 117 --chamber house
```

#### 3. **Bill Categorization** (`categorize_bills.py`)

Categorizes bills by topic and analyzes party focus patterns:

```bash
# Categorize all bills by topic
pipenv run python categorize_bills.py --congress 118 --save-categories

# Quick test with sample data
pipenv run python categorize_bills.py --max-bills 25 --verbose

# Save categorized bills to separate files
pipenv run python categorize_bills.py --save-categories --output-dir data
```

#### 4. **Bill Sponsorship Analysis** (`analyze_bill_sponsors.py`)

Analyzes bill sponsor and co-sponsor patterns:

```bash
# Analyze sponsorship patterns
pipenv run python analyze_bill_sponsors.py --congress 118

# Limited analysis for testing
pipenv run python analyze_bill_sponsors.py --max-bills 50 --verbose
```

#### 5. **Comprehensive Analysis** (`comprehensive_analyzer.py`)

Complete platform combining all data sources:

```bash
# Fetch and analyze everything
pipenv run python comprehensive_analyzer.py --fetch --analyze

# Just analyze existing data
pipenv run python comprehensive_analyzer.py --analyze

# Custom limits
pipenv run python comprehensive_analyzer.py --fetch --max-items 100
```

## 📁 Data Structure

```
data/
├── congress_bills/
│   └── 118/
│       ├── 118_HR_82.json         # Individual bill
│       ├── 118_S_5319.json
│       └── index.json             # Bill index
├── house_votes_detailed/
│   └── 118/
│       ├── 118_1_500.json         # Vote with member positions
│       └── index.json
├── members/
│   └── 118/
│       ├── 118_A000370.json       # Individual member
│       └── summary.json           # Party breakdown
├── senate_filings/
│   ├── ld-1/                      # Lobbying registrations
│   └── ld-2/                      # Quarterly reports
├── senate_lobbyists/
│   ├── john_doe.json
│   └── index.json
├── bill_categories/
│   ├── healthcare.json             # Bills categorized by topic
│   ├── technology.json
│   ├── defense_military.json
│   └── index.json                  # Category summary
├── bill_details/
│   ├── 118_hr_1555.json           # Bill subjects & committees
│   └── index.json
├── bill_sponsors/
│   ├── 118_hr_1555.json           # Sponsor & cosponsor data
│   └── index.json
└── analysis/
    ├── party_voting_analysis.json
    ├── bill_categories_analysis.json
    ├── bill_sponsors_analysis.json
    └── comprehensive_report.json
```

## 📈 Analysis Features

### Party Voting Patterns
- **Party Unity Scores**: How often members vote with their party
- **Bipartisan vs Partisan Votes**: Identify cross-party cooperation
- **Swing Voters**: Members who frequently break party lines

### Bill Categorization & Topics
- **Smart Topic Classification**: Categorizes bills into 10+ topic areas using keywords, committees, and policy areas
- **Party Focus Analysis**: Which party introduces more bills in each category (Healthcare, Defense, Technology, etc.)
- **Success Rates by Category**: Bills becoming law by topic and party
- **Trending Topics**: Identifies growing/declining policy focus areas over time
- **Committee Activity**: Most active committees by party affiliation

### Bill Sponsorship Analysis
- **Cross-Party Co-sponsorship**: Measures bipartisan cooperation on bills
- **Sponsor/Co-sponsor Patterns**: Party introduction and support rates
- **Introduction vs Success**: Which party's bills are more likely to become law

### Individual Member Tracking
- Party affiliation (R/D/I)
- Voting record on every bill
- Times voted against party majority
- State and district representation

### Lobbying Analysis
- Top lobbying issues by frequency
- Major lobbying organizations
- Filing trends over time
- Issue-based lobbying patterns

## 🔧 Advanced Usage

### Parallel Processing

The scripts use `ThreadPoolExecutor` for faster downloads:

```python
# Adjust worker count
pipenv run python gov_data_analyzer.py --max-workers 10
```

### Resume Interrupted Downloads

Downloads are incremental and resume automatically:

```bash
# Will skip already downloaded records
make fetch-all
```

### Custom Analysis

```python
from comprehensive_analyzer import ComprehensiveAnalyzer

analyzer = ComprehensiveAnalyzer(base_dir="data")
report = analyzer.generate_comprehensive_report()

# Access specific analyses
party_voting = report["analyses"]["party_voting"]
lobbying = report["analyses"]["lobbying"]
```

## 📊 Website Integration

The data structure enables building features like:

### 1. Representative Profiles
```json
{
  "bioguideId": "A000370",
  "name": "Alma Adams",
  "party": "Democratic",
  "state": "NC",
  "chamber": "house",
  "voting_record": [...]
}
```

### 2. Vote Breakdowns
```json
{
  "rollCall": 500,
  "question": "On Passage of H.R. 82",
  "party_breakdown": {
    "D": {"yea": 150, "nay": 50},
    "R": {"yea": 175, "nay": 25}
  },
  "result": "Passed"
}
```

### 3. Bipartisanship Metrics
```json
{
  "bipartisan_percentage": 35.2,
  "party_unity_scores": {
    "D": 89.5,
    "R": 91.2
  }
}
```

## 🔒 API Compliance

### Rate Limits
- **Senate.gov**: 120 req/min (authenticated), 15 req/min (anonymous)
- **Congress.gov**: 1000 req/hour with API key

### Terms of Service
- Data citation required with access date
- Cannot vouch for analyses after download
- Respect rate limits at all times

## 🛠 Development

### Running Tests
```bash
make test
```

### Development Workflow
```bash
# Fetch small dataset for development
make dev-senate
make dev-congress

# Run analysis
make dev-analyze
```

### Cleaning Data
```bash
make clean           # Remove all data
make clean-bills     # Remove bills only
make clean-votes     # Remove votes only
make clean-analysis  # Remove analysis results
```

## 📝 Make Targets Reference

| Target | Description |
|--------|-------------|
| `make install` | Install dependencies |
| `make quick-fetch` | Fetch 5 records of each type |
| `make fetch-all` | Fetch 25 records of each type |
| `make fetch-large` | Fetch 100+ records of each type |
| `make analyze` | Run voting pattern analysis |
| `make comprehensive` | Full fetch and analysis |
| `make stats` | Show data statistics |
| `make backup` | Create timestamped backup |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and analysis
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This tool accesses public government data. Users must:
- Respect API rate limits
- Cite data sources appropriately
- Acknowledge that analyses are derived from downloaded data
- Follow all terms of service for senate.gov and congress.gov

## 🔗 Resources

- [Congress.gov API Documentation](https://api.congress.gov/)
- [Senate Lobbying Disclosure](https://lda.senate.gov/)
- [Data.gov API Key](https://api.data.gov/signup/)

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review API terms of service

---

Built to increase government transparency and civic engagement 🇺🇸