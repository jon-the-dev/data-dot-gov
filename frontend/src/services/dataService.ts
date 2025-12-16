// Enhanced data service with TypeScript and advanced features
import type {
  Member,
  Bill,
  Vote,
  LobbyingFiling,
  AnalysisReport,
  SearchFilters,
  ExportOptions,
} from '@/types';

class DataService {
  private static cache = new Map<
    string,
    { data: unknown; timestamp: number }
  >();
  private static cacheTimeout = 5 * 60 * 1000; // 5 minutes
  private static API_BASE_URL =
    import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

  static async loadJSON<T>(path: string, useCache = true): Promise<T | null> {
    try {
      const cacheKey = path;

      if (useCache && this.cache.has(cacheKey)) {
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
          return cached.data as T;
        }
      }

      const response = await fetch(path);
      if (!response.ok) {
        throw new Error(`Failed to load ${path}: ${response.status}`);
      }

      const data = await response.json();

      if (useCache) {
        this.cache.set(cacheKey, {
          data,
          timestamp: Date.now(),
        });
      }

      return data;
    } catch (error) {
      console.error(`Error loading ${path}:`, error);
      return null;
    }
  }

  // Core data loading methods
  static async loadMembersSummary() {
    return this.loadJSON(`${this.API_BASE_URL}/members-summary`);
  }

  static async loadBillsIndex() {
    return this.loadJSON(`${this.API_BASE_URL}/bills-index`);
  }

  static async loadBillDetails(billId: string): Promise<Bill | null> {
    return this.loadJSON(`${this.API_BASE_URL}/bill/${billId}`);
  }

  static async loadMemberDetails(memberId: string): Promise<Member | null> {
    return this.loadJSON(`${this.API_BASE_URL}/member/${memberId}`);
  }

  static async loadVoteDetails(voteId: string): Promise<Vote | null> {
    return this.loadJSON(`${this.API_BASE_URL}/vote/${voteId}`);
  }

  static async loadComprehensiveAnalysis(): Promise<AnalysisReport | null> {
    return this.loadJSON(`${this.API_BASE_URL}/analysis/comprehensive`);
  }

  // Enhanced data loading methods
  static async loadBillCategories() {
    return this.loadJSON(`${this.API_BASE_URL}/analysis/bill-categories`);
  }

  static async loadBillSponsors() {
    return this.loadJSON(`${this.API_BASE_URL}/bill-sponsors`);
  }

  static async loadVotingAnalysis() {
    return this.loadJSON(`${this.API_BASE_URL}/analysis/party-voting`);
  }

  static async loadLobbyingData(): Promise<LobbyingFiling[] | null> {
    return this.loadJSON(`${this.API_BASE_URL}/lobbying`);
  }

  // Trend Analysis Methods
  static async fetchLegislativeActivity(): Promise<any | null> {
    return this.loadJSON(`${this.API_BASE_URL}/trends/legislative-activity`);
  }

  static async fetchBipartisanCooperation(): Promise<any | null> {
    return this.loadJSON(`${this.API_BASE_URL}/trends/bipartisan-cooperation`);
  }

  static async fetchVotingConsistency(): Promise<any | null> {
    return this.loadJSON(`${this.API_BASE_URL}/trends/voting-consistency`);
  }

  // Additional methods for paginated endpoints
  static async loadMembers(congress: number) {
    return this.loadJSON(`${this.API_BASE_URL}/members/${congress}`);
  }

  static async loadBills(congress: number, limit = 100, offset = 0) {
    return this.loadJSON(
      `${this.API_BASE_URL}/bills/${congress}?limit=${limit}&offset=${offset}`
    );
  }

  static async loadVotes(congress: number, limit = 50, offset = 0) {
    return this.loadJSON(
      `${this.API_BASE_URL}/votes/${congress}?limit=${limit}&offset=${offset}`
    );
  }

  static async loadCategories() {
    return this.loadJSON(`${this.API_BASE_URL}/categories`);
  }

  static async loadCategoryBills(category: string) {
    return this.loadJSON(`${this.API_BASE_URL}/categories/${category}`);
  }

  static async loadCommittees(chamber: string | null = null) {
    const url = chamber
      ? `${this.API_BASE_URL}/committees?chamber=${chamber}`
      : `${this.API_BASE_URL}/committees`;
    return this.loadJSON(url);
  }

  static async loadCommitteeDetails(committeeId: string) {
    return this.loadJSON(`${this.API_BASE_URL}/committees/${committeeId}`);
  }

  static async loadSubcommitteeDetails(subcommitteeId: string) {
    return this.loadJSON(
      `${this.API_BASE_URL}/subcommittees/${subcommitteeId}`
    );
  }

  static async loadCommitteeMembers(committeeId: string) {
    return this.loadJSON(
      `${this.API_BASE_URL}/committees/${committeeId}/members`
    );
  }

  static async loadCommitteeBills(committeeId: string) {
    return this.loadJSON(
      `${this.API_BASE_URL}/committees/${committeeId}/bills`
    );
  }

  static async loadCommitteeVotes(committeeId: string) {
    return this.loadJSON(
      `${this.API_BASE_URL}/committees/${committeeId}/votes`
    );
  }

  static async loadCommitteeHearings(committeeId: string) {
    return this.loadJSON(
      `${this.API_BASE_URL}/committees/${committeeId}/hearings`
    );
  }

  static async loadCommitteeMeetings(committeeId: string) {
    return this.loadJSON(
      `${this.API_BASE_URL}/committees/${committeeId}/meetings`
    );
  }

  static async loadCommitteeDocuments(committeeId: string) {
    return this.loadJSON(
      `${this.API_BASE_URL}/committees/${committeeId}/documents`
    );
  }

  // Advanced search functionality
  static async searchMembers(
    query: string,
    filters: SearchFilters = {}
  ): Promise<Member[]> {
    try {
      const membersSummary = await this.loadMembersSummary();
      if (
        !membersSummary ||
        !(membersSummary as { members?: Member[] }).members
      )
        return [];

      let results = (membersSummary as { members: Member[] }).members;

      // Text search
      if (query.trim()) {
        const searchTerm = query.toLowerCase();
        results = results.filter(
          (member: Member) =>
            member.name.toLowerCase().includes(searchTerm) ||
            member.state.toLowerCase().includes(searchTerm) ||
            member.bioguideId.toLowerCase().includes(searchTerm)
        );
      }

      // Apply filters
      if (filters.party?.length) {
        results = results.filter((member: Member) =>
          filters.party?.includes(this.normalizeParty(member.party))
        );
      }

      if (filters.state?.length) {
        results = results.filter((member: Member) =>
          filters.state?.includes(member.state)
        );
      }

      if (filters.chamber?.length) {
        results = results.filter((member: Member) =>
          filters.chamber?.includes(member.chamber)
        );
      }

      return results;
    } catch (error) {
      console.error('Error searching members:', error);
      return [];
    }
  }

  static async searchBills(
    query: string,
    filters: SearchFilters = {}
  ): Promise<Bill[]> {
    try {
      const billsIndex = await this.loadBillsIndex();
      if (
        !billsIndex ||
        !(billsIndex as { bills?: Bill[] | Record<string, Bill> }).bills
      )
        return [];

      const bills = (billsIndex as { bills: Bill[] | Record<string, Bill> })
        .bills;
      let results = Array.isArray(bills) ? bills : Object.values(bills);

      // Text search
      if (query.trim()) {
        const searchTerm = query.toLowerCase();
        results = results.filter(
          (bill: Bill) =>
            bill.title?.toLowerCase().includes(searchTerm) ||
            bill.bill_id?.toLowerCase().includes(searchTerm) ||
            bill.subjects?.some(subject =>
              subject.toLowerCase().includes(searchTerm)
            )
        );
      }

      // Date range filter
      if (filters.dateRange) {
        const startDate = new Date(filters.dateRange.start);
        const endDate = new Date(filters.dateRange.end);
        results = results.filter((bill: Bill) => {
          const billDate = new Date(bill.introducedDate || bill.updateDate);
          return billDate >= startDate && billDate <= endDate;
        });
      }

      return results;
    } catch (error) {
      console.error('Error searching bills:', error);
      return [];
    }
  }

  // Data export functionality
  static async exportData(options: ExportOptions): Promise<string> {
    try {
      let data: unknown[] = [];

      switch (options.data) {
        case 'members':
          data = await this.searchMembers('', options.filters || {});
          break;
        case 'bills':
          data = await this.searchBills('', options.filters || {});
          break;
        case 'votes':
          // Implementation would depend on vote data structure
          break;
        case 'lobbying':
          data = (await this.loadLobbyingData()) || [];
          break;
        case 'all':
          const [members, bills, lobbying] = await Promise.all([
            this.searchMembers('', options.filters || {}),
            this.searchBills('', options.filters || {}),
            this.loadLobbyingData(),
          ]);
          data = [{ members, bills, lobbying }];
          break;
      }

      if (options.format === 'csv') {
        return this.convertToCSV(data as Record<string, unknown>[]);
      } else {
        return JSON.stringify(data, null, 2);
      }
    } catch (error) {
      console.error('Error exporting data:', error);
      throw error;
    }
  }

  private static convertToCSV(data: Record<string, unknown>[]): string {
    if (!data.length) return '';

    const firstItem = data[0];
    if (!firstItem) return '';
    const headers = Object.keys(firstItem);
    const csvHeaders = headers.join(',');

    const csvRows = data.map(row =>
      headers
        .map(header => {
          const value = row[header];
          if (value === null || value === undefined) return '';
          if (
            typeof value === 'string' &&
            (value.includes(',') || value.includes('"'))
          ) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return String(value);
        })
        .join(',')
    );

    return [csvHeaders, ...csvRows].join('\n');
  }

  // Utility methods
  static getPartyColor(party: string): string {
    const normalizedParty = this.normalizeParty(party);
    const colors = {
      Republican: '#E91D0E',
      Democratic: '#0075C4',
      Independent: '#9B59B6',
    };
    return colors[normalizedParty as keyof typeof colors] || '#666666';
  }

  static getPartyLabel(party: string): string {
    const normalizedParty = this.normalizeParty(party);
    return normalizedParty;
  }

  static normalizeParty(party: string): string {
    const normalized = {
      R: 'Republican',
      D: 'Democratic',
      I: 'Independent',
      Republican: 'Republican',
      Democratic: 'Democratic',
      Independent: 'Independent',
    };
    return normalized[party as keyof typeof normalized] || party;
  }

  static formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }

  static formatDate(dateString: string): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(date);
  }

  static formatNumber(num: number, decimals = 1): string {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
  }

  static calculatePercentage(value: number, total: number): number {
    return total > 0 ? (value / total) * 100 : 0;
  }

  // Cache management
  static clearCache(): void {
    this.cache.clear();
  }

  static getCacheSize(): number {
    return this.cache.size;
  }

  // Error boundary helper
  static handleError(error: Error, context: string): void {
    console.error(`DataService Error [${context}]:`, error);
    // Could integrate with error reporting service here
  }
}

export default DataService;
