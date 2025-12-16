import {
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  Award,
  BarChart3,
  Activity,
  Target,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  RadialBarChart,
  RadialBar,
} from 'recharts';

import DataService from '../services/dataService';

function PartyComparison({ data }) {
  const [selectedView, setSelectedView] = useState('overview');
  const [trendsData, setTrendsData] = useState({
    legislativeActivity: null,
    bipartisanCooperation: null,
    votingConsistency: null,
    loading: false,
    error: null,
  });
  const { membersSummary, comprehensiveAnalysis } = data;

  // Load trend data when trends tab is selected
  useEffect(() => {
    if (
      selectedView === 'trends' &&
      !trendsData.legislativeActivity &&
      !trendsData.loading
    ) {
      loadTrendsData();
    }
  }, [selectedView, trendsData.legislativeActivity, trendsData.loading]);

  const loadTrendsData = async () => {
    setTrendsData(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [legislativeActivity, bipartisanCooperation, votingConsistency] =
        await Promise.all([
          DataService.fetchLegislativeActivity(),
          DataService.fetchBipartisanCooperation(),
          DataService.fetchVotingConsistency(),
        ]);

      setTrendsData({
        legislativeActivity,
        bipartisanCooperation,
        votingConsistency,
        loading: false,
        error: null,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Unknown error occurred';
      setTrendsData(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  };

  const COLORS = {
    Republican: '#E91D0E',
    Democratic: '#0075C4',
    Independent: '#9B59B6',
  };

  const getPartyBreakdown = () => {
    if (!membersSummary?.by_party) return [];

    return Object.entries(membersSummary.by_party).map(([party, count]) => ({
      name: party,
      value: count,
      percentage: ((count / membersSummary.total) * 100).toFixed(1),
    }));
  };

  const getChamberComparison = () => {
    if (!membersSummary?.by_chamber) return [];

    const senate = membersSummary.by_chamber.senate || {};
    const house = membersSummary.by_chamber.house || {};

    return [
      {
        chamber: 'Senate',
        Republican: senate.Republican || 0,
        Democratic: senate.Democratic || 0,
        Independent: senate.Independent || 0,
      },
      {
        chamber: 'House',
        Republican: house.Republican || 0,
        Democratic: house.Democratic || 0,
        Independent: house.Independent || 0,
      },
    ];
  };

  const getVotingPatterns = () => {
    if (!comprehensiveAnalysis?.voting_patterns) return null;

    const patterns = comprehensiveAnalysis.voting_patterns;
    return {
      unity: {
        republican: patterns.republican_unity || 0,
        democratic: patterns.democratic_unity || 0,
      },
      crossParty: patterns.cross_party_votes || [],
      contested: patterns.contested_votes || [],
    };
  };

  const partyBreakdown = getPartyBreakdown();
  const chamberComparison = getChamberComparison();
  const votingPatterns = getVotingPatterns();

  const VoteCard = ({ title, value, trend, description }) => (
    <div className='bg-white p-4 rounded-lg border border-gray-200'>
      <h4 className='text-sm font-medium text-gray-600'>{title}</h4>
      <div className='flex items-center justify-between mt-2'>
        <span className='text-2xl font-bold text-gray-900'>{value}</span>
        {trend && (
          <div
            className={`flex items-center ${trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-400'}`}
          >
            {trend === 'up' ? (
              <TrendingUp size={20} />
            ) : trend === 'down' ? (
              <TrendingDown size={20} />
            ) : (
              <Minus size={20} />
            )}
          </div>
        )}
      </div>
      {description && (
        <p className='text-xs text-gray-500 mt-2'>{description}</p>
      )}
    </div>
  );

  return (
    <div className='space-y-6'>
      <div>
        <h2 className='text-2xl font-bold text-gray-900 mb-4'>
          Party Comparison Analysis
        </h2>
        <p className='text-gray-600'>
          Compare voting patterns and party dynamics in the 118th Congress
        </p>
      </div>

      {/* View Selector */}
      <div className='flex gap-2 p-1 bg-gray-100 rounded-lg w-fit'>
        {['overview', 'voting', 'trends'].map(view => (
          <button
            key={view}
            onClick={() => setSelectedView(view)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedView === view
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {view.charAt(0).toUpperCase() + view.slice(1)}
          </button>
        ))}
      </div>

      {selectedView === 'overview' && (
        <>
          {/* Party Distribution Charts */}
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
            {/* Pie Chart */}
            <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                Overall Party Distribution
              </h3>
              <ResponsiveContainer width='100%' height={300}>
                <PieChart>
                  <Pie
                    data={partyBreakdown}
                    cx='50%'
                    cy='50%'
                    labelLine={false}
                    label={({ name, percentage }) => `${name}: ${percentage}%`}
                    outerRadius={80}
                    fill='#8884d8'
                    dataKey='value'
                  >
                    {partyBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.name]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Bar Chart */}
            <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                Chamber Comparison
              </h3>
              <ResponsiveContainer width='100%' height={300}>
                <BarChart data={chamberComparison}>
                  <CartesianGrid strokeDasharray='3 3' />
                  <XAxis dataKey='chamber' />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey='Republican' fill={COLORS.Republican} />
                  <Bar dataKey='Democratic' fill={COLORS.Democratic} />
                  <Bar dataKey='Independent' fill={COLORS.Independent} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* State-by-State Breakdown */}
          {membersSummary?.by_state && (
            <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                State-by-State Party Control
              </h3>
              <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3'>
                {Object.entries(membersSummary.by_state).map(
                  ([state, parties]) => {
                    const total = Object.values(parties).reduce(
                      (a, b) => a + b,
                      0
                    );
                    const majority = Object.entries(parties).reduce(
                      (a, b) => (b[1] > (a[1] || 0) ? b : a),
                      ['', 0]
                    );

                    return (
                      <div
                        key={state}
                        className={`p-3 rounded border-2 ${
                          majority[0] === 'Republican'
                            ? 'border-republican bg-republican/5'
                            : majority[0] === 'Democratic'
                              ? 'border-democrat bg-democrat/5'
                              : 'border-independent bg-independent/5'
                        }`}
                      >
                        <p className='font-medium text-sm text-gray-900'>
                          {state}
                        </p>
                        <div className='mt-1 space-y-1'>
                          {parties.Republican > 0 && (
                            <div className='text-xs'>
                              <span className='text-republican font-semibold'>
                                R: {parties.Republican}
                              </span>
                            </div>
                          )}
                          {parties.Democratic > 0 && (
                            <div className='text-xs'>
                              <span className='text-democrat font-semibold'>
                                D: {parties.Democratic}
                              </span>
                            </div>
                          )}
                          {parties.Independent > 0 && (
                            <div className='text-xs'>
                              <span className='text-independent font-semibold'>
                                I: {parties.Independent}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  }
                )}
              </div>
            </div>
          )}
        </>
      )}

      {selectedView === 'voting' && (
        <div className='space-y-6'>
          {/* Party Unity Scores */}
          {votingPatterns ? (
            <>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                <VoteCard
                  title='Republican Party Unity'
                  value={`${votingPatterns.unity.republican}%`}
                  description='Percentage of votes where Republicans voted together'
                />
                <VoteCard
                  title='Democratic Party Unity'
                  value={`${votingPatterns.unity.democratic}%`}
                  description='Percentage of votes where Democrats voted together'
                />
              </div>

              {/* Cross-Party Votes */}
              {votingPatterns.crossParty.length > 0 && (
                <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                  <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                    Recent Cross-Party Votes
                  </h3>
                  <div className='space-y-3'>
                    {votingPatterns.crossParty
                      .slice(0, 5)
                      .map((vote, index) => (
                        <div
                          key={index}
                          className='border-l-4 border-purple-500 pl-4 py-2'
                        >
                          <p className='text-sm font-medium text-gray-900'>
                            {vote.title}
                          </p>
                          <p className='text-xs text-gray-600 mt-1'>
                            {vote.republicans_for} Republicans voted with{' '}
                            {vote.democrats_for} Democrats
                          </p>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className='bg-yellow-50 border border-yellow-200 p-4 rounded-lg'>
              <p className='text-yellow-800'>
                Voting pattern data not available. Additional analysis scripts
                need to be run to generate this data.
              </p>
            </div>
          )}
        </div>
      )}

      {selectedView === 'trends' && (
        <div className='space-y-6'>
          {trendsData.loading ? (
            <div className='flex items-center justify-center h-64 bg-white rounded-lg border border-gray-200'>
              <div className='text-center'>
                <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4' />
                <p className='text-gray-600'>Loading trend analysis...</p>
              </div>
            </div>
          ) : trendsData.error ? (
            <div className='bg-red-50 border border-red-200 p-4 rounded-lg'>
              <p className='text-red-800'>
                Error loading trend data: {trendsData.error}
              </p>
              <button
                onClick={loadTrendsData}
                className='mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700'
              >
                Retry
              </button>
            </div>
          ) : trendsData.legislativeActivity ||
            trendsData.bipartisanCooperation ||
            trendsData.votingConsistency ? (
            <>
              {/* Legislative Activity Section */}
              {trendsData.legislativeActivity && (
                <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                  <div className='flex items-center gap-3 mb-6'>
                    <BarChart3 className='h-6 w-6 text-blue-600' />
                    <h3 className='text-lg font-semibold text-gray-900'>
                      Legislative Activity Trends
                    </h3>
                  </div>

                  <div className='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6'>
                    {/* Monthly Activity Chart */}
                    <div>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Monthly Bill Sponsorship
                      </h4>
                      <ResponsiveContainer width='100%' height={250}>
                        <BarChart
                          data={
                            trendsData.legislativeActivity.sponsorship_patterns
                              ?.trends?.monthly_activity || []
                          }
                        >
                          <CartesianGrid strokeDasharray='3 3' />
                          <XAxis dataKey='month' tick={{ fontSize: 12 }} />
                          <YAxis />
                          <Tooltip />
                          <Legend />
                          <Bar
                            dataKey='republican_bills'
                            fill={COLORS.Republican}
                            name='Republican'
                          />
                          <Bar
                            dataKey='democratic_bills'
                            fill={COLORS.Democratic}
                            name='Democratic'
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Policy Area Distribution */}
                    <div>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Policy Area Focus
                      </h4>
                      <ResponsiveContainer width='100%' height={250}>
                        <PieChart>
                          <Pie
                            data={[
                              ...(
                                trendsData.legislativeActivity
                                  .sponsorship_patterns?.by_party?.Republican
                                  ?.top_policy_areas || []
                              ).map((area, idx) => ({
                                name: area,
                                value: 100 - idx * 10,
                                party: 'Republican',
                              })),
                              ...(
                                trendsData.legislativeActivity
                                  .sponsorship_patterns?.by_party?.Democratic
                                  ?.top_policy_areas || []
                              ).map((area, idx) => ({
                                name: area,
                                value: 90 - idx * 10,
                                party: 'Democratic',
                              })),
                            ]}
                            cx='50%'
                            cy='50%'
                            outerRadius={80}
                            dataKey='value'
                          >
                            {trendsData.legislativeActivity.sponsorship_patterns?.by_party?.Republican?.top_policy_areas?.map(
                              (_, index) => (
                                <Cell
                                  key={`republican-${index}`}
                                  fill={COLORS.Republican}
                                />
                              )
                            )}
                            {trendsData.legislativeActivity.sponsorship_patterns?.by_party?.Democratic?.top_policy_areas?.map(
                              (_, index) => (
                                <Cell
                                  key={`democratic-${index}`}
                                  fill={COLORS.Democratic}
                                />
                              )
                            )}
                          </Pie>
                          <Tooltip />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Top Sponsors */}
                  {trendsData.legislativeActivity.sponsorship_patterns?.trends
                    ?.most_active_sponsors && (
                    <div>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Most Active Sponsors
                      </h4>
                      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
                        {trendsData.legislativeActivity.sponsorship_patterns.trends.most_active_sponsors
                          .slice(0, 6)
                          .map((sponsor, idx) => (
                            <div
                              key={idx}
                              className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'
                            >
                              <div>
                                <p className='font-medium text-sm text-gray-900'>
                                  {sponsor.name}
                                </p>
                                <p className='text-xs text-gray-600'>
                                  {DataService.getPartyLabel(sponsor.party)}
                                </p>
                              </div>
                              <div className='text-right'>
                                <p
                                  className='text-lg font-bold'
                                  style={{
                                    color: DataService.getPartyColor(
                                      sponsor.party
                                    ),
                                  }}
                                >
                                  {sponsor.bills_sponsored}
                                </p>
                                <p className='text-xs text-gray-500'>bills</p>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Bipartisan Cooperation Section */}
              {trendsData.bipartisanCooperation && (
                <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                  <div className='flex items-center gap-3 mb-6'>
                    <Users className='h-6 w-6 text-purple-600' />
                    <h3 className='text-lg font-semibold text-gray-900'>
                      Bipartisan Cooperation Analysis
                    </h3>
                  </div>

                  <div className='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6'>
                    {/* Cooperation Trends */}
                    <div>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Monthly Cooperation Trends
                      </h4>
                      <ResponsiveContainer width='100%' height={250}>
                        <LineChart
                          data={
                            trendsData.bipartisanCooperation.cooperation_metrics
                              ?.monthly_trends || []
                          }
                        >
                          <CartesianGrid strokeDasharray='3 3' />
                          <XAxis dataKey='month' tick={{ fontSize: 12 }} />
                          <YAxis
                            domain={[0, 1]}
                            tickFormatter={value =>
                              `${(value * 100).toFixed(0)}%`
                            }
                          />
                          <Tooltip
                            formatter={value => [
                              `${(value * 100).toFixed(1)}%`,
                              'Bipartisan Rate',
                            ]}
                          />
                          <Line
                            type='monotone'
                            dataKey='bipartisan_rate'
                            stroke='#7c3aed'
                            strokeWidth={2}
                            dot={{ fill: '#7c3aed' }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Policy Area Bipartisan Appeal */}
                    <div>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Most Bipartisan Policy Areas
                      </h4>
                      <ResponsiveContainer width='100%' height={250}>
                        <BarChart
                          data={
                            trendsData.bipartisanCooperation.cooperation_metrics
                              ?.top_bipartisan_areas || []
                          }
                          layout='horizontal'
                        >
                          <CartesianGrid strokeDasharray='3 3' />
                          <XAxis
                            type='number'
                            domain={[0, 1]}
                            tickFormatter={value =>
                              `${(value * 100).toFixed(0)}%`
                            }
                          />
                          <YAxis
                            type='category'
                            dataKey='policy_area'
                            width={100}
                            tick={{ fontSize: 12 }}
                          />
                          <Tooltip
                            formatter={value => [
                              `${(value * 100).toFixed(1)}%`,
                              'Bipartisan Rate',
                            ]}
                          />
                          <Bar
                            dataKey='bipartisan_rate'
                            fill='#7c3aed'
                            radius={[0, 4, 4, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Bridge Builders */}
                  {trendsData.bipartisanCooperation.cooperation_metrics
                    ?.bridge_builders && (
                    <div>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Top Bridge Builders
                      </h4>
                      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
                        {trendsData.bipartisanCooperation.cooperation_metrics.bridge_builders
                          .slice(0, 6)
                          .map((member, idx) => (
                            <div
                              key={idx}
                              className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'
                            >
                              <div>
                                <p className='font-medium text-sm text-gray-900'>
                                  {member.name}
                                </p>
                                <p className='text-xs text-gray-600'>
                                  {DataService.getPartyLabel(member.party)}
                                </p>
                              </div>
                              <div className='text-right'>
                                <p className='text-lg font-bold text-purple-600'>
                                  {(member.bipartisan_score * 100).toFixed(0)}%
                                </p>
                                <p className='text-xs text-gray-500'>
                                  bipartisan
                                </p>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Voting Consistency Section */}
              {trendsData.votingConsistency && (
                <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                  <div className='flex items-center gap-3 mb-6'>
                    <Target className='h-6 w-6 text-green-600' />
                    <h3 className='text-lg font-semibold text-gray-900'>
                      Party Unity & Voting Consistency
                    </h3>
                  </div>

                  <div className='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6'>
                    {/* Party Unity Gauges */}
                    <div>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Party Unity Scores
                      </h4>
                      <ResponsiveContainer width='100%' height={250}>
                        <RadialBarChart
                          cx='50%'
                          cy='50%'
                          innerRadius='40%'
                          outerRadius='90%'
                          data={Object.entries(
                            trendsData.votingConsistency.consistency_metrics
                              ?.party_unity_scores || {}
                          ).map(([party, score]) => ({
                            party,
                            score: score * 100,
                            fill: COLORS[party] || '#666666',
                          }))}
                        >
                          <RadialBar dataKey='score' cornerRadius={10} />
                          <Tooltip
                            formatter={value => [
                              `${value.toFixed(1)}%`,
                              'Unity Score',
                            ]}
                          />
                          <Legend />
                        </RadialBarChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Temporal Unity Trends */}
                    <div>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Unity Trends Over Time
                      </h4>
                      <ResponsiveContainer width='100%' height={250}>
                        <LineChart
                          data={
                            trendsData.votingConsistency.consistency_metrics
                              ?.temporal_trends || []
                          }
                        >
                          <CartesianGrid strokeDasharray='3 3' />
                          <XAxis dataKey='month' tick={{ fontSize: 12 }} />
                          <YAxis
                            domain={[0.5, 1]}
                            tickFormatter={value =>
                              `${(value * 100).toFixed(0)}%`
                            }
                          />
                          <Tooltip
                            formatter={value => [
                              `${(value * 100).toFixed(1)}%`,
                              'Party Unity',
                            ]}
                          />
                          <Line
                            type='monotone'
                            dataKey='party_unity'
                            stroke='#10b981'
                            strokeWidth={2}
                            dot={{ fill: '#10b981' }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Maverick Members */}
                  {trendsData.votingConsistency.consistency_metrics
                    ?.maverick_members && (
                    <div>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Independent Voices (Mavericks)
                      </h4>
                      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
                        {trendsData.votingConsistency.consistency_metrics.maverick_members
                          .slice(0, 6)
                          .map((member, idx) => (
                            <div
                              key={idx}
                              className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'
                            >
                              <div>
                                <p className='font-medium text-sm text-gray-900'>
                                  {member.name}
                                </p>
                                <p className='text-xs text-gray-600'>
                                  {DataService.getPartyLabel(member.party)}
                                </p>
                              </div>
                              <div className='text-right'>
                                <p className='text-lg font-bold text-orange-600'>
                                  {(member.unity_score * 100).toFixed(0)}%
                                </p>
                                <p className='text-xs text-gray-500'>unity</p>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Key Divisive Votes */}
                  {trendsData.votingConsistency.consistency_metrics
                    ?.key_divisive_votes && (
                    <div className='mt-6'>
                      <h4 className='text-md font-medium text-gray-700 mb-3'>
                        Most Divisive Recent Votes
                      </h4>
                      <div className='space-y-3'>
                        {trendsData.votingConsistency.consistency_metrics.key_divisive_votes
                          .slice(0, 3)
                          .map((vote, idx) => (
                            <div
                              key={idx}
                              className='border-l-4 border-red-500 pl-4 py-2 bg-red-50'
                            >
                              <p className='text-sm font-medium text-gray-900'>
                                {vote.description}
                              </p>
                              <p className='text-xs text-gray-600 mt-1'>
                                {DataService.formatDate(vote.date)} - R:{' '}
                                {vote.party_split?.R_for || 0} for,{' '}
                                {vote.party_split?.R_against || 0} against | D:{' '}
                                {vote.party_split?.D_for || 0} for,{' '}
                                {vote.party_split?.D_against || 0} against
                              </p>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className='space-y-6'>
              <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
                <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                  Party Trends & Insights
                </h3>
                <div className='space-y-4'>
                  <div className='p-4 bg-blue-50 border-l-4 border-blue-500 rounded'>
                    <h4 className='font-medium text-blue-900'>
                      Legislative Activity
                    </h4>
                    <p className='text-sm text-blue-700 mt-1'>
                      Analysis of bill sponsorship and co-sponsorship patterns
                      by party
                    </p>
                  </div>
                  <div className='p-4 bg-purple-50 border-l-4 border-purple-500 rounded'>
                    <h4 className='font-medium text-purple-900'>
                      Bipartisan Cooperation
                    </h4>
                    <p className='text-sm text-purple-700 mt-1'>
                      Tracking cross-party collaboration on key legislation
                    </p>
                  </div>
                  <div className='p-4 bg-green-50 border-l-4 border-green-500 rounded'>
                    <h4 className='font-medium text-green-900'>
                      Voting Consistency
                    </h4>
                    <p className='text-sm text-green-700 mt-1'>
                      Measuring how consistently members vote with their party
                      line
                    </p>
                  </div>
                </div>
              </div>

              <div className='bg-yellow-50 border border-yellow-200 p-4 rounded-lg'>
                <p className='text-yellow-800'>
                  Trend analysis data is not available. This may be because the
                  backend trend endpoints are not yet implemented or there's no
                  analysis data available.
                </p>
                <button
                  onClick={loadTrendsData}
                  className='mt-2 px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700'
                >
                  Try Loading Data
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PartyComparison;
