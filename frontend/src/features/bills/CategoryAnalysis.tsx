import { TrendingUp, Filter, Download, BarChart3 } from 'lucide-react';
import { useState, useEffect } from 'react';
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
// import type { BillCategory } from '@/types';

interface CategoryData {
  category: string;
  total: number;
  democratic: number;
  republican: number;
  independent: number;
  democraticPercentage: number;
  republicanPercentage: number;
  independentPercentage: number;
}

export default function CategoryAnalysis() {
  const [categories, setCategories] = useState<CategoryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'absolute' | 'percentage'>(
    'absolute'
  );
  const [chartType, setChartType] = useState<'bar' | 'pie'>('bar');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    loadCategoryData();
  }, []);

  const loadCategoryData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [billCategories, comprehensiveAnalysis] = await Promise.all([
        DataService.loadBillCategories(),
        DataService.loadComprehensiveAnalysis(),
      ]);

      if (
        !billCategories &&
        !comprehensiveAnalysis?.analyses?.bill_categories
      ) {
        throw new Error('No category data available');
      }

      // Use comprehensive analysis data if available, otherwise process bill categories
      const categoryData =
        (comprehensiveAnalysis as any)?.analyses?.bill_categories ||
        processBillCategories(billCategories);

      setCategories(formatCategoryData(categoryData));
    } catch (err) {
      console.error('Error loading category data:', err);
      setError('Failed to load bill category analysis');
    } finally {
      setLoading(false);
    }
  };

  const processBillCategories = (billCategories: any) => {
    if (!billCategories) return {};

    const processed: any = {};

    Object.entries(billCategories).forEach(
      ([category, data]: [string, any]) => {
        if (data.bills && Array.isArray(data.bills)) {
          const partyBreakdown = {
            Democratic: 0,
            Republican: 0,
            Independent: 0,
          };

          data.bills.forEach((bill: any) => {
            if (bill.sponsors) {
              bill.sponsors.forEach((sponsor: any) => {
                const party = DataService.normalizeParty(sponsor.party);
                if (partyBreakdown.hasOwnProperty(party)) {
                  partyBreakdown[party as keyof typeof partyBreakdown]++;
                }
              });
            }
          });

          processed[category] = {
            total_bills: data.bills.length,
            party_breakdown: partyBreakdown,
            keywords: data.keywords || [],
          };
        }
      }
    );

    return processed;
  };

  const formatCategoryData = (rawData: any): CategoryData[] => {
    if (!rawData) return [];

    return Object.entries(rawData)
      .map(([category, data]: [string, any]) => {
        const total = data.total_bills || 0;
        const democratic = data.party_breakdown?.Democratic || 0;
        const republican = data.party_breakdown?.Republican || 0;
        const independent = data.party_breakdown?.Independent || 0;

        return {
          category: category
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase()),
          total,
          democratic,
          republican,
          independent,
          democraticPercentage: total > 0 ? (democratic / total) * 100 : 0,
          republicanPercentage: total > 0 ? (republican / total) * 100 : 0,
          independentPercentage: total > 0 ? (independent / total) * 100 : 0,
        };
      })
      .sort((a, b) => b.total - a.total);
  };

  const getChartData = () => {
    if (viewMode === 'percentage') {
      return categories.map(cat => ({
        ...cat,
        Democratic: parseFloat(cat.democraticPercentage.toFixed(1)),
        Republican: parseFloat(cat.republicanPercentage.toFixed(1)),
        Independent: parseFloat(cat.independentPercentage.toFixed(1)),
      }));
    } else {
      return categories.map(cat => ({
        ...cat,
        Democratic: cat.democratic,
        Republican: cat.republican,
        Independent: cat.independent,
      }));
    }
  };

  const getPieChartData = () => {
    if (!selectedCategory) return [];

    const category = categories.find(c => c.category === selectedCategory);
    if (!category) return [];

    return [
      {
        name: 'Democratic',
        value: category.democratic,
        color: DataService.getPartyColor('Democratic'),
      },
      {
        name: 'Republican',
        value: category.republican,
        color: DataService.getPartyColor('Republican'),
      },
      {
        name: 'Independent',
        value: category.independent,
        color: DataService.getPartyColor('Independent'),
      },
    ].filter(item => item.value > 0);
  };

  const exportData = async () => {
    try {
      const csvData = categories.map(cat => ({
        Category: cat.category,
        'Total Bills': cat.total,
        'Democratic Bills': cat.democratic,
        'Republican Bills': cat.republican,
        'Independent Bills': cat.independent,
        'Democratic %': cat.democraticPercentage.toFixed(1),
        'Republican %': cat.republicanPercentage.toFixed(1),
        'Independent %': cat.independentPercentage.toFixed(1),
      }));

      const csv = [
        Object.keys(csvData[0] || {}).join(','),
        ...csvData.map(row => Object.values(row).join(',')),
      ].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bill-categories-analysis-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload?.length) {
      return (
        <div className='bg-white p-4 border border-gray-200 rounded-lg shadow-lg'>
          <p className='font-semibold text-gray-900 mb-2'>{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className='text-sm' style={{ color: entry.color }}>
              <span className='font-medium'>{entry.dataKey}:</span>{' '}
              {viewMode === 'percentage'
                ? `${entry.value}%`
                : entry.value.toLocaleString()}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600' />
      </div>
    );
  }

  if (error) {
    return (
      <div className='bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg'>
        {error}
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h2 className='text-2xl font-bold text-gray-900'>
            Bill Category Analysis
          </h2>
          <p className='text-gray-600'>
            Analyze bill distribution by policy area and party
          </p>
        </div>
        <div className='flex gap-2'>
          <button
            onClick={exportData}
            className='flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700'
          >
            <Download size={16} />
            Export
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className='flex flex-col sm:flex-row gap-4'>
        <div className='flex bg-gray-100 rounded-lg p-1'>
          <button
            onClick={() => setViewMode('absolute')}
            className={`px-3 py-2 text-sm rounded transition-colors ${
              viewMode === 'absolute'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Absolute Numbers
          </button>
          <button
            onClick={() => setViewMode('percentage')}
            className={`px-3 py-2 text-sm rounded transition-colors ${
              viewMode === 'percentage'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Percentages
          </button>
        </div>

        <div className='flex bg-gray-100 rounded-lg p-1'>
          <button
            onClick={() => setChartType('bar')}
            className={`px-3 py-2 text-sm rounded transition-colors ${
              chartType === 'bar'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Bar Chart
          </button>
          <button
            onClick={() => setChartType('pie')}
            className={`px-3 py-2 text-sm rounded transition-colors ${
              chartType === 'pie'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Pie Chart
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm font-medium text-gray-600'>
                Total Categories
              </p>
              <p className='text-2xl font-bold text-gray-900 mt-1'>
                {categories.length}
              </p>
            </div>
            <div className='p-3 rounded-lg bg-blue-100'>
              <BarChart3 className='h-6 w-6 text-blue-600' />
            </div>
          </div>
        </div>

        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm font-medium text-gray-600'>Total Bills</p>
              <p className='text-2xl font-bold text-gray-900 mt-1'>
                {categories
                  .reduce((sum, cat) => sum + cat.total, 0)
                  .toLocaleString()}
              </p>
            </div>
            <div className='p-3 rounded-lg bg-green-100'>
              <TrendingUp className='h-6 w-6 text-green-600' />
            </div>
          </div>
        </div>

        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm font-medium text-gray-600'>Top Category</p>
              <p className='text-lg font-bold text-gray-900 mt-1'>
                {categories[0]?.category || 'N/A'}
              </p>
              <p className='text-xs text-gray-500'>
                {categories[0]?.total.toLocaleString()} bills
              </p>
            </div>
            <div className='p-3 rounded-lg bg-purple-100'>
              <Filter className='h-6 w-6 text-purple-600' />
            </div>
          </div>
        </div>

        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-sm font-medium text-gray-600'>
                Avg per Category
              </p>
              <p className='text-2xl font-bold text-gray-900 mt-1'>
                {categories.length > 0
                  ? Math.round(
                      categories.reduce((sum, cat) => sum + cat.total, 0) /
                        categories.length
                    )
                  : 0}
              </p>
            </div>
            <div className='p-3 rounded-lg bg-yellow-100'>
              <BarChart3 className='h-6 w-6 text-yellow-600' />
            </div>
          </div>
        </div>
      </div>

      {/* Main Chart */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
        <h3 className='text-lg font-semibold text-gray-900 mb-4'>
          Bills by Category and Party{' '}
          {viewMode === 'percentage' ? '(%)' : '(Count)'}
        </h3>

        {chartType === 'pie' && (
          <div className='mb-4'>
            <label className='block text-sm font-medium text-gray-700 mb-2'>
              Select Category for Pie Chart
            </label>
            <select
              value={selectedCategory || ''}
              onChange={e => setSelectedCategory(e.target.value || null)}
              className='border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            >
              <option value=''>Select a category...</option>
              {categories.map(cat => (
                <option key={cat.category} value={cat.category}>
                  {cat.category} ({cat.total} bills)
                </option>
              ))}
            </select>
          </div>
        )}

        <div style={{ height: 500 }}>
          <ResponsiveContainer width='100%' height='100%'>
            {chartType === 'pie' && selectedCategory ? (
              <PieChart>
                <Pie
                  data={getPieChartData()}
                  cx='50%'
                  cy='50%'
                  innerRadius={80}
                  outerRadius={160}
                  paddingAngle={5}
                  dataKey='value'
                >
                  {getPieChartData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, name: string) => [
                    `${value.toLocaleString()} bills`,
                    name,
                  ]}
                />
                <Legend />
              </PieChart>
            ) : (
              <BarChart data={getChartData()}>
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis
                  dataKey='category'
                  tick={{ fontSize: 12 }}
                  interval={0}
                  angle={-45}
                  textAnchor='end'
                  height={100}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  label={{
                    value:
                      viewMode === 'percentage'
                        ? 'Percentage'
                        : 'Number of Bills',
                    angle: -90,
                    position: 'insideLeft',
                  }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar
                  dataKey='Democratic'
                  stackId='a'
                  fill={DataService.getPartyColor('Democratic')}
                />
                <Bar
                  dataKey='Republican'
                  stackId='a'
                  fill={DataService.getPartyColor('Republican')}
                />
                <Bar
                  dataKey='Independent'
                  stackId='a'
                  fill={DataService.getPartyColor('Independent')}
                />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Category Details Table */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden'>
        <div className='px-6 py-4 border-b border-gray-200'>
          <h3 className='text-lg font-semibold text-gray-900'>
            Category Details
          </h3>
        </div>
        <div className='overflow-x-auto'>
          <table className='w-full'>
            <thead className='bg-gray-50'>
              <tr>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Category
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Total Bills
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Democratic
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Republican
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Independent
                </th>
                <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                  Distribution
                </th>
              </tr>
            </thead>
            <tbody className='bg-white divide-y divide-gray-200'>
              {categories.map(category => (
                <tr key={category.category} className='hover:bg-gray-50'>
                  <td className='px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900'>
                    {category.category}
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                    {category.total.toLocaleString()}
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                    {category.democratic} (
                    {category.democraticPercentage.toFixed(1)}%)
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                    {category.republican} (
                    {category.republicanPercentage.toFixed(1)}%)
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                    {category.independent} (
                    {category.independentPercentage.toFixed(1)}%)
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <div className='flex w-full bg-gray-200 rounded-full h-2'>
                      <div
                        className='bg-blue-500 h-2 rounded-l-full'
                        style={{ width: `${category.democraticPercentage}%` }}
                      />
                      <div
                        className='bg-red-500 h-2'
                        style={{ width: `${category.republicanPercentage}%` }}
                      />
                      <div
                        className='bg-purple-500 h-2 rounded-r-full'
                        style={{ width: `${category.independentPercentage}%` }}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
