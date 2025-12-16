import { Building2, Users, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

function CommitteeCard({ committee }) {
  if (!committee) {
    return null;
  }

  // Determine chamber badge colors
  const getChamberBadge = chamber => {
    switch (chamber?.toLowerCase()) {
      case 'house':
        return {
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          border: 'border-blue-200',
        };
      case 'senate':
        return {
          bg: 'bg-red-100',
          text: 'text-red-800',
          border: 'border-red-200',
        };
      case 'joint':
        return {
          bg: 'bg-purple-100',
          text: 'text-purple-800',
          border: 'border-purple-200',
        };
      default:
        return {
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200',
        };
    }
  };

  const chamberStyles = getChamberBadge(committee.chamber);
  const committeeName = committee.name || 'Unknown Committee';
  const committeeCode = committee.code || 'N/A';
  const subcommitteeCount = committee.subcommittee_count || 0;
  const committeeId = committee.code || committee.id || 'unknown';

  return (
    <Link
      to={`/committees/${committeeId}`}
      className='block bg-white p-6 rounded-lg border border-gray-200 hover:shadow-lg hover:border-gray-300 transition-all duration-200'
    >
      <div className='space-y-4'>
        {/* Header with committee icon and chamber badge */}
        <div className='flex items-start justify-between'>
          <div className='flex items-center space-x-3'>
            <div className='p-2 bg-gray-100 rounded-lg'>
              <Building2 className='h-5 w-5 text-gray-600' />
            </div>
            <div className='flex-1'>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${chamberStyles.bg} ${chamberStyles.text} ${chamberStyles.border}`}
              >
                {committee.chamber || 'Unknown'}
              </span>
            </div>
          </div>
        </div>

        {/* Committee Name */}
        <div>
          <h3 className='text-lg font-semibold text-gray-900 line-clamp-2 mb-2'>
            {committeeName}
          </h3>
          <p className='text-sm text-gray-600 font-mono'>{committeeCode}</p>
        </div>

        {/* Subcommittee Count */}
        <div className='flex items-center justify-between pt-2'>
          <div className='flex items-center space-x-2 text-sm text-gray-600'>
            <Users className='h-4 w-4' />
            <span>
              {subcommitteeCount}{' '}
              {subcommitteeCount === 1 ? 'Subcommittee' : 'Subcommittees'}
            </span>
          </div>

          {/* View Details Link */}
          <div className='flex items-center space-x-1 text-sm text-blue-600 font-medium'>
            <span>View Details</span>
            <ChevronRight className='h-4 w-4' />
          </div>
        </div>
      </div>
    </Link>
  );
}

export default CommitteeCard;
