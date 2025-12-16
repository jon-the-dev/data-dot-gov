import {
  ArrowLeft,
  Building2,
  Users,
  Calendar,
  FileText,
  ExternalLink,
  Clock,
  AlertCircle,
  Star,
  ChevronRight,
  Link as LinkIcon,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';

import DataService from '../services/dataService';

import BillProgressBar from './BillProgressBar';
import CommitteeTimeline from './CommitteeTimeline';
import MemberRoster from './MemberRoster';

function SubcommitteeDetail() {
  const { subcommitteeId } = useParams();
  const navigate = useNavigate();

  const [subcommittee, setSubcommittee] = useState(null);
  const [parentCommittee, setParentCommittee] = useState(null);
  const [members, setMembers] = useState([]);
  const [bills, setBills] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Loading states for different sections
  const [membersLoading, setMembersLoading] = useState(true);
  const [billsLoading, setBillsLoading] = useState(true);
  const [timelineLoading, setTimelineLoading] = useState(true);

  useEffect(() => {
    loadSubcommitteeData();
  }, [subcommitteeId]);

  const loadSubcommitteeData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load basic subcommittee details
      const subcommitteeData =
        await DataService.loadSubcommitteeDetails(subcommitteeId);
      if (!subcommitteeData) {
        setError('Subcommittee not found');
        setLoading(false);
        return;
      }

      setSubcommittee(subcommitteeData);

      // Load parent committee if available
      if (
        subcommitteeData.parent_committee_id ||
        subcommitteeData.parentCommittee
      ) {
        try {
          const parentId =
            subcommitteeData.parent_committee_id ||
            subcommitteeData.parentCommittee.id;
          const parentData = await DataService.loadCommitteeDetails(parentId);
          setParentCommittee(parentData);
        } catch (err) {
          console.warn('Could not load parent committee:', err);
        }
      }

      setLoading(false);

      // Load additional data in parallel
      loadMembersData();
      loadBillsData();
      loadTimelineData();
    } catch (err) {
      console.error('Error loading subcommittee:', err);
      setError('Failed to load subcommittee data');
      setLoading(false);
    }
  };

  const loadMembersData = async () => {
    try {
      setMembersLoading(true);
      // Try to get subcommittee members, fallback to empty array
      const membersData =
        await DataService.loadCommitteeMembers(subcommitteeId);
      setMembers(membersData?.members || subcommittee?.members || []);
    } catch (err) {
      console.error('Error loading members:', err);
      setMembers([]);
    } finally {
      setMembersLoading(false);
    }
  };

  const loadBillsData = async () => {
    try {
      setBillsLoading(true);
      // Try to get subcommittee bills
      const billsData = await DataService.loadCommitteeBills(subcommitteeId);
      setBills(billsData?.bills || []);
    } catch (err) {
      console.error('Error loading bills:', err);
      setBills([]);
    } finally {
      setBillsLoading(false);
    }
  };

  const loadTimelineData = async () => {
    try {
      setTimelineLoading(true);
      // Try to get subcommittee timeline
      const timelineData =
        await DataService.loadCommitteeTimeline(subcommitteeId);
      setTimeline(timelineData?.activities || []);
    } catch (err) {
      console.error('Error loading timeline:', err);
      setTimeline([]);
    } finally {
      setTimelineLoading(false);
    }
  };

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

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600' />
      </div>
    );
  }

  if (error || !subcommittee) {
    return (
      <div className='bg-red-50 border border-red-200 rounded-lg p-6'>
        <h3 className='text-lg font-semibold text-red-800 mb-2'>
          Error Loading Subcommittee
        </h3>
        <p className='text-red-700'>{error || 'Subcommittee not found'}</p>
        <div className='flex gap-3 mt-4'>
          <button
            onClick={() => navigate('/committees')}
            className='px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700'
          >
            Back to Committees
          </button>
          <button
            onClick={loadSubcommitteeData}
            className='px-4 py-2 border border-red-300 text-red-700 rounded hover:bg-red-50'
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const chamber = subcommittee.chamber || parentCommittee?.chamber;
  const chamberStyles = getChamberBadge(chamber);

  return (
    <div className='space-y-6'>
      {/* Breadcrumb */}
      <div className='flex items-center gap-2 text-sm text-gray-600'>
        <Link to='/committees' className='hover:text-blue-600'>
          Committees
        </Link>
        <span>/</span>
        {parentCommittee && (
          <>
            <Link
              to={`/committees/${parentCommittee.id || parentCommittee.code}`}
              className='hover:text-blue-600'
            >
              {parentCommittee.name}
            </Link>
            <span>/</span>
          </>
        )}
        <span className='text-gray-900'>{subcommittee.name}</span>
      </div>

      {/* Header */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
        <div className='p-6'>
          <button
            onClick={() => {
              if (parentCommittee) {
                navigate(
                  `/committees/${parentCommittee.id || parentCommittee.code}`
                );
              } else {
                navigate('/committees');
              }
            }}
            className='flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-4'
          >
            <ArrowLeft size={20} />
            <span>
              {parentCommittee
                ? `Back to ${parentCommittee.name}`
                : 'Back to Committees'}
            </span>
          </button>

          <div className='flex items-start justify-between'>
            <div className='flex-1'>
              <div className='flex items-center gap-4 mb-3'>
                <div className='p-3 bg-gray-100 rounded-lg'>
                  <Building2 className='h-6 w-6 text-gray-600' />
                </div>
                <div className='flex items-center gap-2'>
                  <span className='text-sm text-gray-500'>Subcommittee</span>
                  {chamber && (
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${chamberStyles.bg} ${chamberStyles.text} ${chamberStyles.border}`}
                    >
                      {chamber}
                    </span>
                  )}
                </div>
              </div>

              <h1 className='text-3xl font-bold text-gray-900 mb-2'>
                {subcommittee.name || 'Unknown Subcommittee'}
              </h1>

              {/* Parent Committee Link */}
              {parentCommittee && (
                <div className='mb-4'>
                  <p className='text-sm text-gray-600 mb-2'>Part of:</p>
                  <Link
                    to={`/committees/${parentCommittee.id || parentCommittee.code}`}
                    className='inline-flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 hover:bg-blue-100 hover:border-blue-300 transition-colors'
                  >
                    <Building2 size={16} />
                    <span className='font-medium'>{parentCommittee.name}</span>
                    <ChevronRight size={14} />
                  </Link>
                </div>
              )}

              <div className='grid grid-cols-2 md:grid-cols-4 gap-4 mt-6'>
                <div className='flex items-center gap-2'>
                  <FileText size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>Subcommittee Code</p>
                    <p className='text-sm font-medium font-mono'>
                      {subcommittee.code || 'N/A'}
                    </p>
                  </div>
                </div>
                <div className='flex items-center gap-2'>
                  <Users size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>Members</p>
                    <p className='text-sm font-medium'>
                      {members.length} {membersLoading ? '(Loading...)' : ''}
                    </p>
                  </div>
                </div>
                <div className='flex items-center gap-2'>
                  <FileText size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>Active Bills</p>
                    <p className='text-sm font-medium'>
                      {bills.length} {billsLoading ? '(Loading...)' : ''}
                    </p>
                  </div>
                </div>
                <div className='flex items-center gap-2'>
                  <Calendar size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>Recent Activity</p>
                    <p className='text-sm font-medium'>
                      {timeline.length}{' '}
                      {timelineLoading ? '(Loading...)' : 'events'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Subcommittee Description */}
        {subcommittee.description && (
          <div className='border-t border-gray-200 px-6 py-4'>
            <h3 className='text-lg font-semibold text-gray-900 mb-3'>
              About This Subcommittee
            </h3>
            <p className='text-gray-700'>{subcommittee.description}</p>
          </div>
        )}

        {/* Leadership */}
        {subcommittee.leadership && subcommittee.leadership.length > 0 && (
          <div className='border-t border-gray-200 px-6 py-4'>
            <h3 className='text-lg font-semibold text-gray-900 mb-3'>
              Subcommittee Leadership
            </h3>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              {subcommittee.leadership.map((leader, index) => (
                <div
                  key={index}
                  className='flex items-center gap-3 p-3 bg-gray-50 rounded-lg'
                >
                  <Star size={16} className='text-yellow-500' />
                  <div>
                    <Link
                      to={`/members/${leader.bioguideId || leader.member_id}`}
                      className='font-medium text-blue-600 hover:text-blue-800'
                    >
                      {leader.name}
                    </Link>
                    <p className='text-sm text-gray-600'>
                      {leader.role} • {leader.party} - {leader.state}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Subcommittee Members */}
      <MemberRoster
        members={members}
        loading={membersLoading}
        title='Subcommittee Members'
      />

      {/* Recent Bills */}
      {bills.length > 0 && (
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
            <FileText size={20} />
            Bills in Subcommittee ({bills.length})
          </h3>
          <div className='space-y-4'>
            {bills.slice(0, 10).map((bill, index) => (
              <div
                key={index}
                className='border border-gray-200 rounded-lg p-4'
              >
                <div className='flex items-start justify-between'>
                  <div className='flex-1'>
                    <Link
                      to={`/bills/${bill.id || bill.bill_id}`}
                      className='text-lg font-medium text-blue-600 hover:text-blue-800 hover:underline'
                    >
                      {bill.type} {bill.bill_id}
                    </Link>
                    <h4 className='text-gray-900 mt-1 line-clamp-2'>
                      {bill.title || 'No title available'}
                    </h4>
                    <div className='flex items-center gap-4 text-sm text-gray-500 mt-2'>
                      {bill.updateDate && (
                        <div className='flex items-center gap-1'>
                          <Calendar size={12} />
                          <span>{DataService.formatDate(bill.updateDate)}</span>
                        </div>
                      )}
                      {bill.latestAction && (
                        <div className='flex items-center gap-1'>
                          <Clock size={12} />
                          <span>
                            {bill.latestAction.text?.substring(0, 50)}...
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Bill Progress */}
                <div className='mt-3'>
                  <BillProgressBar bill={bill} compact={true} />
                </div>
              </div>
            ))}
            {bills.length > 10 && (
              <div className='text-center pt-4'>
                <Link
                  to={`/bills?subcommittee=${subcommitteeId}`}
                  className='inline-flex items-center gap-2 px-4 py-2 text-blue-600 hover:text-blue-800'
                >
                  View all {bills.length} bills
                  <ChevronRight size={16} />
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Subcommittee Timeline */}
      <CommitteeTimeline activities={timeline} loading={timelineLoading} />

      {/* External Links and Navigation */}
      <div className='flex gap-3'>
        <button
          onClick={() => {
            const baseUrl =
              chamber === 'House'
                ? 'https://www.house.gov/committees'
                : 'https://www.senate.gov/committees';
            window.open(baseUrl, '_blank');
          }}
          className='px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2'
        >
          <ExternalLink size={16} />
          View on {chamber} Website
        </button>

        {parentCommittee && (
          <Link
            to={`/committees/${parentCommittee.id || parentCommittee.code}`}
            className='px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 flex items-center gap-2'
          >
            <Building2 size={16} />
            Parent Committee
          </Link>
        )}

        <Link
          to='/committees'
          className='px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 flex items-center gap-2'
        >
          <Building2 size={16} />
          All Committees
        </Link>
      </div>
    </div>
  );
}

export default SubcommitteeDetail;
