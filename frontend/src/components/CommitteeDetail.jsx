import {
  ArrowLeft,
  Building2,
  Users,
  Calendar,
  FileText,
  ExternalLink,
  Clock,
  Star,
  ChevronRight,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';

import OptimizedDataService from '../services/optimizedDataService';

import BillProgressBar from './BillProgressBar';
import CommitteeTimeline from './CommitteeTimeline';
import MemberRoster from './MemberRoster';

function CommitteeDetail() {
  const { committeeId } = useParams();
  const navigate = useNavigate();

  const [committee, setCommittee] = useState(null);
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
    loadCommitteeData();
  }, [committeeId]);

  const loadCommitteeData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load all data in parallel using optimized service
      const result = await OptimizedDataService.loadCommitteeDataOptimized(committeeId);

      if (!result.committee) {
        setError('Committee not found');
        setLoading(false);
        return;
      }

      // Normalize committee data for consistent rendering
      const normalizedData = {
        ...result.committee,
        code: result.committee.systemCode || result.committee.code || committeeId,
        chamber:
          result.committee.chamber || result.committee.chamber_name || 'Unknown',
        leadership: result.committee.leadership || [],
        subcommittees: result.committee.subcommittees || [],
        description: result.committee.description || null,
      };

      setCommittee(normalizedData);
      setLoading(false);

      // Process parallel loaded data
      if (result.members) {
        processMembers(result.members);
      } else {
        loadMembersData(); // Fallback
      }

      if (result.bills) {
        processBills(result.bills);
      } else {
        loadBillsData(); // Fallback
      }

      if (result.timeline) {
        setTimeline(result.timeline.activities || []);
        setTimelineLoading(false);
      } else {
        loadTimelineData(); // Fallback
      }
    } catch (err) {
      console.error('Error loading committee:', err);
      setError('Failed to load committee data');
      setLoading(false);
    }
  };

  const processMembers = (membersData) => {
    let membersList = [];
    if (membersData?.members && Array.isArray(membersData.members)) {
      membersList = membersData.members;
    } else if (Array.isArray(membersData)) {
      membersList = membersData;
    }

    const normalizedMembers = membersList.map(member => ({
      ...member,
      bioguideId: member.bioguideId || member.bioguide_id || member.member_id,
      name: member.name || member.fullName || 'Unknown Member',
      party: member.party || 'Unknown',
      state: member.state || 'N/A',
      role: member.role || 'Member',
      photo_url: member.photo_url || member.imageUrl || member.image_url,
    }));

    setMembers(normalizedMembers);
    setMembersLoading(false);
  };

  const processBills = (billsData) => {
    let billsList = [];
    if (billsData?.bills && Array.isArray(billsData.bills)) {
      billsList = billsData.bills;
    } else if (Array.isArray(billsData)) {
      billsList = billsData;
    }

    const normalizedBills = billsList.map(bill => ({
      ...bill,
      id: bill.id || bill.bill_id || `${bill.type}_${bill.number}`,
      title: bill.title || 'No title available',
      type: bill.type || 'UNKNOWN',
      number: bill.number || 'N/A',
      updateDate: bill.updateDate || bill.introducedDate,
    }));

    setBills(normalizedBills);
    setBillsLoading(false);
  };

  const loadMembersData = async () => {
    try {
      setMembersLoading(true);
      const membersData = await OptimizedDataService.loadCommitteeMembers(committeeId);

      // Handle different response formats
      let membersList = [];
      if (membersData?.members && Array.isArray(membersData.members)) {
        membersList = membersData.members;
      } else if (Array.isArray(membersData)) {
        membersList = membersData;
      }

      // Normalize member data for consistent rendering
      const normalizedMembers = membersList.map(member => ({
        ...member,
        bioguideId: member.bioguideId || member.bioguide_id || member.member_id,
        name: member.name || member.fullName || 'Unknown Member',
        party: member.party || 'Unknown',
        state: member.state || 'N/A',
        role: member.role || 'Member',
        photo_url: member.photo_url || member.imageUrl || member.image_url,
      }));

      setMembers(normalizedMembers);
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
      const billsData = await OptimizedDataService.loadCommitteeBills(committeeId);

      // Handle different response formats
      let billsList = [];
      if (billsData?.bills && Array.isArray(billsData.bills)) {
        billsList = billsData.bills;
      } else if (Array.isArray(billsData)) {
        billsList = billsData;
      }

      // Normalize bill data for consistent rendering
      const normalizedBills = billsList.map(bill => ({
        ...bill,
        id: bill.id || bill.bill_id || `${bill.type}_${bill.number}`,
        title: bill.title || 'No title available',
        type: bill.type || 'UNKNOWN',
        number: bill.number || 'N/A',
        updateDate: bill.updateDate || bill.introducedDate,
      }));

      setBills(normalizedBills);
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
      const timelineData = await OptimizedDataService.loadCommitteeTimeline(committeeId);
      setTimeline(timelineData?.activities || []);
    } catch (err) {
      console.error('Error loading timeline:', err);
      setTimeline([]);
    } finally {
      setTimelineLoading(false);
    }
  };

  const getChamberBadge = chamber => {
    const chamberNormalized = chamber?.toLowerCase().trim();
    switch (chamberNormalized) {
      case 'house':
        return {
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          border: 'border-blue-200',
          label: 'House',
        };
      case 'senate':
        return {
          bg: 'bg-red-100',
          text: 'text-red-800',
          border: 'border-red-200',
          label: 'Senate',
        };
      case 'joint':
        return {
          bg: 'bg-purple-100',
          text: 'text-purple-800',
          border: 'border-purple-200',
          label: 'Joint',
        };
      default:
        return {
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200',
          label: chamber || 'Unknown',
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

  if (error || !committee) {
    return (
      <div className='bg-red-50 border border-red-200 rounded-lg p-6'>
        <h3 className='text-lg font-semibold text-red-800 mb-2'>
          Error Loading Committee
        </h3>
        <p className='text-red-700'>{error || 'Committee not found'}</p>
        <div className='flex gap-3 mt-4'>
          <button
            onClick={() => navigate('/committees')}
            className='px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700'
          >
            Back to Committees
          </button>
          <button
            onClick={loadCommitteeData}
            className='px-4 py-2 border border-red-300 text-red-700 rounded hover:bg-red-50'
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const chamberStyles = getChamberBadge(committee.chamber);

  return (
    <div className='space-y-6'>
      {/* Breadcrumb */}
      <div className='flex items-center gap-2 text-sm text-gray-600'>
        <Link to='/committees' className='hover:text-blue-600'>
          Committees
        </Link>
        <span>/</span>
        <span className='text-gray-900'>{committee.name}</span>
      </div>

      {/* Header */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
        <div className='p-6'>
          <button
            onClick={() => navigate('/committees')}
            className='flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-4'
          >
            <ArrowLeft size={20} />
            <span>Back to Committees</span>
          </button>

          <div className='flex items-start justify-between'>
            <div className='flex-1'>
              <div className='flex items-center gap-4 mb-3'>
                <div className='p-3 bg-gray-100 rounded-lg'>
                  <Building2 className='h-6 w-6 text-gray-600' />
                </div>
                <div>
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${chamberStyles.bg} ${chamberStyles.text} ${chamberStyles.border}`}
                  >
                    {chamberStyles.label}
                  </span>
                </div>
              </div>

              <h1 className='text-3xl font-bold text-gray-900 mb-2'>
                {committee.name || 'Unknown Committee'}
              </h1>

              <div className='grid grid-cols-2 md:grid-cols-4 gap-4 mt-6'>
                <div className='flex items-center gap-2'>
                  <FileText size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>Committee Code</p>
                    <p className='text-sm font-medium font-mono'>
                      {committee.code || 'N/A'}
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
                  <Building2 size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>Subcommittees</p>
                    <p className='text-sm font-medium'>
                      {committee.subcommittee_count ||
                        committee.subcommittees?.length ||
                        0}
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
              </div>
            </div>
          </div>
        </div>

        {/* Committee Description */}
        {committee.description && (
          <div className='border-t border-gray-200 px-6 py-4'>
            <h3 className='text-lg font-semibold text-gray-900 mb-3'>
              About This Committee
            </h3>
            <p className='text-gray-700'>{committee.description}</p>
          </div>
        )}

        {/* Leadership */}
        {committee.leadership && committee.leadership.length > 0 && (
          <div className='border-t border-gray-200 px-6 py-4'>
            <h3 className='text-lg font-semibold text-gray-900 mb-3'>
              Committee Leadership
            </h3>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              {committee.leadership.map((leader, index) => (
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

      {/* Subcommittees */}
      {committee.subcommittees && committee.subcommittees.length > 0 && (
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
            <Building2 size={20} />
            Subcommittees ({committee.subcommittees.length})
          </h3>
          <div className='grid gap-3'>
            {committee.subcommittees.map((subcommittee, index) => (
              <Link
                key={index}
                to={`/subcommittees/${subcommittee.id || subcommittee.code}`}
                className='flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-all'
              >
                <div className='flex items-center gap-3'>
                  <Building2 size={16} className='text-gray-400' />
                  <div>
                    <h4 className='font-medium text-gray-900'>
                      {subcommittee.name}
                    </h4>
                    {subcommittee.code && (
                      <p className='text-sm text-gray-500 font-mono'>
                        {subcommittee.code}
                      </p>
                    )}
                  </div>
                </div>
                <ChevronRight size={16} className='text-gray-400' />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Committee Members */}
      <MemberRoster
        members={members}
        loading={membersLoading}
        title='Committee Members'
      />

      {/* Recent Bills */}
      {bills.length > 0 && (
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
            <FileText size={20} />
            Recent Bills ({bills.length})
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
                  to={`/bills?committee=${committeeId}`}
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

      {/* Committee Timeline */}
      <CommitteeTimeline activities={timeline} loading={timelineLoading} />

      {/* External Links */}
      <div className='flex gap-3'>
        <button
          onClick={() => {
            const chamberLower = committee.chamber?.toLowerCase();
            const baseUrl =
              chamberLower === 'house'
                ? 'https://www.house.gov/committees'
                : chamberLower === 'senate'
                  ? 'https://www.senate.gov/committees'
                  : 'https://www.congress.gov/committees';
            window.open(baseUrl, '_blank');
          }}
          className='px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2'
        >
          <ExternalLink size={16} />
          View on {chamberStyles.label} Website
        </button>
        <Link
          to='/committees'
          className='px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 flex items-center gap-2'
        >
          <Building2 size={16} />
          Back to All Committees
        </Link>
      </div>
    </div>
  );
}

export default CommitteeDetail;
