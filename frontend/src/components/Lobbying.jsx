import {
  Search,
  Filter,
  DollarSign,
  Building,
  Calendar,
  ExternalLink,
  FileText,
  Users,
} from 'lucide-react';
import { useState, useEffect } from 'react';

import DataService from '../services/dataService';

function Lobbying() {
  const [lobbyingData, setLobbyingData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilingType, setSelectedFilingType] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    loadLobbyingData();
  }, [currentPage, selectedFilingType]);

  useEffect(() => {
    applyFilters();
  }, [lobbyingData, searchTerm]);

  const loadLobbyingData = async () => {
    try {
      setLoading(true);
      const offset = (currentPage - 1) * pageSize;
      const result = await DataService.loadLobbyingData(
        selectedFilingType || null,
        pageSize,
        offset
      );

      if (result && result.filings) {
        setLobbyingData(result.filings);
        setTotalCount(result.total || result.filings.length);
      } else {
        setLobbyingData([]);
        setTotalCount(0);
      }
      setError(null);
    } catch (error) {
      console.error('Error loading lobbying data:', error);
      setError('Failed to load lobbying data. Please try again later.');
      setLobbyingData([]);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = lobbyingData;

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        filing =>
          filing.registrant?.name?.toLowerCase().includes(term) ||
          filing.client?.name?.toLowerCase().includes(term) ||
          filing.lobbying_activities?.some(
            activity =>
              activity.general_issue_code_display
                ?.toLowerCase()
                .includes(term) ||
              activity.description?.toLowerCase().includes(term)
          )
      );
    }

    setFilteredData(filtered);
  };

  const formatIncome = income => {
    if (!income || income === '0.00') return 'Not disclosed';
    return DataService.formatCurrency(parseFloat(income));
  };

  const getFilingTypeLabel = filingType => {
    const types = {
      RR: 'Registration',
      Q1: '1st Quarter Report',
      Q2: '2nd Quarter Report',
      Q3: '3rd Quarter Report',
      Q4: '4th Quarter Report',
      MR: 'Mid-Year Report',
      YE: 'Year-End Report',
      T: 'Termination',
    };
    return types[filingType] || filingType;
  };

  const getIssueTypeColor = issueCode => {
    const colors = {
      HCR: 'bg-red-100 text-red-800',
      DEF: 'bg-blue-100 text-blue-800',
      EDU: 'bg-green-100 text-green-800',
      ENV: 'bg-emerald-100 text-emerald-800',
      FIN: 'bg-yellow-100 text-yellow-800',
      ENE: 'bg-orange-100 text-orange-800',
      TRA: 'bg-purple-100 text-purple-800',
      AGR: 'bg-lime-100 text-lime-800',
      TEC: 'bg-indigo-100 text-indigo-800',
    };
    return colors[issueCode] || 'bg-gray-100 text-gray-800';
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600' />
      </div>
    );
  }

  if (error) {
    return (
      <div className='bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg'>
        {error}
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='bg-white rounded-lg shadow-sm p-6'>
        <div className='flex items-center gap-3 mb-4'>
          <Building className='text-blue-600' size={28} />
          <div>
            <h1 className='text-2xl font-bold text-gray-900'>
              Lobbying Disclosure Filings
            </h1>
            <p className='text-gray-600'>
              Senate lobbying disclosure database (LD-1 Registration & LD-2
              Activity Reports)
            </p>
          </div>
        </div>

        {/* Statistics */}
        <div className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-6'>
          <div className='bg-blue-50 p-4 rounded-lg'>
            <div className='flex items-center gap-2'>
              <FileText className='text-blue-600' size={20} />
              <span className='text-sm font-medium text-gray-600'>
                Total Filings
              </span>
            </div>
            <p className='text-2xl font-bold text-blue-900'>
              {totalCount.toLocaleString()}
            </p>
          </div>
          <div className='bg-green-50 p-4 rounded-lg'>
            <div className='flex items-center gap-2'>
              <Building className='text-green-600' size={20} />
              <span className='text-sm font-medium text-gray-600'>
                Active Page
              </span>
            </div>
            <p className='text-2xl font-bold text-green-900'>
              {currentPage} of {totalPages}
            </p>
          </div>
          <div className='bg-purple-50 p-4 rounded-lg'>
            <div className='flex items-center gap-2'>
              <Users className='text-purple-600' size={20} />
              <span className='text-sm font-medium text-gray-600'>
                Displayed
              </span>
            </div>
            <p className='text-2xl font-bold text-purple-900'>
              {filteredData.length}
            </p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className='bg-white rounded-lg shadow-sm p-6'>
        <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
          {/* Search */}
          <div className='relative'>
            <Search
              className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
              size={20}
            />
            <input
              type='text'
              placeholder='Search by registrant, client, or issue...'
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            />
          </div>

          {/* Filing Type Filter */}
          <div className='relative'>
            <Filter
              className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
              size={20}
            />
            <select
              value={selectedFilingType}
              onChange={e => {
                setSelectedFilingType(e.target.value);
                setCurrentPage(1);
              }}
              className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none'
            >
              <option value=''>All Filing Types</option>
              <option value='ld-1'>LD-1 Registration</option>
              <option value='ld-2'>LD-2 Activity Reports</option>
            </select>
          </div>
        </div>
      </div>

      {/* Filings List */}
      <div className='space-y-4'>
        {filteredData.map((filing, index) => (
          <div
            key={filing.filing_uuid || index}
            className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'
          >
            <div className='flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4'>
              {/* Main Content */}
              <div className='flex-1 space-y-3'>
                {/* Header */}
                <div className='flex flex-wrap items-center gap-2'>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      filing.filing_type === 'RR'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-green-100 text-green-800'
                    }`}
                  >
                    {getFilingTypeLabel(filing.filing_type)}
                  </span>
                  <span className='text-sm text-gray-500'>
                    {filing.filing_period_display} {filing.filing_year}
                  </span>
                  {filing.income && (
                    <div className='flex items-center gap-1'>
                      <DollarSign size={14} className='text-green-600' />
                      <span className='text-sm font-medium text-green-700'>
                        {formatIncome(filing.income)}
                      </span>
                    </div>
                  )}
                </div>

                {/* Organizations */}
                <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                  <div>
                    <h3 className='text-sm font-medium text-gray-500 mb-1'>
                      Registrant
                    </h3>
                    <p className='font-semibold text-gray-900'>
                      {filing.registrant?.name || 'Unknown'}
                    </p>
                    <p className='text-sm text-gray-600'>
                      {filing.registrant?.city}, {filing.registrant?.state}
                    </p>
                  </div>
                  <div>
                    <h3 className='text-sm font-medium text-gray-500 mb-1'>
                      Client
                    </h3>
                    <p className='font-semibold text-gray-900'>
                      {filing.client?.name || 'Unknown'}
                    </p>
                    {filing.client?.state && (
                      <p className='text-sm text-gray-600'>
                        {filing.client.state_display}
                      </p>
                    )}
                  </div>
                </div>

                {/* Lobbying Activities */}
                {filing.lobbying_activities?.length > 0 && (
                  <div>
                    <h3 className='text-sm font-medium text-gray-500 mb-2'>
                      Lobbying Issues
                    </h3>
                    <div className='flex flex-wrap gap-2'>
                      {filing.lobbying_activities
                        .slice(0, 5)
                        .map((activity, actIndex) => (
                          <span
                            key={actIndex}
                            className={`px-2 py-1 rounded-md text-xs font-medium ${getIssueTypeColor(activity.general_issue_code)}`}
                          >
                            {activity.general_issue_code_display}
                          </span>
                        ))}
                      {filing.lobbying_activities.length > 5 && (
                        <span className='px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-600'>
                          +{filing.lobbying_activities.length - 5} more
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Lobbyists */}
                {filing.lobbying_activities?.[0]?.lobbyists?.length > 0 && (
                  <div>
                    <h3 className='text-sm font-medium text-gray-500 mb-1'>
                      Lobbyists
                    </h3>
                    <p className='text-sm text-gray-700'>
                      {filing.lobbying_activities[0].lobbyists
                        .map(
                          l =>
                            `${l.lobbyist.first_name} ${l.lobbyist.last_name}`
                        )
                        .slice(0, 3)
                        .join(', ')}
                      {filing.lobbying_activities[0].lobbyists.length > 3 &&
                        ` +${filing.lobbying_activities[0].lobbyists.length - 3} more`}
                    </p>
                  </div>
                )}
              </div>

              {/* Sidebar */}
              <div className='flex flex-col items-end gap-2 text-right'>
                <div className='flex items-center gap-1 text-sm text-gray-500'>
                  <Calendar size={14} />
                  <span>{DataService.formatDate(filing.dt_posted)}</span>
                </div>
                {filing.filing_document_url && (
                  <a
                    href={filing.filing_document_url}
                    target='_blank'
                    rel='noopener noreferrer'
                    className='flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800'
                  >
                    <ExternalLink size={14} />
                    View Filing
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className='bg-white rounded-lg shadow-sm p-4'>
          <div className='flex items-center justify-between'>
            <div className='text-sm text-gray-600'>
              Showing {(currentPage - 1) * pageSize + 1} to{' '}
              {Math.min(currentPage * pageSize, totalCount)} of{' '}
              {totalCount.toLocaleString()} filings
            </div>
            <div className='flex gap-2'>
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className='px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 hover:bg-gray-50'
              >
                Previous
              </button>
              <span className='px-3 py-1 text-sm'>
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() =>
                  setCurrentPage(prev => Math.min(totalPages, prev + 1))
                }
                disabled={currentPage === totalPages}
                className='px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 hover:bg-gray-50'
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {filteredData.length === 0 && !loading && (
        <div className='bg-gray-50 border border-gray-200 text-gray-700 px-4 py-8 rounded-lg text-center'>
          <Building size={48} className='mx-auto text-gray-400 mb-4' />
          <p className='text-lg font-medium mb-2'>No lobbying filings found</p>
          <p className='text-sm'>
            {searchTerm || selectedFilingType
              ? 'Try adjusting your filters or search terms.'
              : 'Lobbying data may still be loading or not available for this period.'}
          </p>
        </div>
      )}
    </div>
  );
}

export default Lobbying;
