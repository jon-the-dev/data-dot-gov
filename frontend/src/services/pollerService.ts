// Poller API service for data fetcher status and control

import type {
  PollerStatus,
  DataFreshness,
  PollerLog,
  TriggerResponse,
  PollerLogFilters,
  DataType,
} from '@/types/poller';

class PollerService {
  private static API_BASE_URL =
    import.meta.env.VITE_API_URL || '/api/v1';

  /**
   * Fetch current poller status
   */
  static async fetchPollerStatus(): Promise<PollerStatus> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/poller/status`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching poller status:', error);
      // Return fallback status
      return {
        status: 'error',
        last_run: null,
        next_scheduled_run: null,
        current_task: null,
        uptime_seconds: 0,
      };
    }
  }

  /**
   * Fetch data freshness for all data types
   */
  static async fetchDataFreshness(): Promise<DataFreshness[]> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/poller/freshness`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching data freshness:', error);
      // Return empty array as fallback
      return [];
    }
  }

  /**
   * Fetch poller logs with optional filtering
   */
  static async fetchPollerLogs(
    filters: PollerLogFilters = {}
  ): Promise<PollerLog[]> {
    try {
      const params = new URLSearchParams();

      if (filters.level) params.append('level', filters.level);
      if (filters.data_type) params.append('data_type', filters.data_type);
      if (filters.limit) params.append('limit', filters.limit.toString());
      if (filters.offset) params.append('offset', filters.offset.toString());

      const url = `${this.API_BASE_URL}/poller/logs${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching poller logs:', error);
      return [];
    }
  }

  /**
   * Trigger manual data fetch for a specific data type
   */
  static async triggerDataFetch(dataType: DataType): Promise<TriggerResponse> {
    try {
      const response = await fetch(
        `${this.API_BASE_URL}/poller/trigger/${dataType}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error(`Error triggering ${dataType} fetch:`, error);
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Format age in hours to human-readable string
   */
  static formatAge(ageHours: number | null): string {
    if (ageHours === null) return 'Never';
    if (ageHours < 1) return `${Math.floor(ageHours * 60)} minutes ago`;
    if (ageHours < 24) return `${Math.floor(ageHours)} hours ago`;
    const days = Math.floor(ageHours / 24);
    return `${days} day${days !== 1 ? 's' : ''} ago`;
  }

  /**
   * Format uptime in seconds to human-readable string
   */
  static formatUptime(seconds: number): string {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
  }

  /**
   * Get display name for data type
   */
  static getDataTypeLabel(dataType: DataType): string {
    const labels: Record<DataType, string> = {
      bills: 'Bills',
      members: 'Members',
      committees: 'Committees',
      lobbying: 'Lobbying Data',
      votes: 'Votes',
    };
    return labels[dataType];
  }

  /**
   * Get status color class
   */
  static getStatusColor(status: 'running' | 'idle' | 'error'): string {
    const colors = {
      running: 'text-green-600',
      idle: 'text-gray-600',
      error: 'text-red-600',
    };
    return colors[status] || 'text-gray-600';
  }

  /**
   * Get log level color class
   */
  static getLogLevelColor(level: string): string {
    const colors: Record<string, string> = {
      info: 'text-blue-600',
      success: 'text-green-600',
      warning: 'text-yellow-600',
      error: 'text-red-600',
    };
    return colors[level] || 'text-gray-600';
  }
}

export default PollerService;
