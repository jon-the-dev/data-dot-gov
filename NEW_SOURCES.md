# NEW_SOURCES.md - Additional Public API Sources for Committee Data

## Primary Government APIs

### 1. Congress.gov API (Already Integrated)
- **Endpoint**: https://api.congress.gov/v3
- **Authentication**: API key required (already have DATA_GOV_API_KEY)
- **Committee Endpoints Available**:
  - `/committee/{congress}/{chamber}` - List committees
  - `/committee/{congress}/{chamber}/{committeeCode}` - Committee details
  - `/committee/{congress}/{chamber}/{committeeCode}/members` - Committee membership
  - `/committee/{congress}/{chamber}/{committeeCode}/bills` - Bills referred to committee
  - `/committee/{congress}/{chamber}/{committeeCode}/reports` - Committee reports
  - `/committee/{congress}/{chamber}/{committeeCode}/hearings` - Committee hearings
  - `/committee/{congress}/{chamber}/{committeeCode}/nominations` - Nominations

### 2. Senate.gov API (Partially Integrated)
- **Endpoint**: https://www.senate.gov/api/
- **Authentication**: Optional (higher rate limits with auth)
- **Committee Features**:
  - Committee schedules and hearings
  - Real-time hearing updates
  - Witness testimony documents
  - Committee membership rosters
  - Webcast links for hearings

## Third-Party Political Data APIs

### 5. GovTrack.us Data
- **Access Method**: Bulk data downloads and web scraping
- **Website**: https://www.govtrack.us/
- **Committee Features**:
  - Historical committee membership (1973-present)
  - Committee activity statistics
  - Bill success rates by committee
  - Member ideology scores
  - Committee report cards
- **Format**: JSON, CSV, and YAML bulk downloads
- **Unique Value**: Historical analysis and performance metrics

### 6. OpenSecrets API
- **Endpoint**: https://www.opensecrets.org/api
- **Authentication**: API key required
- **Committee-Related Features**:
  - `congCmteIndus` - Total raised by committee members from industries
  - Lobbying targeting specific committees
  - Campaign contributions to committee members
  - Committee member financial disclosures
  - Industry influence on committee decisions
- **Rate Limits**: 200 calls per day (default)
- **Unique Value**: Financial influence and lobbying data

### 7. FEC (Federal Election Commission) API
- **Endpoint**: https://api.open.fec.gov/v1
- **Authentication**: API key required (free)
- **Committee-Related Features**:
  - Campaign finance data for committee members
  - PAC contributions to committee members
  - Expenditure data
  - Financial disclosure reports
- **Rate Limits**: 1000 requests per hour
- **Unique Value**: Official campaign finance records

## Specialized Data Sources

### 8. C-SPAN API
- **Endpoint**: Not publicly documented (web scraping required)
- **Website**: https://www.c-span.org/
- **Committee Features**:
  - Video archives of hearings
  - Transcripts (when available)
  - Witness testimony videos
  - Historical hearing footage
- **Access Method**: Web scraping or RSS feeds

### 9. Government Publishing Office (GPO)
- **Endpoint**: https://api.govinfo.gov/
- **Authentication**: API key required
- **Committee Features**:
  - Published hearing transcripts
  - Committee prints
  - Committee reports
  - Legislative calendars
- **Format**: XML, PDF, TXT
- **Unique Value**: Official government documents

### 10. Library of Congress APIs
- **Endpoint**: https://www.loc.gov/apis/
- **Authentication**: Some endpoints require keys
- **Committee Features**:
  - Historical committee records
  - Committee jurisdiction evolution
  - Archived committee websites
  - Committee photographs and media

## RSS and Real-Time Feeds

### 11. Committee RSS Feeds
Most committees provide RSS feeds for:
- Hearing schedules
- Press releases
- Committee news
- Markup schedules

**Senate Committee RSS Pattern**:
`https://www.{committee}.senate.gov/rss/feeds/`

**House Committee RSS Pattern**:
`https://{committee}.house.gov/rss.xml`

### 12. Congressional Chronicle
- **Source**: Library of Congress
- **Features**:
  - Real-time floor proceedings
  - Committee meeting notifications
  - Bill status changes
- **Format**: RSS/XML feeds

## Implementation Recommendations

### Priority 1 - Immediate Integration
1. **ProPublica Congress API** - For committee membership and leadership roles
2. **GPO API** - For official hearing transcripts and reports
3. **Committee RSS Feeds** - For real-time updates

### Priority 2 - Enhanced Analytics
1. **OpenSecrets API** - For lobbying and financial influence data
2. **FEC API** - For campaign finance connections
3. **GovTrack.us** - For historical data and performance metrics

### Priority 3 - Rich Media
1. **C-SPAN** - For video archives
2. **Library of Congress** - For historical records

## API Integration Strategy

### 1. Data Aggregation Pipeline
```python
# Proposed architecture for multi-source integration
class CommitteeDataAggregator:
    sources = {
        'congress_gov': CongressGovAPI(),      # Primary source
        'propublica': ProPublicaAPI(),         # Leadership & roles
        'opensecrets': OpenSecretsAPI(),       # Financial data
        'govtrack': GovTrackAPI(),             # Historical & metrics
        'gpo': GPOApi(),                       # Documents
    }

    def get_complete_committee_data(committee_id, congress):
        # Aggregate from multiple sources
        base_data = sources['congress_gov'].get_committee(committee_id)
        base_data['leadership'] = sources['propublica'].get_leadership(committee_id)
        base_data['financial'] = sources['opensecrets'].get_finances(committee_id)
        base_data['metrics'] = sources['govtrack'].get_metrics(committee_id)
        base_data['documents'] = sources['gpo'].get_documents(committee_id)
        return base_data
```

### 2. Caching Strategy
- **Static Data**: Committee structure, historical data (cache 24 hours)
- **Semi-Dynamic**: Membership, bills (cache 6 hours)
- **Dynamic**: Hearings, schedules (cache 1 hour)
- **Real-time**: RSS feeds, votes (no cache)

### 3. Rate Limit Management
```python
# Rate limiter configuration per API
RATE_LIMITS = {
    'congress_gov': {'requests': 1000, 'period': 'hour'},
    'propublica': {'requests': 5000, 'period': 'day'},
    'opensecrets': {'requests': 200, 'period': 'day'},
    'fec': {'requests': 1000, 'period': 'hour'},
    'gpo': {'requests': 1000, 'period': 'hour'},
}
```

## Data Enrichment Opportunities

### 1. Committee Influence Score
Combine data from multiple sources:
- Bill passage rates (Congress.gov)
- Member seniority (ProPublica)
- Lobbying activity (OpenSecrets)
- Media coverage (C-SPAN appearances)

### 2. Financial Transparency Dashboard
Integrate:
- Member financial disclosures (OpenSecrets)
- Campaign contributions (FEC)
- Lobbying meetings (Senate.gov)
- Industry donations (OpenSecrets)

### 3. Historical Committee Evolution
Track over time:
- Membership changes (GovTrack)
- Jurisdiction shifts (Library of Congress)
- Leadership transitions (ProPublica)
- Activity levels (Congress.gov)

## Authentication Requirements

### APIs Requiring Keys
1. **Congress.gov** - $DATA_GOV_API_KEY (already have)
2. **ProPublica** - Free registration at https://www.propublica.org/datastore/api/propublica-congress-api
3. **OpenSecrets** - Apply at https://www.opensecrets.org/api/admin/
4. **FEC** - Register at https://api.data.gov/signup/
5. **GPO** - Register at https://api.govinfo.gov/docs/

### Public APIs (No Key Required)
1. House Clerk API
2. Most committee RSS feeds
3. GovTrack bulk downloads

## Next Steps

1. **Register for API Keys**:
   - ProPublica Congress API
   - OpenSecrets API
   - FEC API
   - GPO API

2. **Implement Priority 1 Sources**:
   - Add ProPublica integration for committee leadership
   - Add GPO integration for hearing transcripts
   - Set up RSS feed monitoring

3. **Enhance Committee Service**:
   - Create data aggregator class
   - Implement multi-source caching
   - Add rate limit management

4. **Update Frontend**:
   - Display enriched committee data
   - Add financial transparency widgets
   - Show real-time hearing schedules