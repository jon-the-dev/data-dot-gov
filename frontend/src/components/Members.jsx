import {
  Search,
  MapPin,
  Building2,
  Mail,
  Phone,
  ExternalLink,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react';
import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';

import DataService from '../services/dataService';

function Members({ data }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedParty, setSelectedParty] = useState('all');
  const [selectedState, setSelectedState] = useState('all');
  const [selectedChamber, setSelectedChamber] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(24); // Default to 24 items per page

  const { membersSummary } = data;

  const getFilteredMembers = () => {
    if (!membersSummary || !membersSummary.members) return [];

    let members = [...membersSummary.members];

    if (searchTerm) {
      members = members.filter(
        m =>
          m.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          m.state?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedParty !== 'all') {
      members = members.filter(m => m.party === selectedParty);
    }

    if (selectedState !== 'all') {
      members = members.filter(m => m.state === selectedState);
    }

    if (selectedChamber !== 'all') {
      // We can infer chamber from district - if district exists, it's House, otherwise Senate
      if (selectedChamber === 'House') {
        members = members.filter(
          m => m.district !== null && m.district !== undefined
        );
      } else if (selectedChamber === 'Senate') {
        members = members.filter(
          m => m.district === null || m.district === undefined
        );
      }
    }

    return members;
  };

  const getStates = () => {
    if (!membersSummary || !membersSummary.members) return [];
    const states = [
      ...new Set(membersSummary.members.map(m => m.state).filter(Boolean)),
    ];
    return states.sort();
  };

  const MemberCard = ({ member }) => {
    const partyColor =
      member.party === 'Republican'
        ? 'border-republican'
        : member.party === 'Democratic'
          ? 'border-democrat'
          : 'border-independent';

    const isHouse = member.district !== null && member.district !== undefined;
    const chamber = isHouse ? 'House' : 'Senate';
    const title = isHouse ? 'Representative' : 'Senator';

    return (
      <Link
        to={`/members/${member.bioguideId}`}
        className={`block bg-white p-4 rounded-lg border-2 ${partyColor} hover:shadow-lg transition-all h-full`}
      >
        <div className='flex flex-col items-center text-center'>
          <div className='w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center text-gray-500 font-semibold text-sm'>
            {member.name
              ?.split(' ')
              .map(n => n[0])
              .join('') || '?'}
          </div>
          <h3 className='font-semibold text-gray-900 mt-3'>
            {member.name || 'Unknown'}
          </h3>
          <div className='flex items-center gap-2 mt-2'>
            <span
              className={`text-xs font-medium px-2 py-1 rounded ${
                member.party === 'Republican'
                  ? 'bg-republican text-white'
                  : member.party === 'Democratic'
                    ? 'bg-democrat text-white'
                    : 'bg-independent text-white'
              }`}
            >
              {member.party?.[0] || '?'}
            </span>
            <span className='text-xs text-gray-600'>{title}</span>
          </div>
          <div className='flex items-center gap-1 mt-2 text-xs text-gray-600'>
            <MapPin size={12} />
            <span>{member.state || 'Unknown'}</span>
            {isHouse && <span>- District {member.district}</span>}
          </div>
          <div className='flex items-center gap-1 mt-3 text-xs text-blue-600'>
            <span>View Details</span>
            <ChevronRight size={12} />
          </div>
        </div>
      </Link>
    );
  };

  const filteredMembers = getFilteredMembers();
  const states = getStates();

  // Calculate party breakdown from actual members
  const partyBreakdown = useMemo(() => {
    if (!membersSummary?.members)
      return { Democratic: 0, Republican: 0, Independent: 0 };

    const breakdown = membersSummary.members.reduce((acc, member) => {
      const party = member.party || 'Unknown';
      acc[party] = (acc[party] || 0) + 1;
      return acc;
    }, {});

    return {
      Democratic: breakdown.Democratic || breakdown.Democrat || 0,
      Republican: breakdown.Republican || 0,
      Independent: breakdown.Independent || 0,
    };
  }, [membersSummary]);

  // Pagination calculations
  const totalPages = Math.ceil(filteredMembers.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedMembers = filteredMembers.slice(startIndex, endIndex);

  // Reset to page 1 when filters or page size change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedParty, selectedState, selectedChamber, itemsPerPage]);

  // Handle page size change
  const handlePageSizeChange = newSize => {
    setItemsPerPage(Number(newSize));
  };

  return (
    <div className='space-y-6'>
      <div>
        <h2 className='text-2xl font-bold text-gray-900 mb-4'>
          Congressional Members
        </h2>
        <p className='text-gray-600'>
          Browse and search {membersSummary?.members?.length || 0} members of
          the 118th Congress
        </p>
      </div>

      {/* Search and Filters */}
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
                placeholder='Search by name or state...'
                className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className='flex gap-2'>
            <select
              className='px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
              value={selectedParty}
              onChange={e => setSelectedParty(e.target.value)}
            >
              <option value='all'>All Parties</option>
              <option value='Democratic'>
                Democratic ({partyBreakdown.Democratic || 0})
              </option>
              <option value='Republican'>
                Republican ({partyBreakdown.Republican || 0})
              </option>
              <option value='Independent'>
                Independent ({partyBreakdown.Independent || 0})
              </option>
            </select>
            <select
              className='px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
              value={selectedState}
              onChange={e => setSelectedState(e.target.value)}
            >
              <option value='all'>All States</option>
              {states.map(state => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
            <select
              className='px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
              value={selectedChamber}
              onChange={e => setSelectedChamber(e.target.value)}
            >
              <option value='all'>Both Chambers</option>
              <option value='Senate'>Senate</option>
              <option value='House'>House</option>
            </select>
          </div>
        </div>
      </div>

      {/* Party Summary */}
      <div className='grid grid-cols-3 gap-4'>
        <div className='bg-blue-50 border border-blue-200 p-4 rounded-lg'>
          <p className='text-2xl font-bold text-democrat'>
            {partyBreakdown.Democratic || 0}
          </p>
          <p className='text-sm text-gray-600'>Democrats</p>
        </div>
        <div className='bg-red-50 border border-red-200 p-4 rounded-lg'>
          <p className='text-2xl font-bold text-republican'>
            {partyBreakdown.Republican || 0}
          </p>
          <p className='text-sm text-gray-600'>Republicans</p>
        </div>
        <div className='bg-purple-50 border border-purple-200 p-4 rounded-lg'>
          <p className='text-2xl font-bold text-independent'>
            {partyBreakdown.Independent || 0}
          </p>
          <p className='text-sm text-gray-600'>Independents</p>
        </div>
      </div>

      {/* Results Count and Controls */}
      <div className='flex flex-col md:flex-row justify-between items-start md:items-center gap-4'>
        <div className='flex items-center gap-4'>
          <div className='text-sm text-gray-600'>
            Showing {startIndex + 1}-
            {Math.min(endIndex, filteredMembers.length)} of{' '}
            {filteredMembers.length} filtered results (
            {membersSummary?.members?.length || 0} total members)
          </div>

          {/* Page Size Selector */}
          <div className='flex items-center gap-2'>
            <label className='text-sm text-gray-600'>Show:</label>
            <select
              className='px-3 py-1 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm'
              value={itemsPerPage}
              onChange={e => handlePageSizeChange(e.target.value)}
            >
              <option value={24}>24</option>
              <option value={48}>48</option>
              <option value={96}>96</option>
            </select>
            <span className='text-sm text-gray-600'>per page</span>
          </div>
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className='flex items-center gap-2'>
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className='px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1'
            >
              <ChevronLeft size={16} />
              Previous
            </button>

            <div className='flex gap-1'>
              {[...Array(Math.min(5, totalPages))].map((_, idx) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = idx + 1;
                } else if (currentPage <= 3) {
                  pageNum = idx + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + idx;
                } else {
                  pageNum = currentPage - 2 + idx;
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-1 rounded ${
                      currentPage === pageNum
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 hover:bg-gray-50'
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
              className='px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1'
            >
              Next
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Members Grid - Updated to show 3-4 per row */}
      {filteredMembers.length > 0 ? (
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'>
          {paginatedMembers.map(member => (
            <MemberCard key={member.bioguideId} member={member} />
          ))}
        </div>
      ) : (
        <div className='bg-gray-50 border border-gray-200 rounded-lg p-8 text-center'>
          <p className='text-gray-500'>
            No members found matching your criteria
          </p>
        </div>
      )}
    </div>
  );
}

export default Members;
