import {
  Search,
  Filter,
  Building2,
  Users,
  AlertCircle,
  Clock,
  ChevronDown,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

import DataService from '../services/dataService';

import CommitteeCard from './CommitteeCard';

function CommitteesList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [committees, setCommittees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchTerm, setSearchTerm] = useState(
    searchParams.get('search') || ''
  );
  const [selectedChamber, setSelectedChamber] = useState(
    searchParams.get('chamber') || 'all'
  );

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(12);

  useEffect(() => {
    loadCommittees();
  }, []);

  // Update URL params when filters change
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchTerm) params.set('search', searchTerm);
    if (selectedChamber !== 'all') params.set('chamber', selectedChamber);
    setSearchParams(params);
  }, [searchTerm, selectedChamber, setSearchParams]);

  const loadCommittees = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await DataService.loadCommittees();

      if (data && Array.isArray(data.committees)) {
        setCommittees(data.committees);
      } else if (Array.isArray(data)) {
        setCommittees(data);
      } else {
        setCommittees([]);
        setError('Invalid committee data format');
      }
    } catch (err) {
      console.error('Error loading committees:', err);
      setError('Failed to load committees');
      setCommittees([]);
    } finally {
      setLoading(false);
    }
  };

  // Filter committees based on search and chamber
  const filteredCommittees = committees.filter(committee => {
    const matchesSearch =
      !searchTerm ||
      committee.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      committee.code?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesChamber =
      selectedChamber === 'all' ||
      committee.chamber?.toLowerCase() === selectedChamber.toLowerCase();

    return matchesSearch && matchesChamber;
  });

  // Paginate results
  const totalPages = Math.ceil(filteredCommittees.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedCommittees = filteredCommittees.slice(
    startIndex,
    startIndex + itemsPerPage
  );

  // Get chamber summary
  const chamberSummary = committees.reduce((acc, committee) => {
    const chamber = committee.chamber || 'Unknown';
    acc[chamber] = (acc[chamber] || 0) + 1;
    return acc;
  }, {});

  if (loading) {
    return (
      <div className='space-y-6'>
        <div className='flex items-center gap-3'>
          <Clock className='text-blue-500 animate-spin' size={24} />
          <div>
            <h1 className='text-3xl font-bold text-gray-900'>
              Congressional Committees
            </h1>
            <p className='text-gray-600'>Loading committee information...</p>
          </div>
        </div>

        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className='bg-white p-6 rounded-lg border border-gray-200 animate-pulse'
            >
              <div className='space-y-4'>
                <div className='flex items-start justify-between'>
                  <div className='flex items-center space-x-3'>
                    <div className='p-2 bg-gray-200 rounded-lg w-9 h-9' />
                    <div className='h-6 w-20 bg-gray-200 rounded-full' />
                  </div>
                </div>
                <div className='h-6 bg-gray-200 rounded w-3/4' />
                <div className='h-4 bg-gray-200 rounded w-1/2' />
                <div className='flex items-center justify-between pt-2'>
                  <div className='h-4 bg-gray-200 rounded w-1/3' />
                  <div className='h-4 bg-gray-200 rounded w-1/4' />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className='space-y-6'>
        <div>
          <h1 className='text-3xl font-bold text-gray-900'>
            Congressional Committees
          </h1>
          <p className='text-gray-600'>Committee information and oversight</p>
        </div>

        <div className='bg-red-50 border border-red-200 rounded-lg p-6'>
          <div className='flex items-center gap-3'>
            <AlertCircle className='text-red-500' size={24} />
            <div>
              <h3 className='text-lg font-semibold text-red-800'>
                Error Loading Committees
              </h3>
              <p className='text-red-700'>{error}</p>
              <button
                onClick={loadCommittees}
                className='mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700'
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div>
        <h1 className='text-3xl font-bold text-gray-900'>
          Congressional Committees
        </h1>
        <p className='text-gray-600'>
          {committees.length} committees overseeing legislation and government
          operations
        </p>
      </div>

      {/* Summary Cards */}
      {Object.keys(chamberSummary).length > 0 && (
        <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
          <div className='bg-white p-4 rounded-lg border border-gray-200'>
            <p className='text-2xl font-bold text-gray-900'>
              {committees.length}
            </p>
            <p className='text-sm text-gray-600'>Total Committees</p>
          </div>
          {Object.entries(chamberSummary)
            .sort((a, b) => b[1] - a[1])
            .map(([chamber, count]) => {
              const colorClass =
                chamber === 'House'
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : chamber === 'Senate'
                    ? 'bg-red-50 border-red-200 text-red-700'
                    : chamber === 'Joint'
                      ? 'bg-purple-50 border-purple-200 text-purple-700'
                      : 'bg-gray-50 border-gray-200 text-gray-700';

              return (
                <div
                  key={chamber}
                  className={`p-4 rounded-lg border-2 ${colorClass}`}
                >
                  <p className='text-2xl font-bold'>{count}</p>
                  <p className='text-sm opacity-80'>{chamber} Committees</p>
                </div>
              );
            })}
        </div>
      )}

      {/* Search and Filter Bar */}
      <div className='bg-white p-4 rounded-lg shadow-sm border border-gray-200'>
        <div className='flex flex-col md:flex-row gap-4'>
          <div className='flex-1'>
            <div className='relative'>
              <Search
                className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
                size={20}
              />
              <input
                type='text'
                placeholder='Search committees by name or code...'
                className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className='flex gap-2'>
            <div className='relative'>
              <Filter
                className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
                size={16}
              />
              <select
                className='pl-9 pr-8 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white'
                value={selectedChamber}
                onChange={e => setSelectedChamber(e.target.value)}
              >
                <option value='all'>All Chambers</option>
                <option value='house'>
                  House ({chamberSummary.House || 0})
                </option>
                <option value='senate'>
                  Senate ({chamberSummary.Senate || 0})
                </option>
                <option value='joint'>
                  Joint ({chamberSummary.Joint || 0})
                </option>
              </select>
              <ChevronDown
                className='absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400'
                size={16}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Results Summary */}
      {(searchTerm || selectedChamber !== 'all') && (
        <div className='bg-blue-50 border border-blue-200 rounded-lg p-3'>
          <div className='flex items-center gap-2'>
            <Users size={16} className='text-blue-600' />
            <span className='text-sm text-blue-700'>
              Showing {filteredCommittees.length} of {committees.length}{' '}
              committees
              {searchTerm && ` matching "${searchTerm}"`}
              {selectedChamber !== 'all' && ` in the ${selectedChamber}`}
            </span>
            {(searchTerm || selectedChamber !== 'all') && (
              <button
                onClick={() => {
                  setSearchTerm('');
                  setSelectedChamber('all');
                  setCurrentPage(1);
                }}
                className='ml-auto text-xs text-blue-600 hover:text-blue-700 font-medium'
              >
                Clear filters
              </button>
            )}
          </div>
        </div>
      )}

      {/* Committees Grid */}
      {paginatedCommittees.length > 0 ? (
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>
          {paginatedCommittees.map(committee => (
            <CommitteeCard
              key={committee.id || committee.code}
              committee={committee}
            />
          ))}
        </div>
      ) : filteredCommittees.length === 0 && committees.length > 0 ? (
        <div className='bg-gray-50 border border-gray-200 rounded-lg p-8 text-center'>
          <Building2 className='mx-auto text-gray-400 mb-4' size={48} />
          <h3 className='text-lg font-semibold text-gray-900 mb-2'>
            No Committees Found
          </h3>
          <p className='text-gray-500 mb-4'>
            No committees match your current search criteria
          </p>
          <button
            onClick={() => {
              setSearchTerm('');
              setSelectedChamber('all');
              setCurrentPage(1);
            }}
            className='text-blue-600 hover:text-blue-700 font-medium'
          >
            Clear filters and see all committees
          </button>
        </div>
      ) : (
        <div className='bg-gray-50 border border-gray-200 rounded-lg p-8 text-center'>
          <Building2 className='mx-auto text-gray-400 mb-4' size={48} />
          <h3 className='text-lg font-semibold text-gray-900 mb-2'>
            No Committee Data
          </h3>
          <p className='text-gray-500'>
            Committee information is not yet available in the system
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className='flex justify-center items-center gap-2'>
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className='px-3 py-2 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50'
          >
            Previous
          </button>

          <div className='flex gap-1'>
            {[...Array(Math.min(5, totalPages))].map((_, i) => {
              const pageNum =
                Math.max(1, Math.min(currentPage - 2, totalPages - 4)) + i;
              if (pageNum > totalPages) return null;

              return (
                <button
                  key={pageNum}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`px-3 py-2 border rounded text-sm ${
                    currentPage === pageNum
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <button
            onClick={() =>
              setCurrentPage(Math.min(totalPages, currentPage + 1))
            }
            disabled={currentPage === totalPages}
            className='px-3 py-2 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50'
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default CommitteesList;
