import {
  ArrowLeft,
  User,
  MapPin,
  Phone,
  Mail,
  Globe,
  Calendar,
  Building2,
  FileText,
  Vote,
  TrendingUp,
  Award,
  Users,
  ExternalLink,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';

import DataService from '../services/dataService';

function MemberDetail() {
  const { memberId } = useParams();
  const navigate = useNavigate();
  const [member, setMember] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadMemberData();
  }, [memberId]);

  const loadMemberData = async () => {
    try {
      setLoading(true);
      setError(null);

      // First try to load from members summary to get basic info
      const membersSummary = await DataService.loadMembersSummary();
      const basicMember = membersSummary?.members?.find(
        m => m.bioguideId === memberId
      );

      if (!basicMember) {
        setError('Member not found');
        setLoading(false);
        return;
      }

      // Try to load detailed member data if it exists
      try {
        const detailedMember = await DataService.loadMemberDetails(memberId);
        if (detailedMember) {
          setMember({ ...basicMember, ...detailedMember });
        } else {
          setMember(basicMember);
        }
      } catch {
        // If detailed data doesn't exist, use basic data
        setMember(basicMember);
      }

      setLoading(false);
    } catch (err) {
      console.error('Error loading member:', err);
      setError('Failed to load member data');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600' />
      </div>
    );
  }

  if (error || !member) {
    return (
      <div className='bg-red-50 border border-red-200 rounded-lg p-6'>
        <h3 className='text-lg font-semibold text-red-800 mb-2'>
          Error Loading Member
        </h3>
        <p className='text-red-700'>{error || 'Member not found'}</p>
        <button
          onClick={() => navigate('/members')}
          className='mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700'
        >
          Back to Members List
        </button>
      </div>
    );
  }

  const isHouse = member.district !== null && member.district !== undefined;
  const chamber = isHouse ? 'House' : 'Senate';
  const title = isHouse ? 'Representative' : 'Senator';

  const partyColor =
    member.party === 'Republican'
      ? 'bg-republican'
      : member.party === 'Democratic'
        ? 'bg-democrat'
        : 'bg-independent';

  return (
    <div className='space-y-6'>
      {/* Breadcrumb */}
      <div className='flex items-center gap-2 text-sm text-gray-600'>
        <Link to='/members' className='hover:text-blue-600'>
          Members
        </Link>
        <span>/</span>
        <span className='text-gray-900'>{member.name}</span>
      </div>

      {/* Header */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
        <div className='p-6'>
          <button
            onClick={() => navigate('/members')}
            className='flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-4'
          >
            <ArrowLeft size={20} />
            <span>Back to Members</span>
          </button>

          <div className='flex items-start gap-6'>
            <div className='w-32 h-32 bg-gray-200 rounded-lg flex items-center justify-center'>
              <User size={48} className='text-gray-400' />
            </div>

            <div className='flex-1'>
              <div className='flex items-start justify-between'>
                <div>
                  <h1 className='text-3xl font-bold text-gray-900'>
                    {member.name}
                  </h1>
                  <div className='flex items-center gap-3 mt-2'>
                    <span
                      className={`${partyColor} text-white px-3 py-1 rounded font-medium`}
                    >
                      {member.party}
                    </span>
                    <span className='text-gray-600 text-lg'>
                      {title} from {member.state}
                      {isHouse && `, District ${member.district}`}
                    </span>
                  </div>
                </div>

                <div className='text-right'>
                  <p className='text-sm text-gray-500'>Bioguide ID</p>
                  <p className='font-mono text-sm font-semibold'>
                    {member.bioguideId}
                  </p>
                </div>
              </div>

              <div className='grid grid-cols-2 md:grid-cols-4 gap-4 mt-6'>
                <div className='flex items-center gap-2'>
                  <Building2 size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>Chamber</p>
                    <p className='text-sm font-medium'>{chamber}</p>
                  </div>
                </div>
                <div className='flex items-center gap-2'>
                  <MapPin size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>State</p>
                    <p className='text-sm font-medium'>{member.state}</p>
                  </div>
                </div>
                {isHouse && (
                  <div className='flex items-center gap-2'>
                    <Users size={16} className='text-gray-400' />
                    <div>
                      <p className='text-xs text-gray-500'>District</p>
                      <p className='text-sm font-medium'>{member.district}</p>
                    </div>
                  </div>
                )}
                {member.terms?.length > 0 && (
                  <div className='flex items-center gap-2'>
                    <Calendar size={16} className='text-gray-400' />
                    <div>
                      <p className='text-xs text-gray-500'>First Elected</p>
                      <p className='text-sm font-medium'>
                        {member.terms[0].startYear}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Contact Information */}
        {(member.addressInformation || member.directOrderName) && (
          <div className='border-t border-gray-200 px-6 py-4'>
            <h2 className='text-lg font-semibold text-gray-900 mb-3'>
              Contact Information
            </h2>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              {member.addressInformation?.phoneNumber && (
                <div className='flex items-center gap-2 text-sm'>
                  <Phone size={16} className='text-gray-400' />
                  <span>{member.addressInformation.phoneNumber}</span>
                </div>
              )}
              {member.officialWebsiteUrl && (
                <div className='flex items-center gap-2 text-sm'>
                  <Globe size={16} className='text-gray-400' />
                  <a
                    href={member.officialWebsiteUrl}
                    target='_blank'
                    rel='noopener noreferrer'
                    className='text-blue-600 hover:underline'
                  >
                    Official Website
                  </a>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legislative Activity */}
      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
        {/* Sponsored Bills */}
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <h2 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
            <FileText size={20} />
            Sponsored Bills
          </h2>
          {member.sponsoredLegislation?.length > 0 ? (
            <div className='space-y-3'>
              {member.sponsoredLegislation.slice(0, 5).map((bill, index) => (
                <div key={index} className='border-l-2 border-blue-500 pl-3'>
                  <p className='text-sm font-medium text-gray-900'>
                    {bill.number || bill.title?.substring(0, 50)}
                  </p>
                  <p className='text-xs text-gray-600 line-clamp-2'>
                    {bill.title}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className='text-sm text-gray-500'>
              No sponsored bills data available
            </p>
          )}
        </div>

        {/* Committee Assignments */}
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <h2 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
            <Award size={20} />
            Committee Assignments
          </h2>
          {member.committees?.length > 0 ? (
            <div className='space-y-2'>
              {member.committees.map((committee, index) => (
                <div
                  key={index}
                  className='px-3 py-2 bg-gray-50 rounded text-sm'
                >
                  {committee.name || committee}
                </div>
              ))}
            </div>
          ) : (
            <p className='text-sm text-gray-500'>No committee data available</p>
          )}
        </div>
      </div>

      {/* Voting Record */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <h2 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
          <Vote size={20} />
          Voting Record
        </h2>
        {member.votingRecord ? (
          <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
            <div className='text-center'>
              <p className='text-2xl font-bold text-blue-600'>
                {member.votingRecord.partyUnityScore || '-'}%
              </p>
              <p className='text-xs text-gray-600'>Party Unity</p>
            </div>
            <div className='text-center'>
              <p className='text-2xl font-bold text-green-600'>
                {member.votingRecord.totalVotes || '-'}
              </p>
              <p className='text-xs text-gray-600'>Total Votes</p>
            </div>
            <div className='text-center'>
              <p className='text-2xl font-bold text-purple-600'>
                {member.votingRecord.missedVotes || '-'}
              </p>
              <p className='text-xs text-gray-600'>Missed Votes</p>
            </div>
            <div className='text-center'>
              <p className='text-2xl font-bold text-orange-600'>
                {member.votingRecord.attendanceRate || '-'}%
              </p>
              <p className='text-xs text-gray-600'>Attendance</p>
            </div>
          </div>
        ) : (
          <div className='bg-yellow-50 border border-yellow-200 p-4 rounded-lg'>
            <p className='text-yellow-800 text-sm'>
              Detailed voting records are not available for this member yet.
              Check back later as we continue to process congressional data.
            </p>
          </div>
        )}
      </div>

      {/* Additional Actions */}
      <div className='flex gap-3'>
        <button
          onClick={() =>
            window.open(
              `https://www.congress.gov/member/${member.name.replace(/ /g, '-').toLowerCase()}/${member.bioguideId}`,
              '_blank'
            )
          }
          className='px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2'
        >
          <ExternalLink size={16} />
          View on Congress.gov
        </button>
        <Link
          to='/bills'
          className='px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 flex items-center gap-2'
        >
          <FileText size={16} />
          View All Bills
        </Link>
      </div>
    </div>
  );
}

export default MemberDetail;
