import {
  TrendingUp,
  BarChart3,
  PieChart,
  LineChart,
  Filter,
  Download,
  Users,
  Vote,
  Target,
} from 'lucide-react';
import { useState, useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  LineChart as RechartsLineChart,
  Line,
  Legend,
  RadialBarChart,
  RadialBar,
} from 'recharts';

const PARTY_COLORS = {
  Republican: '#dc2626',
  Democratic: '#2563eb',
  Independent: '#7c3aed',
};

const CHART_COLORS = [
  '#3b82f6',
  '#ef4444',
  '#10b981',
  '#f59e0b',
  '#8b5cf6',
  '#ec4899',
];

function CommitteeVoteChart({ committeeId, data, className = '' }) {
  const [activeView, setActiveView] = useState('unity'); // unity, bipartisan, timeline, overview
  const [selectedTimeframe, setSelectedTimeframe] = useState('all'); // all, year, quarter

  // Mock data - in real app, this would come from props or API
  const mockVoteData = useMemo(
    () => ({
      unity: {
        Republican: { score: 87.5, total: 125, unified: 109, splits: 16 },
        Democratic: { score: 92.3, total: 98, unified: 90, splits: 8 },
        Independent: { score: 78.0, total: 5, unified: 4, splits: 1 },
      },
      bipartisan: [
        {
          name: 'Immigration Reform',
          republican: 45,
          democratic: 67,
          bipartisan: 23,
        },
        {
          name: 'Infrastructure',
          republican: 78,
          democratic: 89,
          bipartisan: 67,
        },
        { name: 'Healthcare', republican: 23, democratic: 91, bipartisan: 12 },
        { name: 'Defense', republican: 89, democratic: 72, bipartisan: 61 },
        { name: 'Education', republican: 34, democratic: 87, bipartisan: 21 },
      ],
      timeline: [
        { period: '2023 Q1', republican: 85, democratic: 91, bipartisan: 23 },
        { period: '2023 Q2', republican: 88, democratic: 89, bipartisan: 31 },
        { period: '2023 Q3', republican: 82, democratic: 94, bipartisan: 18 },
        { period: '2023 Q4', republican: 90, democratic: 88, bipartisan: 27 },
        { period: '2024 Q1', republican: 87, democratic: 92, bipartisan: 25 },
      ],
      topVoters: [
        { name: 'Sen. Johnson', party: 'Republican', unity: 96, votes: 45 },
        { name: 'Sen. Williams', party: 'Democratic', unity: 94, votes: 42 },
        { name: 'Sen. Brown', party: 'Democratic', unity: 93, votes: 38 },
        { name: 'Sen. Davis', party: 'Republican', unity: 92, votes: 41 },
        { name: 'Sen. Miller', party: 'Independent', unity: 78, votes: 23 },
      ],
    }),
    []
  );

  const chartData = useMemo(() => {
    const { unity, bipartisan, timeline, topVoters } = mockVoteData;

    switch (activeView) {
      case 'unity':
        return Object.entries(unity).map(([party, data]) => ({
          party,
          score: data.score,
          total: data.total,
          unified: data.unified,
          splits: data.splits,
          percentage: (data.unified / data.total) * 100,
        }));

      case 'bipartisan':
        return bipartisan;

      case 'timeline':
        return timeline;

      case 'overview':
        return topVoters;

      default:
        return [];
    }
  }, [activeView, mockVoteData]);

  const overallStats = useMemo(() => {
    const totalVotes = Object.values(mockVoteData.unity).reduce(
      (sum, party) => sum + party.total,
      0
    );
    const totalUnified = Object.values(mockVoteData.unity).reduce(
      (sum, party) => sum + party.unified,
      0
    );
    const overallUnity =
      totalVotes > 0 ? ((totalUnified / totalVotes) * 100).toFixed(1) : 0;
    const bipartisanAvg =
      mockVoteData.bipartisan.reduce((sum, item) => sum + item.bipartisan, 0) /
      mockVoteData.bipartisan.length;

    return {
      totalVotes,
      overallUnity,
      bipartisanAvg: bipartisanAvg.toFixed(1),
      mostUnified: Object.entries(mockVoteData.unity).reduce(
        (max, [party, data]) =>
          data.score > max.score ? { party, score: data.score } : max,
        { party: '', score: 0 }
      ),
    };
  }, [mockVoteData]);

  const StatCard = ({
    icon: Icon,
    title,
    value,
    subtitle,
    color = 'text-blue-600',
  }) => (
    <div className='bg-white p-4 rounded-lg shadow-sm border border-gray-200'>
      <div className='flex items-center justify-between'>
        <div>
          <p className='text-sm font-medium text-gray-600'>{title}</p>
          <p className={`text-xl font-bold mt-1 ${color}`}>{value}</p>
          {subtitle && <p className='text-xs text-gray-500 mt-1'>{subtitle}</p>}
        </div>
        <Icon
          className={`h-5 w-5 ${color.replace('text-', 'text-').replace('600', '400')}`}
        />
      </div>
    </div>
  );

  const renderChart = () => {
    switch (activeView) {
      case 'unity':
        return (
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
            {/* Unity Scores Bar Chart */}
            <div className='h-64'>
              <h4 className='text-sm font-semibold text-gray-700 mb-3'>
                Party Unity Scores
              </h4>
              <ResponsiveContainer width='100%' height='100%'>
                <BarChart
                  data={chartData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray='3 3' />
                  <XAxis dataKey='party' />
                  <YAxis domain={[0, 100]} />
                  <Tooltip
                    formatter={(value, name) => [
                      name === 'score' ? `${value}%` : value,
                      name === 'score' ? 'Unity Score' : name,
                    ]}
                    labelFormatter={label => `Party: ${label}`}
                  />
                  <Bar
                    dataKey='score'
                    fill='#3b82f6'
                    radius={[4, 4, 0, 0]}
                    name='Unity Score'
                  >
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={PARTY_COLORS[entry.party] || '#6b7280'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Unity Distribution Pie Chart */}
            <div className='h-64'>
              <h4 className='text-sm font-semibold text-gray-700 mb-3'>
                Vote Distribution
              </h4>
              <ResponsiveContainer width='100%' height='100%'>
                <RechartsPieChart>
                  <Pie
                    data={chartData}
                    cx='50%'
                    cy='50%'
                    outerRadius={80}
                    dataKey='unified'
                    label={({ party, unified, total }) =>
                      `${party}: ${unified}/${total}`
                    }
                  >
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={PARTY_COLORS[entry.party] || CHART_COLORS[index]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, name, props) => [
                      `${value} unified votes`,
                      `${props.payload.party}`,
                    ]}
                  />
                  <Legend />
                </RechartsPieChart>
              </ResponsiveContainer>
            </div>
          </div>
        );

      case 'bipartisan':
        return (
          <div className='h-80'>
            <h4 className='text-sm font-semibold text-gray-700 mb-3'>
              Bipartisan Cooperation by Topic
            </h4>
            <ResponsiveContainer width='100%' height='100%'>
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis
                  dataKey='name'
                  angle={-45}
                  textAnchor='end'
                  height={60}
                  fontSize={12}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar
                  dataKey='republican'
                  fill='#dc2626'
                  name='Republican Support %'
                  radius={[2, 2, 0, 0]}
                />
                <Bar
                  dataKey='democratic'
                  fill='#2563eb'
                  name='Democratic Support %'
                  radius={[2, 2, 0, 0]}
                />
                <Bar
                  dataKey='bipartisan'
                  fill='#10b981'
                  name='Bipartisan Votes'
                  radius={[2, 2, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      case 'timeline':
        return (
          <div className='h-80'>
            <h4 className='text-sm font-semibold text-gray-700 mb-3'>
              Unity Trends Over Time
            </h4>
            <ResponsiveContainer width='100%' height='100%'>
              <RechartsLineChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis dataKey='period' />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={value => [`${value}%`, 'Unity Score']} />
                <Legend />
                <Line
                  type='monotone'
                  dataKey='republican'
                  stroke='#dc2626'
                  strokeWidth={2}
                  name='Republican Unity %'
                  dot={{ fill: '#dc2626' }}
                />
                <Line
                  type='monotone'
                  dataKey='democratic'
                  stroke='#2563eb'
                  strokeWidth={2}
                  name='Democratic Unity %'
                  dot={{ fill: '#2563eb' }}
                />
                <Line
                  type='monotone'
                  dataKey='bipartisan'
                  stroke='#10b981'
                  strokeWidth={2}
                  name='Bipartisan Votes'
                  dot={{ fill: '#10b981' }}
                />
              </RechartsLineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'overview':
        return (
          <div className='h-80'>
            <h4 className='text-sm font-semibold text-gray-700 mb-3'>
              Top Committee Members by Unity Score
            </h4>
            <ResponsiveContainer width='100%' height='100%'>
              <BarChart
                data={chartData}
                layout='horizontal'
                margin={{ top: 20, right: 30, left: 80, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis type='number' domain={[0, 100]} />
                <YAxis type='category' dataKey='name' fontSize={12} />
                <Tooltip
                  formatter={(value, name) => [
                    name === 'unity' ? `${value}%` : value,
                    name === 'unity' ? 'Unity Score' : name,
                  ]}
                  labelFormatter={label => `${label}`}
                />
                <Bar dataKey='unity' radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={PARTY_COLORS[entry.party] || '#6b7280'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      default:
        return <div>No chart data available</div>;
    }
  };

  if (!data && !mockVoteData) {
    return (
      <div
        className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}
      >
        <div className='text-center py-8'>
          <Vote className='h-12 w-12 text-gray-400 mx-auto mb-4' />
          <h3 className='text-lg font-medium text-gray-900 mb-2'>
            No Voting Data Available
          </h3>
          <p className='text-gray-500'>
            Committee voting patterns will appear here when data becomes
            available.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}
    >
      {/* Header */}
      <div className='border-b border-gray-200 p-6'>
        <div className='flex items-center justify-between'>
          <div>
            <h3 className='text-xl font-semibold text-gray-900 flex items-center gap-2'>
              <TrendingUp className='h-5 w-5' />
              Committee Vote Analysis
            </h3>
            <p className='text-sm text-gray-600 mt-1'>
              Voting patterns, party unity, and bipartisan cooperation metrics
            </p>
          </div>
          <div className='flex items-center gap-2'>
            <button className='p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded'>
              <Download size={16} />
            </button>
            <button className='p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded'>
              <Filter size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4 p-6 border-b border-gray-200'>
        <StatCard
          icon={Users}
          title='Total Votes'
          value={overallStats.totalVotes}
          subtitle='Committee votes tracked'
          color='text-blue-600'
        />
        <StatCard
          icon={Target}
          title='Overall Unity'
          value={`${overallStats.overallUnity}%`}
          subtitle='Average party cohesion'
          color='text-green-600'
        />
        <StatCard
          icon={TrendingUp}
          title='Bipartisan Avg'
          value={`${overallStats.bipartisanAvg}%`}
          subtitle='Cross-party cooperation'
          color='text-purple-600'
        />
        <StatCard
          icon={Vote}
          title='Most Unified'
          value={overallStats.mostUnified.party}
          subtitle={`${overallStats.mostUnified.score}% unity`}
          color='text-orange-600'
        />
      </div>

      {/* View Selector */}
      <div className='flex items-center justify-between p-6 border-b border-gray-200'>
        <div className='flex space-x-1 bg-gray-100 rounded-lg p-1'>
          {[
            { key: 'unity', label: 'Party Unity', icon: Target },
            { key: 'bipartisan', label: 'Bipartisan', icon: Users },
            { key: 'timeline', label: 'Timeline', icon: LineChart },
            { key: 'overview', label: 'Top Members', icon: BarChart3 },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveView(key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeView === key
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        <select
          value={selectedTimeframe}
          onChange={e => setSelectedTimeframe(e.target.value)}
          className='px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        >
          <option value='all'>All Time</option>
          <option value='year'>Past Year</option>
          <option value='quarter'>Past Quarter</option>
        </select>
      </div>

      {/* Chart Content */}
      <div className='p-6'>{renderChart()}</div>

      {/* Footer with insights */}
      <div className='border-t border-gray-200 p-6 bg-gray-50'>
        <h4 className='text-sm font-semibold text-gray-700 mb-3'>
          Key Insights
        </h4>
        <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600'>
          <div>
            <p className='font-medium text-gray-900'>Party Cohesion</p>
            <p>
              Democrats show {mockVoteData.unity.Democratic.score}% unity vs
              Republicans at {mockVoteData.unity.Republican.score}%
            </p>
          </div>
          <div>
            <p className='font-medium text-gray-900'>
              Bipartisan Opportunities
            </p>
            <p>
              Infrastructure and Defense show highest cross-party support
              potential
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CommitteeVoteChart;
