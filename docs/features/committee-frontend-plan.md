# Committee/Subcommittee Frontend Implementation Plan

## Overview
This document outlines the frontend changes needed to display committee and subcommittee data in the Congressional Transparency Portal (React viewer).

## Data Structure Available

### Committee Data (from backend)
```json
{
  "committees": {
    "118": {
      "house": [
        {
          "systemCode": "HSAG",
          "name": "House Agriculture Committee",
          "type": "Standing",
          "chamber": "house",
          "url": "https://agriculture.house.gov/",
          "subcommittees": [...],
          "parent": null
        }
      ],
      "senate": [...],
      "joint": [...]
    }
  },
  "committee_bills": {
    "HSAG": {
      "bills": [...],
      "stats": {
        "total_bills": 45,
        "party_breakdown": {
          "R": 28,
          "D": 17
        }
      }
    }
  }
}
```

### Bill Committee Activity
```json
{
  "bill_id": "118_HR_1234",
  "committees": [
    {
      "systemCode": "HSAG",
      "name": "House Agriculture Committee",
      "activities": [
        {
          "name": "Referred to",
          "date": "2023-03-15"
        },
        {
          "name": "Markup",
          "date": "2023-04-10"
        }
      ]
    }
  ]
}
```

## Implementation Plan

### Phase 1: Committee List & Details Pages

#### 1.1 Committee List Page (`/committees`)

**Route**: `/committees/:congress?/:chamber?`

**Components to Create**:
```typescript
// src/pages/CommitteesPage.tsx
interface CommitteesPageProps {
  congress?: number;
  chamber?: 'house' | 'senate' | 'joint';
}

// src/components/committees/CommitteeList.tsx
interface CommitteeListProps {
  committees: Committee[];
  onCommitteeSelect: (committee: Committee) => void;
}

// src/components/committees/CommitteeCard.tsx
interface CommitteeCardProps {
  committee: Committee;
  billCount?: number;
  memberCount?: number;
}
```

**Features**:
- Filter by chamber (House/Senate/Joint)
- Filter by committee type (Standing/Select/Special)
- Search committees by name
- Sort by activity level (bill count)
- Committee cards showing:
  - Committee name and type
  - Chair information
  - Number of bills handled
  - Number of subcommittees
  - Recent activity indicator

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Congressional Committees                                     │
├─────────────────────────────────────────────────────────────┤
│ [Congress 118 ▼] [All Chambers ▼] [Search committees...]    │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│ │ House Agri. │ │ Senate HELP │ │ Joint Econ. │            │
│ │ Standing    │ │ Standing    │ │ Joint       │            │
│ │ 45 bills    │ │ 67 bills    │ │ 12 bills    │            │
│ │ 3 subcomm.  │ │ 2 subcomm.  │ │ 0 subcomm.  │            │
│ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 1.2 Committee Detail Page (`/committees/:systemCode`)

**Route**: `/committees/:systemCode/:congress?`

**Components to Create**:
```typescript
// src/pages/CommitteeDetailPage.tsx
interface CommitteeDetailPageProps {
  systemCode: string;
  congress?: number;
}

// src/components/committees/CommitteeHeader.tsx
interface CommitteeHeaderProps {
  committee: Committee;
  stats: CommitteeStats;
}

// src/components/committees/SubcommitteeList.tsx
interface SubcommitteeListProps {
  subcommittees: Committee[];
  parentCommittee: Committee;
}

// src/components/committees/CommitteeBillsTable.tsx
interface CommitteeBillsTableProps {
  bills: Bill[];
  committee: Committee;
  pagination: PaginationProps;
}
```

**Features**:
- Committee overview and description
- Leadership information (Chair, Ranking Member)
- Subcommittee listing
- Bills handled by committee
- Committee activity timeline
- Party breakdown of committee members
- Links to official committee website

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ House Committee on Agriculture                               │
│ Standing Committee • 118th Congress                         │
├─────────────────────────────────────────────────────────────┤
│ Chair: Rep. Thompson (R-PA) | Ranking: Rep. Scott (D-GA)   │
│ Members: 28 Republicans, 17 Democrats                       │
├─────────────────────────────────────────────────────────────┤
│ [Overview] [Bills] [Subcommittees] [Members] [Activity]    │
├─────────────────────────────────────────────────────────────┤
│ Statistics                                                   │
│ • 45 bills referred                                        │
│ • 12 bills reported                                        │
│ • 8 hearings held                                          │
│ • 3 subcommittees                                         │
├─────────────────────────────────────────────────────────────┤
│ Recent Bills                                                │
│ H.R. 1234 - Farm Bill Extension          [Referred] 3/15   │
│ H.R. 2345 - Agricultural Innovation      [Markup]   4/10   │
│ H.R. 3456 - Rural Development           [Reported]  4/25   │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: Bill-Committee Integration

#### 2.1 Enhanced Bill Detail Pages

**Add Committee Section to Bill Pages**:

```typescript
// src/components/bills/BillCommitteeActivity.tsx
interface BillCommitteeActivityProps {
  bill: Bill;
  committeeActivities: CommitteeActivity[];
}
```

**Features**:
- Show which committees a bill was referred to
- Display committee actions (referral, markup, reported)
- Committee action timeline
- Links to committee pages

#### 2.2 Committee Filter on Bills Page

**Add Committee Filter**:
```typescript
// Enhanced BillsPage filters
interface BillFilters {
  congress: number;
  chamber?: string;
  party?: string;
  committee?: string;  // NEW
  status?: string;
  searchTerm?: string;
}
```

### Phase 3: Advanced Analytics

#### 3.1 Committee Performance Analytics

**Components**:
```typescript
// src/components/committees/CommitteeAnalytics.tsx
interface CommitteeAnalyticsProps {
  committee: Committee;
  congress: number;
}

// src/components/charts/CommitteeActivityChart.tsx
interface CommitteeActivityChartProps {
  activityData: CommitteeActivity[];
  timeRange: string;
}
```

**Analytics to Display**:
- Bills processed over time
- Success rate (reported vs referred)
- Bipartisan vs partisan activity
- Hearing frequency
- Member attendance rates

#### 3.2 Cross-Committee Analysis

**New Page**: `/analytics/committees`

**Features**:
- Compare committee productivity
- Most/least active committees
- Committee collaboration network
- Topic focus by committee

### Phase 4: Data Integration & API Updates

#### 4.1 Frontend Data Service Updates

```typescript
// src/services/committeeService.ts
export class CommitteeService {
  async getCommittees(congress: number, chamber?: string): Promise<Committee[]> {
    const response = await api.get(`/committees`, {
      params: { congress, chamber }
    });
    return response.data;
  }

  async getCommitteeDetail(systemCode: string, congress: number): Promise<CommitteeDetail> {
    const response = await api.get(`/committees/${systemCode}`, {
      params: { congress }
    });
    return response.data;
  }

  async getCommitteeBills(systemCode: string, congress: number): Promise<Bill[]> {
    const response = await api.get(`/committees/${systemCode}/bills`, {
      params: { congress }
    });
    return response.data;
  }

  async getCommitteeAnalytics(systemCode: string, congress: number): Promise<CommitteeAnalytics> {
    const response = await api.get(`/committees/${systemCode}/analytics`, {
      params: { congress }
    });
    return response.data;
  }
}
```

#### 4.2 State Management (Zustand)

```typescript
// src/stores/committeeStore.ts
interface CommitteeState {
  committees: Committee[];
  selectedCommittee: Committee | null;
  committeeBills: Bill[];
  loading: boolean;
  error: string | null;

  // Actions
  fetchCommittees: (congress: number, chamber?: string) => Promise<void>;
  fetchCommitteeDetail: (systemCode: string, congress: number) => Promise<void>;
  fetchCommitteeBills: (systemCode: string, congress: number) => Promise<void>;
  setSelectedCommittee: (committee: Committee | null) => void;
  clearError: () => void;
}

export const useCommitteeStore = create<CommitteeState>((set, get) => ({
  committees: [],
  selectedCommittee: null,
  committeeBills: [],
  loading: false,
  error: null,

  fetchCommittees: async (congress, chamber) => {
    set({ loading: true, error: null });
    try {
      const committees = await committeeService.getCommittees(congress, chamber);
      set({ committees, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  fetchCommitteeDetail: async (systemCode, congress) => {
    set({ loading: true, error: null });
    try {
      const committee = await committeeService.getCommitteeDetail(systemCode, congress);
      set({ selectedCommittee: committee, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  // ... other actions
}));
```

### Phase 5: UI/UX Enhancements

#### 5.1 Committee Navigation

**Add to Main Navigation**:
```typescript
// Update navigation to include committees
const navigationItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/bills', label: 'Bills' },
  { path: '/members', label: 'Members' },
  { path: '/votes', label: 'Votes' },
  { path: '/committees', label: 'Committees' },  // NEW
  { path: '/analysis', label: 'Analysis' }
];
```

#### 5.2 Committee Breadcrumbs

```typescript
// src/components/navigation/CommitteeBreadcrumbs.tsx
interface CommitteeBreadcrumbsProps {
  committee?: Committee;
  subcommittee?: Committee;
  bill?: Bill;
}

// Examples:
// Home > Committees > House Agriculture
// Home > Committees > House Agriculture > Livestock Subcommittee
// Home > Bills > H.R. 1234 > Committees > House Agriculture
```

#### 5.3 Committee Quick Actions

**Action Buttons**:
```typescript
// src/components/committees/CommitteeActions.tsx
interface CommitteeActionsProps {
  committee: Committee;
}

// Actions:
// - Follow Committee (notifications)
// - Export Committee Data
// - View Official Website
// - Subscribe to Calendar
// - Share Committee Profile
```

### Implementation Timeline

#### Week 1-2: Foundation
- [ ] Create basic committee data models and types
- [ ] Set up committee service and API integration
- [ ] Create committee store with Zustand
- [ ] Build basic committee list page

#### Week 3-4: Core Features
- [ ] Implement committee detail page
- [ ] Add subcommittee support
- [ ] Create committee-bill integration
- [ ] Add committee filters to bill pages

#### Week 5-6: Analytics & Enhancement
- [ ] Build committee analytics components
- [ ] Create committee comparison features
- [ ] Add navigation and breadcrumbs
- [ ] Implement search and filtering

#### Week 7-8: Polish & Testing
- [ ] UI/UX refinements
- [ ] Mobile responsiveness
- [ ] Performance optimization
- [ ] Testing and bug fixes

### Technical Requirements

#### Dependencies to Add
```json
{
  "dependencies": {
    "recharts": "^2.8.0",      // For analytics charts
    "react-select": "^5.7.0",  // For advanced filtering
    "react-table": "^7.8.0"    // For committee bills table
  }
}
```

#### Performance Considerations

1. **Data Loading**:
   - Lazy load committee bills
   - Paginate large committee lists
   - Cache committee data in localStorage

2. **Search Optimization**:
   - Debounce search inputs
   - Client-side filtering for small datasets
   - Server-side search for large datasets

3. **Mobile Optimization**:
   - Responsive committee cards
   - Collapsible subcommittee lists
   - Touch-friendly navigation

### Testing Strategy

#### Unit Tests
```typescript
// tests/committees/CommitteeList.test.tsx
describe('CommitteeList', () => {
  it('renders committee cards correctly', () => {
    // Test committee card rendering
  });

  it('filters committees by chamber', () => {
    // Test chamber filtering
  });

  it('searches committees by name', () => {
    // Test search functionality
  });
});
```

#### Integration Tests
```typescript
// tests/committees/committeeStore.test.ts
describe('CommitteeStore', () => {
  it('fetches committees successfully', async () => {
    // Test API integration
  });

  it('handles API errors gracefully', async () => {
    // Test error handling
  });
});
```

### Future Enhancements

#### Phase 6: Advanced Features
- Committee member voting patterns
- Committee hearing transcripts
- Committee markup videos
- Real-time committee activity feeds
- Committee influence network analysis
- Historical committee performance trends

#### Phase 7: Interactive Features
- Committee comparison tool
- Committee watchlists
- Committee activity notifications
- Export committee reports
- Committee data visualization dashboard

This implementation plan provides a comprehensive approach to adding committee functionality to the Congressional Transparency Platform frontend, with clear phases, technical specifications, and timeline for development.