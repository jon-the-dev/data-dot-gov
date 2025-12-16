import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

import DataService from '@/services/dataService';
import type { ChartProps } from '@/types';

interface PartyUnityData {
  name: string;
  party: string;
  partyUnityScore: number;
  totalVotes: number;
  crossPartyVotes: number;
}

interface PartyUnityChartProps extends Omit<ChartProps, 'data'> {
  data: PartyUnityData[];
  chartType?: 'bar' | 'pie';
  showComparison?: boolean;
}

export default function PartyUnityChart({
  data,
  title = 'Party Unity Scores',
  height = 400,
  showLegend = true,
  chartType = 'bar',
  showComparison = false,
}: PartyUnityChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload?.length) {
      const data = payload[0].payload;
      return (
        <div className='bg-white p-4 border border-gray-200 rounded-lg shadow-lg'>
          <p className='font-semibold text-gray-900'>{label}</p>
          <p className='text-sm text-gray-600 mb-2'>
            {DataService.getPartyLabel(data.party)}
          </p>
          <div className='space-y-1'>
            <p className='text-sm'>
              <span className='font-medium'>Party Unity:</span>{' '}
              {DataService.formatNumber(data.partyUnityScore)}%
            </p>
            <p className='text-sm'>
              <span className='font-medium'>Total Votes:</span>{' '}
              {data.totalVotes.toLocaleString()}
            </p>
            <p className='text-sm'>
              <span className='font-medium'>Cross-Party Votes:</span>{' '}
              {data.crossPartyVotes}
            </p>
            <p className='text-sm'>
              <span className='font-medium'>Party Line Votes:</span>{' '}
              {(data.totalVotes - data.crossPartyVotes).toLocaleString()}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  const prepareBarChartData = () =>
    data.map(member => ({
      ...member,
      displayName: member.name.split(' ').pop() || member.name, // Show last name for space
    }));

  const preparePieChartData = () => {
    if (data.length === 0) return [];

    const member = data[0]; // For single member view
    if (!member) return [];

    return [
      {
        name: 'Party Line Votes',
        value: member.totalVotes - member.crossPartyVotes,
        color: DataService.getPartyColor(member.party),
      },
      {
        name: 'Cross-Party Votes',
        value: member.crossPartyVotes,
        color: '#94A3B8',
      },
    ];
  };

  const prepareComparisonData = () => {
    if (!showComparison || data.length === 0) return [];

    // Calculate party averages (this would ideally come from the API)
    const partyAverages = {
      Democratic: 85.2,
      Republican: 88.4,
      Independent: 75.8,
    };

    return data.map(member => ({
      ...member,
      displayName: member.name.split(' ').pop() || member.name,
      partyAverage:
        partyAverages[
          DataService.normalizeParty(member.party) as keyof typeof partyAverages
        ] || 80,
    }));
  };

  if (data.length === 0) {
    return (
      <div className='flex items-center justify-center h-64 bg-gray-50 rounded-lg'>
        <p className='text-gray-500'>No data available</p>
      </div>
    );
  }

  return (
    <div className='space-y-4'>
      {title && (
        <h3 className='text-lg font-semibold text-gray-900'>{title}</h3>
      )}

      {/* Chart Type Toggle */}
      {data.length === 1 && (
        <div className='flex justify-end'>
          <div className='flex bg-gray-100 rounded-lg p-1'>
            <button
              onClick={() => {
                /* Would need to be controlled from parent */
              }}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                chartType === 'bar'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Bar Chart
            </button>
            <button
              onClick={() => {
                /* Would need to be controlled from parent */
              }}
              className={`px-3 py-1 text-sm rounded transition-colors ${
                chartType === 'pie'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Pie Chart
            </button>
          </div>
        </div>
      )}

      <div style={{ height }}>
        <ResponsiveContainer width='100%' height='100%'>
          {chartType === 'pie' && data.length === 1 ? (
            <PieChart>
              <Pie
                data={preparePieChartData()}
                cx='50%'
                cy='50%'
                innerRadius={60}
                outerRadius={120}
                paddingAngle={5}
                dataKey='value'
              >
                {preparePieChartData().map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => [value.toLocaleString(), 'Votes']}
              />
              {showLegend && <Legend />}
            </PieChart>
          ) : showComparison ? (
            <BarChart data={prepareComparisonData()}>
              <CartesianGrid strokeDasharray='3 3' />
              <XAxis
                dataKey='displayName'
                tick={{ fontSize: 12 }}
                interval={0}
                angle={-45}
                textAnchor='end'
                height={60}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 12 }}
                label={{
                  value: 'Unity Score (%)',
                  angle: -90,
                  position: 'insideLeft',
                }}
              />
              <Tooltip content={<CustomTooltip />} />
              {showLegend && <Legend />}
              <Bar
                dataKey='partyUnityScore'
                name='Member Score'
                fill='#3B82F6'
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey='partyAverage'
                name='Party Average'
                fill='#94A3B8'
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          ) : (
            <BarChart data={prepareBarChartData()}>
              <CartesianGrid strokeDasharray='3 3' />
              <XAxis
                dataKey='displayName'
                tick={{ fontSize: 12 }}
                interval={0}
                angle={data.length > 5 ? -45 : 0}
                textAnchor={data.length > 5 ? 'end' : 'middle'}
                height={data.length > 5 ? 60 : 30}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 12 }}
                label={{
                  value: 'Unity Score (%)',
                  angle: -90,
                  position: 'insideLeft',
                }}
              />
              <Tooltip content={<CustomTooltip />} />
              {showLegend && <Legend />}
              <Bar
                dataKey='partyUnityScore'
                name='Party Unity Score'
                radius={[4, 4, 0, 0]}
                fill='#3B82F6'
              />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      {data.length === 1 && data[0] && (
        <div className='grid grid-cols-3 gap-4 pt-4 border-t border-gray-200'>
          <div className='text-center'>
            <p className='text-2xl font-bold text-gray-900'>
              {DataService.formatNumber(data[0].partyUnityScore)}%
            </p>
            <p className='text-sm text-gray-600'>Party Unity</p>
          </div>
          <div className='text-center'>
            <p className='text-2xl font-bold text-gray-900'>
              {data[0].totalVotes.toLocaleString()}
            </p>
            <p className='text-sm text-gray-600'>Total Votes</p>
          </div>
          <div className='text-center'>
            <p className='text-2xl font-bold text-gray-900'>
              {data[0].crossPartyVotes}
            </p>
            <p className='text-sm text-gray-600'>Cross-Party</p>
          </div>
        </div>
      )}
    </div>
  );
}
