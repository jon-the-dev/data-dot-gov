import {
  User,
  MapPin,
  Calendar,
  TrendingUp,
  Vote,
  ExternalLink,
  ArrowLeft,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

import PartyUnityChart from './PartyUnityChart';

import DataService from '@/services/dataService';
import type { Member, VotePosition } from '@/types';

interface MemberProfileData {
  member: Member | null;
  votingRecord: VotePosition[];
  partyUnityScore: number;
  totalVotes: number;
  crossPartyVotes: number;
  loading: boolean;
  error: string | null;
}

export default function MemberProfile() {
  const { memberId } = useParams<{ memberId: string }>();
  const [data, setData] = useState<MemberProfileData>({
    member: null,
    votingRecord: [],
    partyUnityScore: 0,
    totalVotes: 0,
    crossPartyVotes: 0,
    loading: true,
    error: null,
  });

  useEffect(() => {
    if (memberId) {
      loadMemberData(memberId);
    }
  }, [memberId]);

  const loadMemberData = async (id: string) => {
    try {
      setData(prev => ({ ...prev, loading: true, error: null }));

      const [memberDetails, votingAnalysis] = await Promise.all([
        DataService.loadMemberDetails(id),
        DataService.loadVotingAnalysis(),
      ]);

      if (!memberDetails) {
        throw new Error('Member not found');
      }

      // Calculate party unity metrics from voting analysis
      const memberVoting = (votingAnalysis as any)?.member_voting?.[id] || {};
      const partyUnityScore = memberVoting.party_unity_score || 0;
      const totalVotes = memberVoting.total_votes || 0;
      const crossPartyVotes = memberVoting.cross_party_votes || 0;

      setData({
        member: memberDetails,
        votingRecord: memberDetails.votingRecord || [],
        partyUnityScore: partyUnityScore * 100, // Convert to percentage
        totalVotes,
        crossPartyVotes,
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Error loading member data:', error);
      setData(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load member details',
      }));
    }
  };

  if (data.loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600' />
      </div>
    );
  }

  if (data.error || !data.member) {
    return (
      <div className='bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg'>
        {data.error || 'Member not found'}
      </div>
    );
  }

  const { member } = data;
  const partyColor = DataService.getPartyColor(member.party);

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center gap-4 mb-6'>
        <Link
          to='/members'
          className='flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors'
        >
          <ArrowLeft size={20} />
          Back to Members
        </Link>
      </div>

      {/* Member Header */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <div className='flex flex-col md:flex-row md:items-center md:justify-between gap-4'>
          <div className='flex items-center gap-4'>
            <div
              className='w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold'
              style={{ backgroundColor: partyColor }}
            >
              <User size={32} />
            </div>
            <div>
              <h1 className='text-2xl font-bold text-gray-900'>
                {member.name}
              </h1>
              <div className='flex items-center gap-4 text-sm text-gray-600 mt-1'>
                <span className='flex items-center gap-1'>
                  <MapPin size={16} />
                  {member.state}
                  {member.district ? ` District ${member.district}` : ''}
                </span>
                <span
                  className='px-2 py-1 rounded text-white text-xs font-medium'
                  style={{ backgroundColor: partyColor }}
                >
                  {DataService.getPartyLabel(member.party)}
                </span>
                <span className='capitalize'>{member.chamber}</span>
              </div>
            </div>
          </div>

          <div className='flex gap-4'>
            <a
              href={`https://bioguide.congress.gov/search/bio/${member.bioguideId}`}
              target='_blank'
              rel='noopener noreferrer'
              className='flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors'
            >
              <ExternalLink size={16} />
              Bio Guide
            </a>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm font-medium text-gray-600'>
                Party Unity Score
              </p>
              <p className='text-2xl font-bold text-gray-900 mt-1'>
                {DataService.formatNumber(data.partyUnityScore)}%
              </p>
              <p className='text-xs text-gray-500 mt-1'>
                Votes with party majority
              </p>
            </div>
            <div className='p-3 rounded-lg bg-blue-100'>
              <TrendingUp className='h-6 w-6 text-blue-600' />
            </div>
          </div>
        </div>

        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm font-medium text-gray-600'>Total Votes</p>
              <p className='text-2xl font-bold text-gray-900 mt-1'>
                {data.totalVotes.toLocaleString()}
              </p>
              <p className='text-xs text-gray-500 mt-1'>Recorded votes</p>
            </div>
            <div className='p-3 rounded-lg bg-green-100'>
              <Vote className='h-6 w-6 text-green-600' />
            </div>
          </div>
        </div>

        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm font-medium text-gray-600'>
                Cross-Party Votes
              </p>
              <p className='text-2xl font-bold text-gray-900 mt-1'>
                {data.crossPartyVotes}
              </p>
              <p className='text-xs text-gray-500 mt-1'>
                {DataService.formatNumber(
                  DataService.calculatePercentage(
                    data.crossPartyVotes,
                    data.totalVotes
                  )
                )}
                % of total votes
              </p>
            </div>
            <div className='p-3 rounded-lg bg-purple-100'>
              <Calendar className='h-6 w-6 text-purple-600' />
            </div>
          </div>
        </div>
      </div>

      {/* Party Unity Chart */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          Voting Pattern Analysis
        </h3>
        <PartyUnityChart
          data={[
            {
              name: member.name,
              party: member.party,
              partyUnityScore: data.partyUnityScore,
              totalVotes: data.totalVotes,
              crossPartyVotes: data.crossPartyVotes,
            },
          ]}
          height={300}
        />
      </div>

      {/* Terms of Service */}
      {member.terms && member.terms.length > 0 && (
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4'>
            Congressional Terms
          </h3>
          <div className='space-y-3'>
            {member.terms.map((term, index) => (
              <div
                key={index}
                className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'
              >
                <div>
                  <p className='font-medium text-gray-900'>
                    {term.congress}th Congress ({term.chamber})
                  </p>
                  <p className='text-sm text-gray-600'>
                    {DataService.formatDate(term.startDate)} -{' '}
                    {DataService.formatDate(term.endDate)}
                  </p>
                </div>
                <div className='text-right'>
                  <p className='text-sm font-medium text-gray-900'>
                    {term.state}
                  </p>
                  <p className='text-xs text-gray-500'>
                    {DataService.getPartyLabel(term.party)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Votes */}
      {data.votingRecord.length > 0 && (
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4'>
            Recent Voting Record
          </h3>
          <div className='space-y-3'>
            {data.votingRecord.slice(0, 10).map((vote, index) => (
              <div
                key={index}
                className='flex items-center justify-between p-3 border border-gray-200 rounded-lg'
              >
                <div className='flex-1'>
                  <Link
                    to={`/votes/${vote.vote_id}`}
                    className='text-sm font-medium text-blue-600 hover:text-blue-800'
                  >
                    Vote #{vote.vote_id}
                  </Link>
                </div>
                <div className='flex items-center gap-2'>
                  <span
                    className={`
                      px-2 py-1 text-xs font-medium rounded
                      ${
                        vote.position === 'Yea'
                          ? 'bg-green-100 text-green-800'
                          : vote.position === 'Nay'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                      }
                    `}
                  >
                    {vote.position}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
