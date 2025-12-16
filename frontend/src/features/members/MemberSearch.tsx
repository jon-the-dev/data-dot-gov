import { Search, Filter, X, Download, Users } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';

import DataService from '@/services/dataService';
import type { Member, SearchFilters } from '@/types';

interface MemberSearchProps {
  onSearch?: (results: Member[]) => void;
  embedded?: boolean;
}

const US_STATES = [
  'AL',
  'AK',
  'AZ',
  'AR',
  'CA',
  'CO',
  'CT',
  'DE',
  'FL',
  'GA',
  'HI',
  'ID',
  'IL',
  'IN',
  'IA',
  'KS',
  'KY',
  'LA',
  'ME',
  'MD',
  'MA',
  'MI',
  'MN',
  'MS',
  'MO',
  'MT',
  'NE',
  'NV',
  'NH',
  'NJ',
  'NM',
  'NY',
  'NC',
  'ND',
  'OH',
  'OK',
  'OR',
  'PA',
  'RI',
  'SC',
  'SD',
  'TN',
  'TX',
  'UT',
  'VT',
  'VA',
  'WA',
  'WV',
  'WI',
  'WY',
];

export default function MemberSearch({
  onSearch,
  embedded = false,
}: MemberSearchProps) {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [results, setResults] = useState<Member[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [totalMembers, setTotalMembers] = useState(0);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const membersSummary = await DataService.loadMembersSummary();
      const allMembers = (membersSummary as any)?.members || [];
      setResults(allMembers);
      setTotalMembers(allMembers.length);
      onSearch?.(allMembers);
    } catch (error) {
      console.error('Error loading initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const performSearch = useCallback(async () => {
    try {
      setLoading(true);
      const searchResults = await DataService.searchMembers(query, filters);
      setResults(searchResults);
      onSearch?.(searchResults);
    } catch (error) {
      console.error('Error performing search:', error);
    } finally {
      setLoading(false);
    }
  }, [query, filters, onSearch]);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      performSearch();
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [performSearch]);

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const clearFilters = () => {
    setFilters({});
    setQuery('');
  };

  const exportResults = async () => {
    try {
      const csvData = await DataService.exportData({
        format: 'csv',
        data: 'members',
        filters,
      });

      const blob = new Blob([csvData], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `members-search-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting results:', error);
    }
  };

  const activeFilterCount = Object.values(filters).filter(value =>
    Array.isArray(value) ? value.length > 0 : Boolean(value)
  ).length;

  return (
    <div className='space-y-4'>
      {/* Search Header */}
      <div className='flex flex-col sm:flex-row gap-4'>
        <div className='relative flex-1'>
          <Search
            className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
            size={20}
          />
          <input
            type='text'
            placeholder='Search by name, state, or bioguide ID...'
            value={query}
            onChange={e => setQuery(e.target.value)}
            className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
          />
        </div>

        <div className='flex gap-2'>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors
              ${
                showFilters
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }
            `}
          >
            <Filter size={16} />
            Filters
            {activeFilterCount > 0 && (
              <span className='bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center'>
                {activeFilterCount}
              </span>
            )}
          </button>

          <button
            onClick={exportResults}
            disabled={results.length === 0}
            className='flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors'
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className='bg-white border border-gray-200 rounded-lg p-4 space-y-4'>
          <div className='flex items-center justify-between'>
            <h3 className='text-sm font-medium text-gray-900'>
              Search Filters
            </h3>
            {activeFilterCount > 0 && (
              <button
                onClick={clearFilters}
                className='flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900'
              >
                <X size={14} />
                Clear all
              </button>
            )}
          </div>

          <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
            {/* Party Filter */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Party
              </label>
              <div className='space-y-2'>
                {['Democratic', 'Republican', 'Independent'].map(party => (
                  <label key={party} className='flex items-center'>
                    <input
                      type='checkbox'
                      checked={filters.party?.includes(party) || false}
                      onChange={e => {
                        const currentParties = filters.party || [];
                        if (e.target.checked) {
                          updateFilter('party', [...currentParties, party]);
                        } else {
                          updateFilter(
                            'party',
                            currentParties.filter(p => p !== party)
                          );
                        }
                      }}
                      className='rounded border-gray-300 text-blue-600 focus:ring-blue-500'
                    />
                    <span className='ml-2 text-sm text-gray-700'>{party}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Chamber Filter */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                Chamber
              </label>
              <div className='space-y-2'>
                {['house', 'senate'].map(chamber => (
                  <label key={chamber} className='flex items-center'>
                    <input
                      type='checkbox'
                      checked={filters.chamber?.includes(chamber) || false}
                      onChange={e => {
                        const currentChambers = filters.chamber || [];
                        if (e.target.checked) {
                          updateFilter('chamber', [
                            ...currentChambers,
                            chamber,
                          ]);
                        } else {
                          updateFilter(
                            'chamber',
                            currentChambers.filter(c => c !== chamber)
                          );
                        }
                      }}
                      className='rounded border-gray-300 text-blue-600 focus:ring-blue-500'
                    />
                    <span className='ml-2 text-sm text-gray-700 capitalize'>
                      {chamber}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* State Filter */}
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                State
              </label>
              <select
                multiple
                value={filters.state || []}
                onChange={e => {
                  const selectedStates = Array.from(
                    e.target.selectedOptions,
                    option => option.value
                  );
                  updateFilter('state', selectedStates);
                }}
                className='w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                size={4}
              >
                {US_STATES.map(state => (
                  <option key={state} value={state}>
                    {state}
                  </option>
                ))}
              </select>
              <p className='text-xs text-gray-500 mt-1'>
                Hold Ctrl/Cmd to select multiple
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results Summary */}
      <div className='flex items-center justify-between bg-gray-50 px-4 py-3 rounded-lg'>
        <div className='flex items-center gap-2 text-sm text-gray-600'>
          <Users size={16} />
          <span>
            Showing {results.length.toLocaleString()} of{' '}
            {totalMembers.toLocaleString()} members
          </span>
        </div>
        {loading && (
          <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600' />
        )}
      </div>

      {/* Results List */}
      {!embedded && (
        <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
          {results.length > 0 ? (
            <div className='divide-y divide-gray-200'>
              {results.map(member => (
                <Link
                  key={member.bioguideId}
                  to={`/members/${member.bioguideId}`}
                  className='block p-4 hover:bg-gray-50 transition-colors'
                >
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-3'>
                      <div
                        className='w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold'
                        style={{
                          backgroundColor: DataService.getPartyColor(
                            member.party
                          ),
                        }}
                      >
                        {member.name
                          .split(' ')
                          .map(n => n[0])
                          .join('')
                          .slice(0, 2)}
                      </div>
                      <div>
                        <h3 className='font-medium text-gray-900'>
                          {member.name}
                        </h3>
                        <p className='text-sm text-gray-600'>
                          {member.state}
                          {member.district
                            ? ` District ${member.district}`
                            : ''}{' '}
                          • {DataService.getPartyLabel(member.party)} •{' '}
                          {member.chamber}
                        </p>
                      </div>
                    </div>
                    <div className='text-right'>
                      <p className='text-sm font-medium text-gray-900'>
                        {member.bioguideId}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : !loading ? (
            <div className='p-8 text-center text-gray-500'>
              <Users size={48} className='mx-auto mb-4 text-gray-300' />
              <p>No members found matching your search criteria.</p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
