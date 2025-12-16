// Reusable chart components for trend visualization
import PropTypes from 'prop-types';
import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  RadialBarChart,
  RadialBar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Party color constants
const PARTY_COLORS = {
  Republican: '#E91D0E',
  Democratic: '#0075C4',
  Independent: '#9B59B6',
  R: '#E91D0E',
  D: '#0075C4',
  I: '#9B59B6',
};

const CHART_COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

/**
 * Monthly Activity Bar Chart Component
 */
export function MonthlyActivityChart({ data, title = 'Monthly Activity' }) {
  if (!data || !Array.isArray(data)) {
    return (
      <div className='flex items-center justify-center h-64 bg-gray-50 rounded-lg'>
        <p className='text-gray-500'>No data available</p>
      </div>
    );
  }

  return (
    <div className='w-full'>
      <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
      <ResponsiveContainer width='100%' height={250}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis dataKey='month' tick={{ fontSize: 12 }} />
          <YAxis />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Bar
            dataKey='republican_bills'
            fill={PARTY_COLORS.Republican}
            name='Republican Bills'
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey='democratic_bills'
            fill={PARTY_COLORS.Democratic}
            name='Democratic Bills'
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Policy Areas Pie Chart Component
 */
export function PolicyAreasPieChart({
  republicanAreas,
  democraticAreas,
  title = 'Policy Area Distribution',
}) {
  if (!republicanAreas?.length && !democraticAreas?.length) {
    return (
      <div className='flex items-center justify-center h-64 bg-gray-50 rounded-lg'>
        <p className='text-gray-500'>No policy area data available</p>
      </div>
    );
  }

  const data = [
    ...(republicanAreas || []).map((area, idx) => ({
      name: area,
      value: 100 - idx * 10, // Mock values for visualization
      party: 'Republican',
    })),
    ...(democraticAreas || []).map((area, idx) => ({
      name: area,
      value: 90 - idx * 10, // Mock values for visualization
      party: 'Democratic',
    })),
  ];

  return (
    <div className='w-full'>
      <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
      <ResponsiveContainer width='100%' height={250}>
        <PieChart>
          <Pie data={data} cx='50%' cy='50%' outerRadius={80} dataKey='value'>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  PARTY_COLORS[entry.party] ||
                  CHART_COLORS[index % CHART_COLORS.length]
                }
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value, name, props) => [
              `${value}%`,
              `${props.payload.name} (${props.payload.party})`,
            ]}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Bipartisan Cooperation Trend Line Chart
 */
export function BipartisanTrendChart({
  data,
  title = 'Bipartisan Cooperation Trends',
}) {
  if (!data || !Array.isArray(data)) {
    return (
      <div className='flex items-center justify-center h-64 bg-gray-50 rounded-lg'>
        <p className='text-gray-500'>No trend data available</p>
      </div>
    );
  }

  return (
    <div className='w-full'>
      <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
      <ResponsiveContainer width='100%' height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis dataKey='month' tick={{ fontSize: 12 }} />
          <YAxis
            tickFormatter={value => `${(value * 100).toFixed(0)}%`}
            domain={[0, 'dataMax']}
          />
          <Tooltip
            formatter={value => [
              `${(value * 100).toFixed(1)}%`,
              'Bipartisan Rate',
            ]}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Line
            type='monotone'
            dataKey='bipartisan_rate'
            stroke='#9B59B6'
            strokeWidth={3}
            dot={{ fill: '#9B59B6', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Horizontal Bar Chart for Rankings
 */
export function RankingBarChart({
  data,
  title = 'Rankings',
  dataKey,
  valueKey = 'value',
}) {
  if (!data || !Array.isArray(data)) {
    return (
      <div className='flex items-center justify-center h-64 bg-gray-50 rounded-lg'>
        <p className='text-gray-500'>No ranking data available</p>
      </div>
    );
  }

  return (
    <div className='w-full'>
      <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
      <ResponsiveContainer width='100%' height={250}>
        <BarChart data={data} layout='horizontal'>
          <CartesianGrid strokeDasharray='3 3' />
          <XAxis
            type='number'
            tickFormatter={value => `${(value * 100).toFixed(0)}%`}
          />
          <YAxis
            dataKey={dataKey}
            type='category'
            width={100}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={value => [
              `${(value * 100).toFixed(1)}%`,
              'Bipartisan Rate',
            ]}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Bar dataKey={valueKey} fill='#9B59B6' radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Party Unity Radial Bar Chart
 */
export function PartyUnityRadialChart({ data, title = 'Party Unity Scores' }) {
  if (!data || typeof data !== 'object') {
    return (
      <div className='flex items-center justify-center h-64 bg-gray-50 rounded-lg'>
        <p className='text-gray-500'>No unity data available</p>
      </div>
    );
  }

  const chartData = Object.entries(data).map(([party, score]) => ({
    party,
    score: score * 100,
    fill: PARTY_COLORS[party] || '#666666',
  }));

  return (
    <div className='w-full'>
      <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
      <ResponsiveContainer width='100%' height={250}>
        <RadialBarChart
          cx='50%'
          cy='50%'
          innerRadius='40%'
          outerRadius='90%'
          data={chartData}
        >
          <RadialBar
            dataKey='score'
            cornerRadius={10}
            fill={entry => entry.fill}
          />
          <Tooltip
            formatter={(value, name) => [
              `${value.toFixed(1)}%`,
              `${name} Unity`,
            ]}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
        </RadialBarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Member Spotlight Cards Component
 */
export function MemberSpotlightCards({
  members,
  title,
  scoreLabel,
  scoreKey = 'bipartisan_score',
}) {
  if (!members || !Array.isArray(members)) {
    return (
      <div className='bg-gray-50 p-4 rounded-lg'>
        <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
        <p className='text-gray-500'>No member data available</p>
      </div>
    );
  }

  return (
    <div>
      <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
        {members.slice(0, 6).map((member, idx) => (
          <div
            key={idx}
            className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'
          >
            <div>
              <p className='font-medium text-gray-900 text-sm'>{member.name}</p>
              <p
                className='text-xs'
                style={{ color: PARTY_COLORS[member.party] }}
              >
                {member.party === 'R'
                  ? 'Republican'
                  : member.party === 'D'
                    ? 'Democratic'
                    : member.party === 'I'
                      ? 'Independent'
                      : member.party}
              </p>
            </div>
            <div className='text-right'>
              <p className='font-semibold text-gray-900'>
                {typeof member[scoreKey] === 'number'
                  ? `${(member[scoreKey] * 100).toFixed(0)}%`
                  : member[scoreKey] || 'N/A'}
              </p>
              <p className='text-xs text-gray-600'>{scoreLabel}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Divisive Votes List Component
 */
export function DivisiveVotesList({
  votes,
  title = 'Most Divisive Recent Votes',
}) {
  if (!votes || !Array.isArray(votes)) {
    return (
      <div className='bg-gray-50 p-4 rounded-lg'>
        <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
        <p className='text-gray-500'>No vote data available</p>
      </div>
    );
  }

  return (
    <div>
      <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
      <div className='space-y-3'>
        {votes.slice(0, 3).map((vote, idx) => (
          <div
            key={idx}
            className='border-l-4 border-red-500 pl-4 py-2 bg-red-50'
          >
            <h5 className='font-medium text-gray-900'>{vote.description}</h5>
            <p className='text-sm text-gray-600 mt-1'>
              {vote.date && new Date(vote.date).toLocaleDateString()}
            </p>
            {vote.party_split && (
              <div className='flex flex-wrap gap-4 mt-2 text-sm'>
                <span className='text-red-600'>
                  Republicans: {vote.party_split.R_for} for,{' '}
                  {vote.party_split.R_against} against
                </span>
                <span className='text-blue-600'>
                  Democrats: {vote.party_split.D_for} for,{' '}
                  {vote.party_split.D_against} against
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Simple Network Visualization for Bipartisan Relationships
 */
export function SimpleNetworkVisualization({
  bridgeBuilders,
  title = 'Cross-Party Collaboration Network',
}) {
  if (!bridgeBuilders || !Array.isArray(bridgeBuilders)) {
    return (
      <div className='flex items-center justify-center h-64 bg-gray-50 rounded-lg'>
        <p className='text-gray-500'>No collaboration data available</p>
      </div>
    );
  }

  return (
    <div className='w-full'>
      <h4 className='text-md font-medium text-gray-700 mb-3'>{title}</h4>
      <div className='relative h-64 bg-gradient-to-r from-red-50 via-purple-50 to-blue-50 rounded-lg p-6'>
        <div className='flex justify-between items-center h-full'>
          {/* Republican Side */}
          <div className='flex flex-col space-y-2'>
            <div className='w-12 h-12 bg-red-500 rounded-full flex items-center justify-center text-white font-bold'>
              R
            </div>
            <p className='text-xs text-center font-medium'>Republican</p>
          </div>

          {/* Bridge Builders in the middle */}
          <div className='flex-1 flex flex-col items-center space-y-2'>
            <div className='flex flex-wrap justify-center gap-2'>
              {bridgeBuilders.slice(0, 4).map((member, idx) => (
                <div
                  key={idx}
                  className='relative'
                  title={`${member.name} - ${(member.bipartisan_score * 100).toFixed(0)}% bipartisan`}
                >
                  <div
                    className='w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white'
                    style={{ backgroundColor: PARTY_COLORS[member.party] }}
                  >
                    {member.name
                      .split(' ')
                      .map(n => n[0])
                      .join('')
                      .substr(0, 2)}
                  </div>
                  {/* Connection lines */}
                  <div className='absolute top-4 left-0 w-full h-px bg-purple-300 opacity-50' />
                </div>
              ))}
            </div>
            <p className='text-xs text-center font-medium text-purple-700'>
              Bridge Builders
            </p>
          </div>

          {/* Democratic Side */}
          <div className='flex flex-col space-y-2'>
            <div className='w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold'>
              D
            </div>
            <p className='text-xs text-center font-medium'>Democratic</p>
          </div>
        </div>
      </div>
      <p className='text-xs text-gray-600 mt-2 text-center'>
        Lines represent cross-party collaboration relationships
      </p>
    </div>
  );
}

// Prop Types
MonthlyActivityChart.propTypes = {
  data: PropTypes.array,
  title: PropTypes.string,
};

PolicyAreasPieChart.propTypes = {
  republicanAreas: PropTypes.array,
  democraticAreas: PropTypes.array,
  title: PropTypes.string,
};

BipartisanTrendChart.propTypes = {
  data: PropTypes.array,
  title: PropTypes.string,
};

RankingBarChart.propTypes = {
  data: PropTypes.array,
  title: PropTypes.string,
  dataKey: PropTypes.string.isRequired,
  valueKey: PropTypes.string,
};

PartyUnityRadialChart.propTypes = {
  data: PropTypes.object,
  title: PropTypes.string,
};

MemberSpotlightCards.propTypes = {
  members: PropTypes.array,
  title: PropTypes.string.isRequired,
  scoreLabel: PropTypes.string.isRequired,
  scoreKey: PropTypes.string,
};

DivisiveVotesList.propTypes = {
  votes: PropTypes.array,
  title: PropTypes.string,
};

SimpleNetworkVisualization.propTypes = {
  bridgeBuilders: PropTypes.array,
  title: PropTypes.string,
};

export default {
  MonthlyActivityChart,
  PolicyAreasPieChart,
  BipartisanTrendChart,
  RankingBarChart,
  PartyUnityRadialChart,
  MemberSpotlightCards,
  DivisiveVotesList,
  SimpleNetworkVisualization,
};
