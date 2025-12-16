// Data service for loading and processing congressional data
class DataService {
  static API_BASE_URL =
    import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

  // Cache for API responses
  static cache = new Map();
  static cacheTimeout = 5 * 60 * 1000; // 5 minutes

  /**
   * Fetch data with caching support
   * @param {string} endpoint - API endpoint path
   * @param {Object} options - Fetch options and cache settings
   * @param {boolean} options.useCache - Whether to use caching (default: true)
   * @returns {Promise<any|null>} Cached or fresh data
   */
  static async fetchWithCache(endpoint, options = {}) {
    try {
      const { useCache = true, ...fetchOptions } = options;
      const fullUrl = endpoint.startsWith('http')
        ? endpoint
        : `${this.API_BASE_URL}${endpoint}`;
      const cacheKey = fullUrl;

      // Check cache first if enabled
      if (useCache && this.cache.has(cacheKey)) {
        const cached = this.cache.get(cacheKey);
        if (Date.now() - cached.timestamp < this.cacheTimeout) {
          return cached.data;
        }
      }

      const response = await fetch(fullUrl, fetchOptions);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${fullUrl}: ${response.status}`);
      }

      const data = await response.json();

      // Store in cache if enabled
      if (useCache) {
        this.cache.set(cacheKey, {
          data,
          timestamp: Date.now(),
        });
      }

      return data;
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error);
      return null;
    }
  }

  static async loadJSON(path) {
    try {
      const response = await fetch(path);
      if (!response.ok) {
        throw new Error(`Failed to load ${path}: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error loading ${path}:`, error);
      return null;
    }
  }

  static async loadMembersSummary() {
    return this.loadJSON(`${this.API_BASE_URL}/members-summary`);
  }

  static async loadBillsIndex(limit = 2000, offset = 0) {
    return this.loadJSON(
      `${this.API_BASE_URL}/bills-index?limit=${limit}&offset=${offset}`
    );
  }

  static async loadBillDetails(billId) {
    return this.loadJSON(`${this.API_BASE_URL}/bill/${billId}`);
  }

  static async loadMemberDetails(memberId) {
    return this.loadJSON(`${this.API_BASE_URL}/member/${memberId}`);
  }

  static async loadVoteDetails(voteId) {
    return this.loadJSON(`${this.API_BASE_URL}/vote/${voteId}`);
  }

  static async loadComprehensiveAnalysis() {
    return this.loadJSON(`${this.API_BASE_URL}/analysis/comprehensive`);
  }

  static async loadMembers(congress) {
    return this.loadJSON(`${this.API_BASE_URL}/members/${congress}`);
  }

  static async loadBills(congress, limit = 100, offset = 0) {
    return this.loadJSON(
      `${this.API_BASE_URL}/bills/${congress}?limit=${limit}&offset=${offset}`
    );
  }

  static async loadVotes(congress, limit = 50, offset = 0) {
    return this.loadJSON(
      `${this.API_BASE_URL}/votes/${congress}?limit=${limit}&offset=${offset}`
    );
  }

  static async loadPartyVotingAnalysis() {
    return this.loadJSON(`${this.API_BASE_URL}/analysis/party-voting`);
  }

  static async loadBillCategoriesAnalysis() {
    return this.loadJSON(`${this.API_BASE_URL}/analysis/bill-categories`);
  }

  static async loadCategories() {
    return this.loadJSON(`${this.API_BASE_URL}/categories`);
  }

  static async loadCategoryBills(category) {
    return this.loadJSON(`${this.API_BASE_URL}/categories/${category}`);
  }

  static async loadCommittees(chamber = null) {
    const url = chamber
      ? `${this.API_BASE_URL}/committees?chamber=${chamber}`
      : `${this.API_BASE_URL}/committees`;
    return this.loadJSON(url);
  }

  static async loadCommitteeDetails(committeeId) {
    return this.loadJSON(`${this.API_BASE_URL}/committees/${committeeId}`);
  }

  static async loadSubcommitteeDetails(subcommitteeId) {
    return this.loadJSON(
      `${this.API_BASE_URL}/subcommittees/${subcommitteeId}`
    );
  }

  static async loadCommitteeMembers(committeeId) {
    return this.loadJSON(
      `${this.API_BASE_URL}/committees/${committeeId}/members`
    );
  }

  static async loadCommitteeBills(committeeId) {
    return this.loadJSON(
      `${this.API_BASE_URL}/committees/${committeeId}/bills`
    );
  }

  static async loadCommitteeTimeline(committeeId, limit = 20) {
    // Timeline endpoint not yet implemented - return mock data for now
    console.warn(
      'Committee timeline endpoint not yet implemented, using mock data'
    );

    // Return mock timeline data based on committee ID
    const mockActivities = [
      {
        id: `${committeeId}_1`,
        date: '2024-09-20T10:00:00Z',
        type: 'hearing',
        description: 'Committee hearing on pending legislation',
        details: {
          summary: 'Discussion of key policy issues and pending bills',
          participants: [
            'Committee Chair',
            'Ranking Member',
            'Expert Witnesses',
          ],
          outcome: 'Hearing completed, further review scheduled',
        },
      },
      {
        id: `${committeeId}_2`,
        date: '2024-09-15T14:30:00Z',
        type: 'bill_referral',
        description: 'New bill referred to committee',
        details: {
          summary: 'Bill assigned for committee review and markup',
          bills: [{ number: 'H.R. 1234', title: 'Sample Legislation Act' }],
        },
      },
      {
        id: `${committeeId}_3`,
        date: '2024-09-10T09:00:00Z',
        type: 'markup',
        description: 'Committee markup session',
        details: {
          summary: 'Review and amendment of pending legislation',
          outcome: 'Bill marked up and ready for floor consideration',
        },
      },
    ];

    return {
      activities: mockActivities,
      total: mockActivities.length,
      committee_id: committeeId,
      note: 'Mock timeline data - real implementation pending',
    };
  }

  static async loadCommitteeAnalytics(committeeId) {
    return this.loadJSON(
      `${this.API_BASE_URL}/committees/${committeeId}/analytics`
    );
  }

  static async loadLobbyingData(filingType = null, limit = 100, offset = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (filingType) {
      params.append('filing_type', filingType);
    }
    return this.loadJSON(`${this.API_BASE_URL}/lobbying?${params.toString()}`);
  }

  // Trend Analysis Endpoints

  /**
   * Fetch legislative activity trends data
   * @returns {Promise<any|null>} Legislative activity trends or null on error
   */
  static async fetchLegislativeActivity() {
    const result = await this.fetchWithCache('/trends/legislative-activity');

    // Return mock data if API is not available (for development/testing)
    if (!result) {
      return {
        sponsorship_patterns: {
          trends: {
            monthly_activity: [
              { month: 'Jan 2024', republican_bills: 45, democratic_bills: 52 },
              { month: 'Feb 2024', republican_bills: 38, democratic_bills: 48 },
              { month: 'Mar 2024', republican_bills: 42, democratic_bills: 55 },
              { month: 'Apr 2024', republican_bills: 41, democratic_bills: 49 },
              { month: 'May 2024', republican_bills: 37, democratic_bills: 51 },
              { month: 'Jun 2024', republican_bills: 44, democratic_bills: 53 },
            ],
            most_active_sponsors: [
              { name: 'Sen. John Smith', party: 'R', bills_sponsored: 12 },
              { name: 'Sen. Jane Doe', party: 'D', bills_sponsored: 11 },
              { name: 'Sen. Bob Johnson', party: 'R', bills_sponsored: 9 },
              { name: 'Sen. Mary Wilson', party: 'D', bills_sponsored: 8 },
              { name: 'Sen. Tom Brown', party: 'R', bills_sponsored: 7 },
              { name: 'Sen. Lisa Davis', party: 'D', bills_sponsored: 6 },
            ],
          },
          by_party: {
            Republican: {
              top_policy_areas: [
                'Defense',
                'Economy',
                'Healthcare',
                'Immigration',
                'Energy',
              ],
            },
            Democratic: {
              top_policy_areas: [
                'Healthcare',
                'Environment',
                'Education',
                'Social Programs',
                'Civil Rights',
              ],
            },
          },
        },
      };
    }

    return result;
  }

  /**
   * Fetch bipartisan cooperation trends data
   * @returns {Promise<any|null>} Bipartisan cooperation trends or null on error
   */
  static async fetchBipartisanCooperation() {
    const result = await this.fetchWithCache('/trends/bipartisan-cooperation');

    // Return mock data if API is not available (for development/testing)
    if (!result) {
      return {
        cooperation_metrics: {
          monthly_trends: [
            { month: 'Jan 2024', bipartisan_rate: 0.23 },
            { month: 'Feb 2024', bipartisan_rate: 0.18 },
            { month: 'Mar 2024', bipartisan_rate: 0.31 },
            { month: 'Apr 2024', bipartisan_rate: 0.26 },
            { month: 'May 2024', bipartisan_rate: 0.22 },
            { month: 'Jun 2024', bipartisan_rate: 0.28 },
          ],
          top_bipartisan_areas: [
            { policy_area: 'Infrastructure', bipartisan_rate: 0.65 },
            { policy_area: 'Veterans Affairs', bipartisan_rate: 0.58 },
            { policy_area: 'Transportation', bipartisan_rate: 0.52 },
            { policy_area: 'Agriculture', bipartisan_rate: 0.47 },
            { policy_area: 'Technology', bipartisan_rate: 0.41 },
          ],
          bridge_builders: [
            { name: 'Sen. Susan Collins', party: 'R', bipartisan_score: 0.72 },
            { name: 'Sen. Joe Manchin', party: 'D', bipartisan_score: 0.68 },
            { name: 'Sen. Lisa Murkowski', party: 'R', bipartisan_score: 0.64 },
            { name: 'Sen. Kyrsten Sinema', party: 'I', bipartisan_score: 0.61 },
            { name: 'Sen. Mitt Romney', party: 'R', bipartisan_score: 0.58 },
            { name: 'Sen. Mark Warner', party: 'D', bipartisan_score: 0.55 },
          ],
        },
      };
    }

    return result;
  }

  /**
   * Fetch voting consistency trends data
   * @returns {Promise<any|null>} Voting consistency trends or null on error
   */
  static async fetchVotingConsistency() {
    const result = await this.fetchWithCache('/trends/voting-consistency');

    // Return mock data if API is not available (for development/testing)
    if (!result) {
      return {
        consistency_metrics: {
          party_unity_scores: {
            Republican: 0.87,
            Democratic: 0.89,
            Independent: 0.45,
          },
          temporal_trends: [
            { month: 'Jan 2024', party_unity: 0.86 },
            { month: 'Feb 2024', party_unity: 0.88 },
            { month: 'Mar 2024', party_unity: 0.84 },
            { month: 'Apr 2024', party_unity: 0.87 },
            { month: 'May 2024', party_unity: 0.89 },
            { month: 'Jun 2024', party_unity: 0.85 },
          ],
          maverick_members: [
            { name: 'Sen. Joe Manchin', party: 'D', unity_score: 0.62 },
            { name: 'Sen. Susan Collins', party: 'R', unity_score: 0.68 },
            { name: 'Sen. Kyrsten Sinema', party: 'I', unity_score: 0.45 },
            { name: 'Sen. Lisa Murkowski', party: 'R', unity_score: 0.71 },
            { name: 'Sen. Mitt Romney', party: 'R', unity_score: 0.74 },
            { name: 'Sen. Jon Tester', party: 'D', unity_score: 0.76 },
          ],
          key_divisive_votes: [
            {
              description: 'Infrastructure Investment and Jobs Act',
              date: '2024-03-15',
              party_split: {
                R_for: 19,
                R_against: 30,
                D_for: 48,
                D_against: 2,
              },
            },
            {
              description: 'Climate Action Framework',
              date: '2024-02-28',
              party_split: { R_for: 3, R_against: 46, D_for: 47, D_against: 3 },
            },
            {
              description: 'Border Security Enhancement Act',
              date: '2024-01-18',
              party_split: {
                R_for: 45,
                R_against: 4,
                D_for: 12,
                D_against: 38,
              },
            },
          ],
        },
      };
    }

    return result;
  }

  // Helper methods for data processing
  static getPartyColor(party) {
    const colors = {
      Republican: '#E91D0E',
      R: '#E91D0E',
      Democratic: '#0075C4',
      D: '#0075C4',
      Independent: '#9B59B6',
      I: '#9B59B6',
    };
    return colors[party] || '#666666';
  }

  static getPartyLabel(party) {
    const labels = {
      R: 'Republican',
      D: 'Democratic',
      I: 'Independent',
      Republican: 'Republican',
      Democratic: 'Democratic',
      Independent: 'Independent',
    };
    return labels[party] || party;
  }

  static formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  }

  static formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(date);
  }

  /**
   * Clear all cached data
   */
  static clearCache() {
    this.cache.clear();
  }

  /**
   * Get current cache size
   * @returns {number} Number of cached entries
   */
  static getCacheSize() {
    return this.cache.size;
  }
}

export default DataService;
