import {
  Vote,
  Calendar,
  ArrowLeft,
  ExternalLink,
  CheckCircle,
  XCircle,
  MinusCircle,
  Clock,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

import DataService from '@/services/dataService';
import type { Vote as VoteType } from '@/types';

export default function VoteBreakdown() {
  const { voteId } = useParams<{ voteId: string }>();
  const [vote, setVote] = useState<VoteType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'overview' | 'members'>('overview');
  const [filterParty, setFilterParty] = useState<string>('all');
  const [filterPosition, setFilterPosition] = useState<string>('all');

  useEffect(() => {
    if (voteId) {
      loadVoteData(voteId);
    }
  }, [voteId]);

  const loadVoteData = async (id: string) => {
    try {
      setLoading(true);
      setError(null);

      const voteDetails = await DataService.loadVoteDetails(id);
      if (!voteDetails) {
        throw new Error('Vote not found');
      }

      setVote(voteDetails);
    } catch (err) {
      console.error('Error loading vote data:', err);
      setError('Failed to load vote details');
    } finally {
      setLoading(false);
    }
  };

  const getResultColor = (result: string) => {
    const resultColors = {
      Passed: 'text-green-600',
      Failed: 'text-red-600',
      'Agreed to': 'text-green-600',
      Rejected: 'text-red-600',
      Adopted: 'text-green-600',
      'Not Adopted': 'text-red-600',
    };
    return resultColors[result as keyof typeof resultColors] || 'text-gray-600';
  };

  const getPositionIcon = (position: string) => {
    switch (position) {
      case 'Yea':
        return <CheckCircle className='h-4 w-4 text-green-600' />;
      case 'Nay':
        return <XCircle className='h-4 w-4 text-red-600' />;
      case 'Present':
        return <MinusCircle className='h-4 w-4 text-yellow-600' />;
      case 'Not Voting':
        return <Clock className='h-4 w-4 text-gray-400' />;
      default:
        return <MinusCircle className='h-4 w-4 text-gray-400' />;
    }
  };

  const getPositionColor = (position: string) => {
    switch (position) {
      case 'Yea':
        return 'bg-green-100 text-green-800';
      case 'Nay':
        return 'bg-red-100 text-red-800';
      case 'Present':
        return 'bg-yellow-100 text-yellow-800';
      case 'Not Voting':
        return 'bg-gray-100 text-gray-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const prepareOverallData = () => {
    if (!vote) return [];

    return [
      { name: 'Yea', value: vote.total_votes.yea, color: '#10B981' },
      { name: 'Nay', value: vote.total_votes.nay, color: '#EF4444' },
      { name: 'Present', value: vote.total_votes.present, color: '#F59E0B' },
      {
        name: 'Not Voting',
        value: vote.total_votes.not_voting,
        color: '#6B7280',
      },
    ].filter(item => item.value > 0);
  };

  const preparePartyData = () => {
    if (!vote?.party_breakdown) return [];

    return Object.entries(vote.party_breakdown).map(([party, breakdown]) => ({
      party: DataService.getPartyLabel(party),
      Yea: breakdown.yea,
      Nay: breakdown.nay,
      Present: breakdown.present,
      'Not Voting': breakdown.not_voting,
      color: DataService.getPartyColor(party),
    }));
  };

  const getFilteredMembers = () => {
    if (!vote?.member_votes) return [];

    let filtered = vote.member_votes;

    if (filterParty !== 'all') {
      filtered = filtered.filter(
        member => DataService.normalizeParty(member.party) === filterParty
      );
    }

    if (filterPosition !== 'all') {
      filtered = filtered.filter(member => member.position === filterPosition);
    }

    return filtered.sort((a, b) => a.name.localeCompare(b.name));
  };

  const calculatePartyUnity = () => {
    if (!vote?.party_breakdown) return {};

    const unity: { [party: string]: number } = {};

    Object.entries(vote.party_breakdown).forEach(([party, breakdown]) => {
      const total =
        breakdown.yea +
        breakdown.nay +
        breakdown.present +
        breakdown.not_voting;
      if (total > 0) {
        const majorityPosition = Math.max(breakdown.yea, breakdown.nay);
        unity[party] = (majorityPosition / total) * 100;
      }
    });

    return unity;
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600' />
      </div>
    );
  }

  if (error || !vote) {
    return (
      <div className='bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg'>
        {error || 'Vote not found'}
      </div>
    );
  }

  const partyUnity = calculatePartyUnity();

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center gap-4 mb-6'>
        <Link
          to='/votes'
          className='flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors'
        >
          <ArrowLeft size={20} />
          Back to Votes
        </Link>
      </div>

      {/* Vote Header */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4'>
          <div className='flex-1'>
            <div className='flex items-center gap-3 mb-2'>
              <Vote className='h-6 w-6 text-blue-600' />
              <h1 className='text-2xl font-bold text-gray-900'>
                Roll Call #{vote.roll_call}
              </h1>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${getResultColor(vote.result)}`}
              >
                {vote.result}
              </span>
            </div>
            <h2 className='text-lg text-gray-700 mb-3'>{vote.question}</h2>
            {vote.description && (
              <p className='text-gray-600 mb-4'>{vote.description}</p>
            )}
            <div className='flex flex-wrap gap-4 text-sm text-gray-600'>
              <span className='flex items-center gap-1'>
                <Calendar size={16} />
                {DataService.formatDate(vote.vote_date)}
              </span>
              <span className='capitalize'>
                {vote.chamber} • Session {vote.session} • {vote.congress}th
                Congress
              </span>
            </div>
          </div>
          <div className='flex gap-2'>
            <a
              href={`https://clerk.house.gov/evs/${new Date(vote.vote_date).getFullYear()}/roll${vote.roll_call.toString().padStart(3, '0')}.xml`}
              target='_blank'
              rel='noopener noreferrer'
              className='flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors'
            >
              <ExternalLink size={16} />
              House Clerk
            </a>
          </div>
        </div>
      </div>

      {/* View Mode Toggle */}
      <div className='flex bg-gray-100 rounded-lg p-1 w-fit'>
        <button
          onClick={() => setViewMode('overview')}
          className={`px-4 py-2 text-sm rounded transition-colors ${
            viewMode === 'overview'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setViewMode('members')}
          className={`px-4 py-2 text-sm rounded transition-colors ${
            viewMode === 'members'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Member Votes ({vote.member_votes?.length || 0})
        </button>
      </div>

      {viewMode === 'overview' ? (
        <>
          {/* Vote Summary Stats */}
          <div className='grid grid-cols-2 lg:grid-cols-4 gap-4'>
            <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm font-medium text-gray-600'>Yea Votes</p>
                  <p className='text-2xl font-bold text-green-600 mt-1'>
                    {vote.total_votes.yea}
                  </p>
                </div>
                <CheckCircle className='h-8 w-8 text-green-600' />
              </div>
            </div>

            <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm font-medium text-gray-600'>Nay Votes</p>
                  <p className='text-2xl font-bold text-red-600 mt-1'>
                    {vote.total_votes.nay}
                  </p>
                </div>
                <XCircle className='h-8 w-8 text-red-600' />
              </div>
            </div>

            <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm font-medium text-gray-600'>Present</p>
                  <p className='text-2xl font-bold text-yellow-600 mt-1'>
                    {vote.total_votes.present}
                  </p>
                </div>
                <MinusCircle className='h-8 w-8 text-yellow-600' />
              </div>
            </div>

            <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm font-medium text-gray-600'>
                    Not Voting
                  </p>
                  <p className='text-2xl font-bold text-gray-600 mt-1'>
                    {vote.total_votes.not_voting}
                  </p>
                </div>
                <Clock className='h-8 w-8 text-gray-600' />
              </div>
            </div>
          </div>

          {/* Charts */}
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
            {/* Overall Vote Distribution */}
            <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                Overall Vote Distribution
              </h3>
              <div style={{ height: 300 }}>
                <ResponsiveContainer width='100%' height='100%'>
                  <PieChart>
                    <Pie
                      data={prepareOverallData()}
                      cx='50%'
                      cy='50%'
                      innerRadius={60}
                      outerRadius={120}
                      paddingAngle={5}
                      dataKey='value'
                    >
                      {prepareOverallData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number, name: string) => [
                        `${value} votes`,
                        name,
                      ]}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Party Breakdown */}
            <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                Vote by Party
              </h3>
              <div style={{ height: 300 }}>
                <ResponsiveContainer width='100%' height='100%'>
                  <BarChart data={preparePartyData()}>
                    <CartesianGrid strokeDasharray='3 3' />
                    <XAxis dataKey='party' />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey='Yea' stackId='a' fill='#10B981' />
                    <Bar dataKey='Nay' stackId='a' fill='#EF4444' />
                    <Bar dataKey='Present' stackId='a' fill='#F59E0B' />
                    <Bar dataKey='Not Voting' stackId='a' fill='#6B7280' />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Party Unity Scores */}
          <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4'>
              Party Unity on This Vote
            </h3>
            <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
              {Object.entries(partyUnity).map(([party, unity]) => (
                <div
                  key={party}
                  className='text-center p-4 bg-gray-50 rounded-lg'
                >
                  <p className='text-sm font-medium text-gray-600 mb-2'>
                    {DataService.getPartyLabel(party)}
                  </p>
                  <p
                    className='text-2xl font-bold mb-2'
                    style={{ color: DataService.getPartyColor(party) }}
                  >
                    {unity.toFixed(1)}%
                  </p>
                  <div className='w-full bg-gray-200 rounded-full h-2'>
                    <div
                      className='h-2 rounded-full'
                      style={{
                        width: `${unity}%`,
                        backgroundColor: DataService.getPartyColor(party),
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <>
          {/* Member Votes Filters */}
          <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-4'>
            <div className='flex flex-wrap gap-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Filter by Party
                </label>
                <select
                  value={filterParty}
                  onChange={e => setFilterParty(e.target.value)}
                  className='border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                >
                  <option value='all'>All Parties</option>
                  <option value='Democratic'>Democratic</option>
                  <option value='Republican'>Republican</option>
                  <option value='Independent'>Independent</option>
                </select>
              </div>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-1'>
                  Filter by Position
                </label>
                <select
                  value={filterPosition}
                  onChange={e => setFilterPosition(e.target.value)}
                  className='border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                >
                  <option value='all'>All Positions</option>
                  <option value='Yea'>Yea</option>
                  <option value='Nay'>Nay</option>
                  <option value='Present'>Present</option>
                  <option value='Not Voting'>Not Voting</option>
                </select>
              </div>
            </div>
          </div>

          {/* Members List */}
          <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
            <div className='px-6 py-4 border-b border-gray-200'>
              <h3 className='text-lg font-semibold text-gray-900'>
                Individual Member Votes ({getFilteredMembers().length})
              </h3>
            </div>
            <div className='divide-y divide-gray-200 max-h-96 overflow-y-auto'>
              {getFilteredMembers().map(member => (
                <div
                  key={member.bioguideId}
                  className='px-6 py-4 flex items-center justify-between hover:bg-gray-50'
                >
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
                      <Link
                        to={`/members/${member.bioguideId}`}
                        className='font-medium text-blue-600 hover:text-blue-800'
                      >
                        {member.name}
                      </Link>
                      <p className='text-sm text-gray-600'>
                        {member.state} •{' '}
                        {DataService.getPartyLabel(member.party)}
                      </p>
                    </div>
                  </div>
                  <div className='flex items-center gap-2'>
                    {getPositionIcon(member.position)}
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded ${getPositionColor(member.position)}`}
                    >
                      {member.position}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
