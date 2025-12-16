/**
 * Optimized Data Service with enhanced caching and performance features
 */

class OptimizedDataService {
  static API_BASE_URL =
    import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

  // Enhanced cache with request deduplication
  static cache = new Map();
  static pendingRequests = new Map();
  static cacheTimeout = 10 * 60 * 1000; // 10 minutes for cached data

  // Cache configuration per endpoint type
  static cacheConfig = {
    committees: { ttl: 3600000 }, // 1 hour
    'committee-details': { ttl: 1800000 }, // 30 minutes
    'committee-members': { ttl: 600000 }, // 10 minutes
    'committee-bills': { ttl: 300000 }, // 5 minutes
    bills: { ttl: 600000 }, // 10 minutes
    members: { ttl: 1800000 }, // 30 minutes
    analysis: { ttl: 3600000 }, // 1 hour
  };

  /**
   * Enhanced fetch with request deduplication and smart caching
   */
  static async fetchWithOptimization(endpoint, options = {}) {
    try {
      const fullUrl = endpoint.startsWith('http')
        ? endpoint
        : `${this.API_BASE_URL}${endpoint}`;

      const cacheKey = fullUrl;
      const endpointType = this.getEndpointType(endpoint);
      const cacheTTL = this.cacheConfig[endpointType]?.ttl || this.cacheTimeout;

      // Check if we have a pending request for this endpoint
      if (this.pendingRequests.has(cacheKey)) {
        // Return the existing promise to avoid duplicate requests
        return await this.pendingRequests.get(cacheKey);
      }

      // Check cache first
      if (this.cache.has(cacheKey)) {
        const cached = this.cache.get(cacheKey);
        if (Date.now() - cached.timestamp < cacheTTL) {
          return cached.data;
        }
      }

      // Create a new request promise
      const requestPromise = this.performFetch(fullUrl, cacheKey, cacheTTL, options);

      // Store the pending request
      this.pendingRequests.set(cacheKey, requestPromise);

      try {
        const result = await requestPromise;
        return result;
      } finally {
        // Remove from pending requests
        this.pendingRequests.delete(cacheKey);
      }
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error);

      // Try to return stale cache if available
      const cacheKey = endpoint.startsWith('http')
        ? endpoint
        : `${this.API_BASE_URL}${endpoint}`;

      if (this.cache.has(cacheKey)) {
        console.warn('Returning stale cache due to error');
        return this.cache.get(cacheKey).data;
      }

      return null;
    }
  }

  static async performFetch(fullUrl, cacheKey, cacheTTL, options) {
    const response = await fetch(fullUrl, {
      ...options,
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch ${fullUrl}: ${response.status}`);
    }

    const data = await response.json();

    // Store in cache
    this.cache.set(cacheKey, {
      data,
      timestamp: Date.now(),
    });

    // Implement cache size management
    this.manageCacheSize();

    return data;
  }

  static getEndpointType(endpoint) {
    if (endpoint.includes('/committees/') && endpoint.includes('/members')) {
      return 'committee-members';
    }
    if (endpoint.includes('/committees/') && endpoint.includes('/bills')) {
      return 'committee-bills';
    }
    if (endpoint.includes('/committees/')) {
      return 'committee-details';
    }
    if (endpoint.includes('/bills')) {
      return 'bills';
    }
    if (endpoint.includes('/members')) {
      return 'members';
    }
    if (endpoint.includes('/analysis')) {
      return 'analysis';
    }
    return 'default';
  }

  static manageCacheSize() {
    // Remove old entries if cache gets too large
    const maxCacheSize = 100;
    if (this.cache.size > maxCacheSize) {
      const entries = Array.from(this.cache.entries());
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp);

      // Remove oldest 20% of entries
      const toRemove = Math.floor(maxCacheSize * 0.2);
      for (let i = 0; i < toRemove; i++) {
        this.cache.delete(entries[i][0]);
      }
    }
  }

  /**
   * Prefetch data that will likely be needed soon
   */
  static async prefetch(endpoints) {
    const promises = endpoints.map(endpoint =>
      this.fetchWithOptimization(endpoint).catch(err => {
        console.warn(`Prefetch failed for ${endpoint}:`, err);
        return null;
      })
    );

    await Promise.allSettled(promises);
  }

  /**
   * Load multiple endpoints in parallel
   */
  static async loadParallel(endpoints) {
    const promises = endpoints.map(endpoint =>
      this.fetchWithOptimization(endpoint)
    );

    return await Promise.all(promises);
  }

  /**
   * Clear cache for specific pattern or all
   */
  static clearCache(pattern = null) {
    if (!pattern) {
      this.cache.clear();
      return;
    }

    for (const [key] of this.cache) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  // Optimized API methods with better defaults
  static async loadCommitteeDetails(committeeId) {
    return this.fetchWithOptimization(`/committees/${committeeId}`);
  }

  static async loadCommitteeMembers(committeeId) {
    return this.fetchWithOptimization(`/committees/${committeeId}/members`);
  }

  static async loadCommitteeBills(committeeId) {
    return this.fetchWithOptimization(`/committees/${committeeId}/bills`);
  }

  static async loadCommitteeTimeline(committeeId) {
    // Mock timeline data since endpoint not implemented
    return {
      activities: [
        {
          id: 1,
          type: 'hearing',
          title: 'Committee hearing on pending legislation',
          date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 2,
          type: 'bill_referral',
          title: 'New bill referred to committee',
          date: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 3,
          type: 'markup',
          title: 'Committee markup session',
          date: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
        },
      ],
    };
  }

  /**
   * Load committee data with optimized parallel loading
   */
  static async loadCommitteeDataOptimized(committeeId) {
    // Load basic details first
    const committee = await this.loadCommitteeDetails(committeeId);

    // Then load other data in parallel
    const [members, bills, timeline] = await Promise.allSettled([
      this.loadCommitteeMembers(committeeId),
      this.loadCommitteeBills(committeeId),
      this.loadCommitteeTimeline(committeeId),
    ]);

    return {
      committee,
      members: members.status === 'fulfilled' ? members.value : null,
      bills: bills.status === 'fulfilled' ? bills.value : null,
      timeline: timeline.status === 'fulfilled' ? timeline.value : null,
    };
  }

  // Compatibility methods
  static async loadMembersSummary() {
    return this.fetchWithOptimization('/members-summary');
  }

  static async loadBillsIndex(limit = 100, offset = 0) {
    // Reduce default limit for better performance
    return this.fetchWithOptimization(
      `/bills-index?limit=${limit}&offset=${offset}`
    );
  }

  static async loadComprehensiveAnalysis() {
    return this.fetchWithOptimization('/analysis/comprehensive');
  }
}

export default OptimizedDataService;