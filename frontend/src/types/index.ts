// Type definitions for Congressional transparency platform

export interface Member {
  bioguideId: string;
  name: string;
  party: 'Democratic' | 'Republican' | 'Independent' | 'D' | 'R' | 'I';
  state: string;
  chamber: 'house' | 'senate';
  congress_numbers?: number[];
  district?: string;
  terms?: Term[];
  votingRecord?: VotePosition[];
}

export interface Term {
  congress: number;
  chamber: string;
  startDate: string;
  endDate: string;
  party: string;
  state: string;
  district?: string;
}

export interface Bill {
  bill_id: string;
  type: string;
  congress: number;
  title: string;
  introducedDate: string;
  updateDate: string;
  actions?: BillAction[];
  sponsors?: Sponsor[];
  cosponsors?: Sponsor[];
  subjects?: string[];
  committees?: string[];
  policyArea?: string;
  status?: string;
  summary?: string;
}

export interface BillAction {
  date: string;
  description: string;
  type: string;
}

export interface Sponsor {
  bioguideId: string;
  name: string;
  party: string;
  state: string;
  district?: string;
  sponsorshipDate?: string;
}

export interface Vote {
  vote_id: string;
  congress: number;
  roll_call: number;
  chamber: 'house' | 'senate';
  session: number;
  vote_date: string;
  question: string;
  description: string;
  result: string;
  total_votes: {
    yea: number;
    nay: number;
    present: number;
    not_voting: number;
  };
  party_breakdown: {
    [party: string]: {
      yea: number;
      nay: number;
      present: number;
      not_voting: number;
    };
  };
  member_votes?: VotePosition[];
}

export interface VotePosition {
  bioguideId: string;
  name: string;
  party: string;
  state: string;
  position: 'Yea' | 'Nay' | 'Present' | 'Not Voting';
  vote_id: string;
}

export interface LobbyingFiling {
  id: string;
  filing_type: 'LD-1' | 'LD-2';
  filing_date: string;
  client_name: string;
  registrant_name: string;
  issues: string[];
  amount?: number;
  termination_date?: string;
  year: number;
  quarter?: number;
}

export interface PartyStats {
  total: number;
  republicans: number;
  democrats: number;
  independents: number;
}

export interface BillCategory {
  name: string;
  bills: Bill[];
  party_breakdown: {
    [party: string]: number;
  };
  keywords: string[];
}

export interface PartyUnityScore {
  bioguideId: string;
  name: string;
  party: string;
  unity_score: number;
  total_votes: number;
  party_line_votes: number;
  cross_party_votes: number;
}

export interface SwingVoter {
  member: Member;
  crossPartyVotes: number;
  totalVotes: number;
  swingRate: number;
  notableVotes: Vote[];
}

export interface SearchFilters {
  party?: string[];
  state?: string[];
  chamber?: string[];
  dateRange?: {
    start: string;
    end: string;
  };
  category?: string[];
  keywords?: string;
}

export interface ExportOptions {
  format: 'csv' | 'json';
  data: 'members' | 'bills' | 'votes' | 'lobbying' | 'all';
  filters?: SearchFilters;
}

export interface AnalysisReport {
  title: string;
  description: string;
  data: Record<string, unknown>;
  generated_at: string;
  congress: number;
  metrics: {
    [key: string]: number | string;
  };
  analyses?: {
    [key: string]: Record<string, unknown>;
  };
}

export interface DashboardData {
  membersSummary: {
    party_breakdown?: { [party: string]: number };
    members?: Member[];
    by_state?: { [state: string]: { [party: string]: number } };
    [key: string]: unknown;
  } | null;
  billsIndex: {
    bills?: Bill[] | { [key: string]: Bill };
    total?: number;
    [key: string]: unknown;
  } | null;
  comprehensiveAnalysis: AnalysisReport | null;
  loading: boolean;
  error: string | null;
}

export interface LoadingState {
  loading: boolean;
  error?: string;
  progress?: number;
}

// UI Component Props
export interface SearchProps {
  onSearch: (query: string, filters: SearchFilters) => void;
  loading?: boolean;
  placeholder?: string;
}

export interface ChartProps {
  data: Record<string, unknown>[];
  title?: string;
  height?: number;
  showLegend?: boolean;
}

export interface TableProps {
  data: Record<string, unknown>[];
  columns: TableColumn[];
  loading?: boolean;
  onRowClick?: (row: Record<string, unknown>) => void;
  sortable?: boolean;
}

export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
}
