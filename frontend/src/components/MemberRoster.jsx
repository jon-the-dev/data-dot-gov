import {
  Search,
  MapPin,
  Star,
  Users,
  ChevronRight,
  AlertCircle,
  Clock,
} from 'lucide-react';
import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

function MemberRoster({
  members = [],
  loading = false,
  title = 'Committee Members',
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedParty, setSelectedParty] = useState('all');
  const [selectedRole, setSelectedRole] = useState('all');

  // Extract unique roles and parties from members
  const getUniqueRoles = () => {
    if (!members || members.length === 0) return [];
    const roles = [...new Set(members.map(m => m.role).filter(Boolean))];
    return roles.sort();
  };

  const getUniqueParties = () => {
    if (!members || members.length === 0) return [];
    const parties = [...new Set(members.map(m => m.party).filter(Boolean))];
    return parties.sort();
  };

  // Filter members based on search and filters
  const getFilteredMembers = () => {
    if (!members || members.length === 0) return [];

    let filteredMembers = [...members];

    if (searchTerm) {
      filteredMembers = filteredMembers.filter(
        m =>
          m.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          m.state?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          m.role?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (selectedParty !== 'all') {
      filteredMembers = filteredMembers.filter(m => m.party === selectedParty);
    }

    if (selectedRole !== 'all') {
      filteredMembers = filteredMembers.filter(m => m.role === selectedRole);
    }

    return filteredMembers;
  };

  // Get role badge styling
  const getRoleBadge = role => {
    if (!role) return null;

    const roleStyles = {
      Chair: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'Ranking Member': 'bg-purple-100 text-purple-800 border-purple-200',
      'Vice Chair': 'bg-blue-100 text-blue-800 border-blue-200',
      'Senior Member': 'bg-green-100 text-green-800 border-green-200',
      Member: 'bg-gray-100 text-gray-800 border-gray-200',
      'Ex Officio': 'bg-orange-100 text-orange-800 border-orange-200',
    };

    const styleClass =
      roleStyles[role] || 'bg-gray-100 text-gray-800 border-gray-200';

    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border ${styleClass}`}
      >
        {(role === 'Chair' || role === 'Ranking Member') && <Star size={10} />}
        {role}
      </span>
    );
  };

  const MemberCard = ({ member }) => {
    // Normalize party names for consistent styling
    const normalizedParty =
      member.party === 'R'
        ? 'Republican'
        : member.party === 'D'
          ? 'Democratic'
          : member.party === 'I'
            ? 'Independent'
            : member.party;

    const partyColor =
      normalizedParty === 'Republican'
        ? 'border-red-300 hover:border-red-400'
        : normalizedParty === 'Democratic' || normalizedParty === 'Democrat'
          ? 'border-blue-300 hover:border-blue-400'
          : normalizedParty === 'Independent'
            ? 'border-purple-300 hover:border-purple-400'
            : 'border-gray-300 hover:border-gray-400';

    const isHouse = member.district !== null && member.district !== undefined;
    const memberTitle = isHouse ? 'Representative' : 'Senator';

    return (
      <Link
        to={`/members/${member.bioguideId || member.member_id}`}
        className={`block bg-white p-4 rounded-lg border-2 ${partyColor} hover:shadow-lg transition-all h-full`}
      >
        <div className='flex flex-col items-center text-center space-y-3'>
          {/* Member Photo/Avatar */}
          <div className='w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center text-gray-500 font-semibold'>
            {member.photo_url ? (
              <img
                src={member.photo_url}
                alt={member.name}
                className='w-16 h-16 rounded-full object-cover'
                onError={e => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
              />
            ) : null}
            <div
              className='w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center text-gray-500 font-semibold'
              style={{ display: member.photo_url ? 'none' : 'flex' }}
            >
              {member.name
                ?.split(' ')
                .map(n => n[0])
                .join('') || '?'}
            </div>
          </div>

          {/* Member Name */}
          <h3 className='font-semibold text-gray-900 text-sm leading-tight'>
            {member.name || 'Unknown Member'}
          </h3>

          {/* Role Badge */}
          <div className='flex flex-col items-center gap-2'>
            {getRoleBadge(member.role)}
          </div>

          {/* Party and Title */}
          <div className='flex items-center gap-2'>
            <span
              className={`text-xs font-medium px-2 py-1 rounded ${
                normalizedParty === 'Republican'
                  ? 'bg-red-500 text-white'
                  : normalizedParty === 'Democratic' ||
                      normalizedParty === 'Democrat'
                    ? 'bg-blue-500 text-white'
                    : normalizedParty === 'Independent'
                      ? 'bg-purple-500 text-white'
                      : 'bg-gray-500 text-white'
              }`}
            >
              {member.party?.[0] || normalizedParty?.[0] || '?'}
            </span>
            <span className='text-xs text-gray-600'>{memberTitle}</span>
          </div>

          {/* State/District */}
          <div className='flex items-center gap-1 text-xs text-gray-600'>
            <MapPin size={12} />
            <span>{member.state || 'Unknown'}</span>
            {isHouse && member.district && <span>-{member.district}</span>}
          </div>

          {/* View Details Link */}
          <div className='flex items-center gap-1 text-xs text-blue-600 pt-2'>
            <span>View Details</span>
            <ChevronRight size={12} />
          </div>
        </div>
      </Link>
    );
  };

  const filteredMembers = getFilteredMembers();
  const uniqueRoles = getUniqueRoles();
  const uniqueParties = getUniqueParties();

  // Calculate party and role breakdowns
  const partyBreakdown = useMemo(() => {
    if (!members || members.length === 0) return {};

    return members.reduce((acc, member) => {
      const party = member.party || 'Unknown';
      acc[party] = (acc[party] || 0) + 1;
      return acc;
    }, {});
  }, [members]);

  const roleBreakdown = useMemo(() => {
    if (!members || members.length === 0) return {};

    return members.reduce((acc, member) => {
      const role = member.role || 'Member';
      acc[role] = (acc[role] || 0) + 1;
      return acc;
    }, {});
  }, [members]);

  // Loading state
  if (loading) {
    return (
      <div className='space-y-6'>
        <div className='flex items-center gap-3'>
          <Clock className='text-blue-500 animate-spin' size={24} />
          <div>
            <h2 className='text-2xl font-bold text-gray-900'>{title}</h2>
            <p className='text-gray-600'>Loading committee members...</p>
          </div>
        </div>

        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'>
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className='bg-white p-4 rounded-lg border-2 border-gray-200 animate-pulse'
            >
              <div className='flex flex-col items-center text-center space-y-3'>
                <div className='w-16 h-16 bg-gray-300 rounded-full' />
                <div className='h-4 bg-gray-300 rounded w-24' />
                <div className='h-3 bg-gray-300 rounded w-16' />
                <div className='h-3 bg-gray-300 rounded w-12' />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Empty state - no members available yet
  if (!members || members.length === 0) {
    return (
      <div className='space-y-6'>
        <div>
          <h2 className='text-2xl font-bold text-gray-900'>{title}</h2>
          <p className='text-gray-600'>Committee member information</p>
        </div>

        <div className='bg-amber-50 border border-amber-200 rounded-lg p-8 text-center'>
          <AlertCircle className='mx-auto text-amber-500 mb-4' size={48} />
          <h3 className='text-lg font-semibold text-amber-800 mb-2'>
            Member Data Pending
          </h3>
          <p className='text-amber-700 mb-4'>
            Committee member information is not yet available. This may be
            because:
          </p>
          <ul className='text-left text-amber-700 text-sm space-y-1 max-w-md mx-auto'>
            <li>• Member data is still being loaded</li>
            <li>
              • Committee membership data is not available in our current
              dataset
            </li>
            <li>• The committee may be newly formed or restructured</li>
          </ul>
          <p className='text-amber-600 text-sm mt-4'>
            We're working on improving our data coverage and will update this
            information as it becomes available.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div>
        <h2 className='text-2xl font-bold text-gray-900'>{title}</h2>
        <p className='text-gray-600'>
          {members.length} member{members.length !== 1 ? 's' : ''} serving on
          this committee
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
                placeholder='Search by name, state, or role...'
                className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className='flex gap-2'>
            {uniqueParties.length > 0 && (
              <select
                className='px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                value={selectedParty}
                onChange={e => setSelectedParty(e.target.value)}
              >
                <option value='all'>All Parties</option>
                {uniqueParties.map(party => (
                  <option key={party} value={party}>
                    {party} ({partyBreakdown[party] || 0})
                  </option>
                ))}
              </select>
            )}
            {uniqueRoles.length > 0 && (
              <select
                className='px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                value={selectedRole}
                onChange={e => setSelectedRole(e.target.value)}
              >
                <option value='all'>All Roles</option>
                {uniqueRoles.map(role => (
                  <option key={role} value={role}>
                    {role} ({roleBreakdown[role] || 0})
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {Object.keys(partyBreakdown).length > 0 && (
        <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
          {Object.entries(partyBreakdown)
            .sort((a, b) => b[1] - a[1])
            .map(([party, count]) => {
              // Normalize party names for consistent styling
              const normalizedPartyName =
                party === 'R'
                  ? 'Republican'
                  : party === 'D'
                    ? 'Democratic'
                    : party === 'I'
                      ? 'Independent'
                      : party;

              const colorClass =
                normalizedPartyName === 'Republican'
                  ? 'bg-red-50 border-red-200 text-red-700'
                  : normalizedPartyName === 'Democratic' ||
                      normalizedPartyName === 'Democrat'
                    ? 'bg-blue-50 border-blue-200 text-blue-700'
                    : normalizedPartyName === 'Independent'
                      ? 'bg-purple-50 border-purple-200 text-purple-700'
                      : 'bg-gray-50 border-gray-200 text-gray-700';

              return (
                <div
                  key={party}
                  className={`${colorClass} border p-4 rounded-lg`}
                >
                  <p className='text-2xl font-bold'>{count}</p>
                  <p className='text-sm opacity-80'>{normalizedPartyName}</p>
                </div>
              );
            })}
        </div>
      )}

      {/* Results Count */}
      {searchTerm || selectedParty !== 'all' || selectedRole !== 'all' ? (
        <div className='text-sm text-gray-600'>
          Showing {filteredMembers.length} of {members.length} members
        </div>
      ) : null}

      {/* Members Grid */}
      {filteredMembers.length > 0 ? (
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'>
          {filteredMembers.map(member => (
            <MemberCard
              key={member.bioguideId || member.member_id || member.name}
              member={member}
            />
          ))}
        </div>
      ) : (
        <div className='bg-gray-50 border border-gray-200 rounded-lg p-8 text-center'>
          <Users className='mx-auto text-gray-400 mb-4' size={48} />
          <p className='text-gray-500'>
            No members found matching your search criteria
          </p>
          {(searchTerm ||
            selectedParty !== 'all' ||
            selectedRole !== 'all') && (
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedParty('all');
                setSelectedRole('all');
              }}
              className='mt-3 text-blue-600 hover:text-blue-700 text-sm'
            >
              Clear filters
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default MemberRoster;
