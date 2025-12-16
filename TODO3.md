# TODO3.md - Committee Enhancement Analysis

## Current State Analysis

### What We Have

1. **Basic Committee Data Structure**
   - Committee listings by chamber (House, Senate, Joint)
   - Basic committee information (name, code, type, jurisdiction)
   - Subcommittee hierarchy structure
   - Committee detail pages with placeholder data

2. **Limited Data Integration**
   - Bills associated with committees (partial - searches for committee references in bill text)
   - Member associations (derived from bill sponsorship activity)
   - Basic analytics (activity scores based on bill counts)

3. **Missing Critical Features**
   - No actual committee membership data (chair, ranking member, members)
   - No hearing or meeting schedules
   - No committee reports or documents
   - No voting records within committees
   - No historical data or timeline of committee activities
   - No integration with lobbying data for committee influence analysis

### Frontend Issues

The Senate Judiciary Committee page (<https://congress.local.team-skynet.io/committees/ssju00>) shows empty data because:

- The committee code 'ssju00' doesn't match the actual Senate Judiciary Committee code format in Congress.gov
- Committee member data is only inferred from bill sponsorship, not actual membership
- No hearing/meeting data is being fetched or displayed
- Timeline component receives empty data arrays

## Required Enhancements

### 1. Expand Committee Data Fetching

#### A. Committee Membership

- **Congress.gov API** provides `/committee/{chamber}/{committeeCode}/members` endpoint
- Need to fetch and store actual committee membership with roles:
  - Chair/Chairwoman
  - Ranking Member
  - Members by party
  - Ex-officio members
  - Membership start/end dates

#### B. Committee Activities

- **Hearings**: `/committee/{chamber}/{committeeCode}/hearings`
  - Date, time, location
  - Witness list
  - Topics/agenda
  - Video/transcript links
- **Meetings**: `/committee/{chamber}/{committeeCode}/meetings`
  - Business meetings
  - Markups
  - Executive sessions
- **Reports**: `/committee/{chamber}/{committeeCode}/reports`
  - Committee reports on bills
  - Investigation reports
  - Annual/periodic reports

#### C. Committee Communications

- Press releases
- Statements
- Letters to agencies
- Oversight correspondence

### 2. Backend Service Enhancements

```python
# New methods needed in committee_service.py:

async def fetch_committee_members(committee_id: str, congress: int):
    """Fetch actual committee membership from Congress.gov API"""
    # Implementation to fetch from /committee/{chamber}/{code}/members

async def fetch_committee_hearings(committee_id: str, congress: int):
    """Fetch committee hearings schedule and history"""
    # Implementation to fetch from /committee/{chamber}/{code}/hearings

async def fetch_committee_meetings(committee_id: str, congress: int):
    """Fetch committee meetings and markups"""
    # Implementation to fetch from /committee/{chamber}/{code}/meetings

async def fetch_committee_documents(committee_id: str, congress: int):
    """Fetch committee reports and documents"""
    # Implementation to fetch from /committee/{chamber}/{code}/reports
```

### 3. Data Model Enhancements

```python
# Enhanced committee models needed:

class CommitteeMember(BaseModel):
    bioguideId: str
    name: str
    party: str
    state: str
    role: str  # Chair, Ranking Member, Member
    start_date: Optional[str]
    end_date: Optional[str]
    seniority_rank: Optional[int]

class CommitteeHearing(BaseModel):
    hearing_id: str
    title: str
    date: str
    time: Optional[str]
    location: Optional[str]
    witnesses: List[str]
    topics: List[str]
    video_url: Optional[str]
    transcript_url: Optional[str]
    status: str  # Scheduled, Completed, Cancelled

class CommitteeMeeting(BaseModel):
    meeting_id: str
    type: str  # Business Meeting, Markup, Executive Session
    date: str
    time: Optional[str]
    agenda: Optional[str]
    bills_considered: List[str]
    outcome: Optional[str]
```

### 4. Frontend Component Enhancements

#### A. Enhanced Committee Detail Page

- **Leadership Section**: Display Chair, Ranking Member prominently
- **Members Grid**: Show all members with party affiliation, state, and seniority
- **Hearings Tab**: Upcoming and past hearings with witness lists
- **Meetings Tab**: Meeting schedule and markup sessions
- **Documents Tab**: Committee reports and publications
- **Analytics Dashboard**:
  - Activity timeline chart
  - Bill progression funnel
  - Member participation rates
  - Bipartisan cooperation score

#### B. New Components Needed

- `CommitteeLeadership.jsx` - Display committee leadership
- `CommitteeMembersGrid.jsx` - Full member roster with filtering
- `HearingsList.jsx` - Hearing schedule and archives
- `MeetingsList.jsx` - Meeting schedule and outcomes
- `CommitteeDocuments.jsx` - Reports and publications viewer
- `CommitteeAnalyticsDashboard.jsx` - Data visualizations

### 5. Additional Data Sources Integration

#### ProPublica Congress API

- More detailed member information
- Committee leadership changes
- Member attendance records

#### GovTrack.us

- Historical committee data
- Member ideology scores
- Bill success rates by committee

#### OpenSecrets API

- Lobbying activity targeting specific committees
- Campaign contributions to committee members
- Industry influence on committee decisions

### 6. Implementation Priority

1. **Phase 1 - Core Data** (High Priority)
   - Fix committee code mapping issues
   - Implement actual committee membership fetching
   - Display basic member roster with roles

2. **Phase 2 - Activities** (High Priority)
   - Fetch and display hearings
   - Fetch and display meetings
   - Create timeline of committee activities

3. **Phase 3 - Enhanced Analytics** (Medium Priority)
   - Integrate lobbying data from OpenSecrets
   - Calculate committee influence scores
   - Track bill success rates through committee

4. **Phase 4 - Historical Data** (Low Priority)
   - Historical membership changes
   - Past hearing archives
   - Committee evolution over congresses

## Technical Implementation Steps

### Step 1: Fix Committee Code Issues

The current system uses codes like 'ssju00' but Congress.gov uses 'SSJU'. Need to:

- Update committee code format in fetchers
- Add code normalization in API calls
- Update frontend routing to use correct codes

### Step 2: Enhance Data Fetcher

```python
# fetch_committees.py enhancements:
def fetch_committee_members(self, congress, chamber, committee_code):
    endpoint = f"/committee/{congress}/{chamber}/{committee_code}/members"
    # Fetch and parse member data with roles

def fetch_committee_schedule(self, congress, chamber, committee_code):
    # Fetch both hearings and meetings
    hearings = self.fetch_committee_hearings(congress, chamber, committee_code)
    meetings = self.fetch_committee_meetings(congress, chamber, committee_code)
    return {"hearings": hearings, "meetings": meetings}
```

### Step 3: Update Backend Services

- Modify `committee_service.py` to use new fetched data
- Add caching for committee member data (changes infrequently)
- Implement real-time updates for hearing schedules

### Step 4: Frontend Updates

- Update `CommitteeDetail.jsx` to display all new data
- Add loading states for each data section
- Implement error boundaries for partial data failures
- Add data refresh capabilities

## Success Metrics

1. **Data Completeness**
   - All committees show actual members (not inferred)
   - Hearing schedules available for active committees
   - Historical data for at least 2 congresses

2. **User Experience**
   - Page load time under 2 seconds
   - Intuitive navigation between committee sections
   - Mobile-responsive design for all new components

3. **Data Accuracy**
   - Member roles match official records
   - Hearing schedules update within 24 hours
   - Bill associations correctly mapped

## Conclusion

The current committee implementation provides a foundation but lacks the depth needed for meaningful transparency. By implementing these enhancements, particularly the integration of actual membership data and hearing schedules, the platform will provide citizens with comprehensive visibility into committee operations - where much of Congress's real work happens.

The top priority should be fixing the committee code mapping and implementing actual member fetching from Congress.gov API, as this will immediately resolve the empty data issue on committee detail pages.
