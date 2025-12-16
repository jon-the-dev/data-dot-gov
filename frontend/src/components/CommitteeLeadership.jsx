import {
  Star,
  Crown,
  Shield,
  MapPin,
  Phone,
  Mail,
  ExternalLink,
  Users,
  AlertCircle,
} from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

function CommitteeLeadership({
  leadership = [],
  committeeInfo = null,
  loading = false,
}) {
  const [selectedMember, setSelectedMember] = useState(null);

  // Get party color styling
  const getPartyStyles = party => {
    const normalizedParty =
      party === 'R'
        ? 'Republican'
        : party === 'D'
          ? 'Democratic'
          : party === 'I'
            ? 'Independent'
            : party;

    switch (normalizedParty) {
      case 'Republican':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-700',
          accent: 'bg-red-500',
        };
      case 'Democratic':
      case 'Democrat':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-700',
          accent: 'bg-blue-500',
        };
      case 'Independent':
        return {
          bg: 'bg-purple-50',
          border: 'border-purple-200',
          text: 'text-purple-700',
          accent: 'bg-purple-500',
        };
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-700',
          accent: 'bg-gray-500',
        };
    }
  };

  // Get role icon and styling
  const getRoleInfo = role => {
    switch (role?.toLowerCase()) {
      case 'chair':
      case 'chairman':
      case 'chairwoman':
        return {
          icon: Crown,
          label: 'Chair',
          priority: 1,
          bg: 'bg-yellow-100',
          text: 'text-yellow-800',
          border: 'border-yellow-200',
        };
      case 'ranking member':
        return {
          icon: Shield,
          label: 'Ranking Member',
          priority: 2,
          bg: 'bg-purple-100',
          text: 'text-purple-800',
          border: 'border-purple-200',
        };
      case 'vice chair':
      case 'vice chairman':
        return {
          icon: Star,
          label: 'Vice Chair',
          priority: 3,
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          border: 'border-blue-200',
        };
      default:
        return {
          icon: Star,
          label: role || 'Member',
          priority: 4,
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200',
        };
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-3 mb-4'>
          <div className='animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-600' />
          <h3 className='text-lg font-semibold text-gray-900'>
            Committee Leadership
          </h3>
        </div>

        <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
          {[...Array(2)].map((_, i) => (
            <div key={i} className='animate-pulse'>
              <div className='flex items-center gap-4 p-4 border border-gray-200 rounded-lg'>
                <div className='w-16 h-16 bg-gray-300 rounded-full' />
                <div className='flex-1 space-y-2'>
                  <div className='h-4 bg-gray-300 rounded w-3/4' />
                  <div className='h-3 bg-gray-300 rounded w-1/2' />
                  <div className='h-3 bg-gray-300 rounded w-1/3' />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Empty state
  if (!leadership || leadership.length === 0) {
    return (
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex items-center gap-3 mb-4'>
          <Crown className='h-6 w-6 text-yellow-600' />
          <h3 className='text-lg font-semibold text-gray-900'>
            Committee Leadership
          </h3>
        </div>

        <div className='bg-amber-50 border border-amber-200 rounded-lg p-6 text-center'>
          <AlertCircle className='mx-auto text-amber-500 mb-3' size={32} />
          <h4 className='text-md font-medium text-amber-800 mb-2'>
            Leadership Information Pending
          </h4>
          <p className='text-amber-700 text-sm'>
            Committee leadership data is not yet available in our current
            dataset.
          </p>
        </div>
      </div>
    );
  }

  // Sort leadership by priority (Chair first, then Ranking Member, etc.)
  const sortedLeadership = [...leadership].sort((a, b) => {
    const aInfo = getRoleInfo(a.role);
    const bInfo = getRoleInfo(b.role);
    return aInfo.priority - bInfo.priority;
  });

  const LeadershipCard = ({ leader }) => {
    const partyStyles = getPartyStyles(leader.party);
    const roleInfo = getRoleInfo(leader.role);
    const RoleIcon = roleInfo.icon;

    return (
      <div
        className={`relative border-2 ${partyStyles.border} rounded-lg overflow-hidden hover:shadow-lg transition-all`}
      >
        {/* Role priority indicator */}
        {roleInfo.priority <= 2 && (
          <div
            className={`absolute top-0 left-0 ${roleInfo.bg} ${roleInfo.text} px-3 py-1 text-xs font-medium`}
          >
            {roleInfo.label}
          </div>
        )}

        <div className={`${partyStyles.bg} p-6`}>
          <div className='flex items-start gap-4'>
            {/* Member Photo/Avatar */}
            <div className='flex-shrink-0'>
              {leader.photo_url ? (
                <img
                  src={leader.photo_url}
                  alt={leader.name}
                  className='w-16 h-16 rounded-full object-cover border-2 border-white shadow-sm'
                  onError={e => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'flex';
                  }}
                />
              ) : null}
              <div
                className={`w-16 h-16 ${partyStyles.accent} rounded-full flex items-center justify-center text-white font-bold text-lg shadow-sm`}
                style={{ display: leader.photo_url ? 'none' : 'flex' }}
              >
                {leader.name
                  ?.split(' ')
                  .map(n => n[0])
                  .join('')
                  .substring(0, 2) || '?'}
              </div>
            </div>

            {/* Member Info */}
            <div className='flex-1 min-w-0'>
              <div className='flex items-start justify-between mb-2'>
                <Link
                  to={`/members/${leader.bioguideId || leader.member_id}`}
                  className='font-bold text-gray-900 text-lg hover:text-blue-600 hover:underline'
                >
                  {leader.name || 'Unknown Member'}
                </Link>
                <RoleIcon
                  className={`${roleInfo.text} ml-2 flex-shrink-0`}
                  size={20}
                />
              </div>

              <div
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${roleInfo.bg} ${roleInfo.text} ${roleInfo.border} mb-3`}
              >
                {roleInfo.label}
              </div>

              {/* Party and State */}
              <div className='grid grid-cols-2 gap-4 text-sm'>
                <div>
                  <p className='text-gray-600'>Party</p>
                  <div className='flex items-center gap-2'>
                    <span
                      className={`w-3 h-3 rounded-full ${partyStyles.accent}`}
                    ></span>
                    <span className={`font-medium ${partyStyles.text}`}>
                      {leader.party === 'R'
                        ? 'Republican'
                        : leader.party === 'D'
                          ? 'Democratic'
                          : leader.party === 'I'
                            ? 'Independent'
                            : leader.party}
                    </span>
                  </div>
                </div>
                <div>
                  <p className='text-gray-600'>State</p>
                  <div className='flex items-center gap-1'>
                    <MapPin size={12} className='text-gray-400' />
                    <span className='font-medium text-gray-900'>
                      {leader.state || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Contact Info (if available) */}
              {(leader.phone || leader.email || leader.website) && (
                <div className='mt-3 pt-3 border-t border-gray-200'>
                  <div className='flex flex-wrap gap-3 text-xs'>
                    {leader.phone && (
                      <div className='flex items-center gap-1 text-gray-600'>
                        <Phone size={10} />
                        <span>{leader.phone}</span>
                      </div>
                    )}
                    {leader.email && (
                      <div className='flex items-center gap-1 text-gray-600'>
                        <Mail size={10} />
                        <span>{leader.email}</span>
                      </div>
                    )}
                    {leader.website && (
                      <a
                        href={leader.website}
                        target='_blank'
                        rel='noopener noreferrer'
                        className='flex items-center gap-1 text-blue-600 hover:text-blue-800'
                      >
                        <ExternalLink size={10} />
                        <span>Website</span>
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
      {/* Header */}
      <div className='px-6 py-4 border-b border-gray-200'>
        <div className='flex items-center justify-between'>
          <div className='flex items-center gap-3'>
            <Crown className='h-6 w-6 text-yellow-600' />
            <div>
              <h3 className='text-lg font-semibold text-gray-900'>
                Committee Leadership
              </h3>
              <p className='text-sm text-gray-600'>
                {committeeInfo?.name || 'Committee'} leadership team
              </p>
            </div>
          </div>
          <div className='flex items-center gap-2 text-sm text-gray-500'>
            <Users size={16} />
            <span>
              {leadership.length} leader{leadership.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </div>

      {/* Leadership Grid */}
      <div className='p-6'>
        <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
          {sortedLeadership.map((leader, index) => (
            <LeadershipCard
              key={leader.bioguideId || leader.member_id || index}
              leader={leader}
            />
          ))}
        </div>

        {/* Committee info summary */}
        {committeeInfo && (
          <div className='mt-6 pt-6 border-t border-gray-200'>
            <div className='grid grid-cols-1 md:grid-cols-3 gap-4 text-center'>
              <div className='p-4 bg-gray-50 rounded-lg'>
                <p className='text-2xl font-bold text-gray-900'>
                  {leadership.length}
                </p>
                <p className='text-sm text-gray-600'>Leadership Positions</p>
              </div>
              <div className='p-4 bg-gray-50 rounded-lg'>
                <p className='text-2xl font-bold text-gray-900'>
                  {committeeInfo.subcommittees?.length ||
                    committeeInfo.subcommittee_count ||
                    0}
                </p>
                <p className='text-sm text-gray-600'>Subcommittees</p>
              </div>
              <div className='p-4 bg-gray-50 rounded-lg'>
                <p className='text-2xl font-bold text-gray-900'>
                  {committeeInfo.chamber || 'N/A'}
                </p>
                <p className='text-sm text-gray-600'>Chamber</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CommitteeLeadership;
