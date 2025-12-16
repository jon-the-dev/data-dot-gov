import {
  Search,
  Filter,
  ChevronRight,
  Calendar,
  User,
  FileText,
  Clock,
  Check,
  Building,
} from 'lucide-react';
import PropTypes from 'prop-types';
import { useState, useEffect, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
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
} from 'recharts';

import DataService from '../services/dataService';

import BillProgressBar from './BillProgressBar';

function BillsAnalysis({ data }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [filteredBills, setFilteredBills] = useState([]);
  const [selectedBill, setSelectedBill] = useState(null);

  const { billsIndex } = data;

  // Status categorization function - define early to avoid temporal dead zone
  const categorizeStatus = status => {
    if (!status) return 'Unknown';

    if (status.includes('Became Public Law')) return 'Enacted';
    if (status.includes('Passed') || status.includes('agreed to'))
      return 'Passed';
    if (status.includes('Placed on') && status.includes('Calendar'))
      return 'On Calendar';
    if (status.includes('Referred to')) return 'In Committee';
    if (status.includes('Read twice and referred')) return 'In Committee';
    if (status.includes('Received in')) return 'Cross-Chamber';
    if (status.includes('Held at the desk')) return 'Held at Desk';
    if (status.includes('Introduced')) return 'Introduced';
    if (status.includes('ASSUMING FIRST SPONSOR')) return 'Administrative';
    if (status.includes('Motion to reconsider')) return 'Procedural';

    return 'Other';
  };

  // Calculate dashboard metrics
  const dashboardData = useMemo(() => {
    if (!billsIndex || (!billsIndex.records && !billsIndex.bills)) {
      return {
        totalBills: 0,
        billsByType: [],
        billsByStatus: [],
        recentActivity: [],
        topSponsors: [],
      };
    }

    const billsArray = billsIndex.records || billsIndex.bills || [];
    const bills = Array.isArray(billsArray)
      ? billsArray
      : Object.values(billsArray);

    // Bills by type
    const typeCounts = {};
    const statusCounts = {};
    const recentBills = [];

    bills.forEach(bill => {
      // Type counts
      typeCounts[bill.type] = (typeCounts[bill.type] || 0) + 1;

      // Status counts
      const status = bill.latest_action || bill.latestAction?.text;
      const category = categorizeStatus(status);
      statusCounts[category] = (statusCounts[category] || 0) + 1;

      // Recent activity (last 30 bills by update date)
      if (bill.updateDate || bill.last_updated) {
        recentBills.push(bill);
      }
    });

    // Sort recent bills by date
    recentBills.sort(
      (a, b) =>
        new Date(b.updateDate || b.last_updated || 0) -
        new Date(a.updateDate || a.last_updated || 0)
    );

    const billsByType = Object.entries(typeCounts)
      .sort((a, b) => b[1] - a[1])
      .map(([type, count]) => ({ name: type, value: count, count }));

    const billsByStatus = Object.entries(statusCounts)
      .sort((a, b) => b[1] - a[1])
      .map(([status, count]) => ({ name: status, value: count, count }));

    return {
      totalBills: bills.length,
      billsByType,
      billsByStatus,
      recentActivity: recentBills.slice(0, 10),
      topSponsors: [], // We don't have sponsor data in the index
    };
  }, [billsIndex]);

  const filterBills = useCallback(() => {
    if (!billsIndex || (!billsIndex.records && !billsIndex.bills)) {
      setFilteredBills([]);
      return;
    }

    let bills = billsIndex?.records || billsIndex?.bills || [];
    bills = Array.isArray(bills) ? bills : Object.values(bills);

    // Apply search filter
    if (searchTerm) {
      bills = bills.filter(
        bill =>
          (bill.title &&
            bill.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (bill.bill_id &&
            bill.bill_id
              .toString()
              .toLowerCase()
              .includes(searchTerm.toLowerCase())) ||
          (bill.type &&
            bill.type.toLowerCase().includes(searchTerm.toLowerCase())) ||
          (bill.number && bill.number.toString().includes(searchTerm))
      );
    }

    // Apply type filter
    if (selectedType !== 'all') {
      bills = bills.filter(bill => bill.type === selectedType);
    }

    // Apply status filter - now using categorized statuses
    if (selectedStatus !== 'all') {
      bills = bills.filter(bill => {
        const status = bill.latest_action || bill.latestAction?.text;
        const category = categorizeStatus(status);
        return category === selectedStatus;
      });
    }

    // Sort by date
    bills.sort(
      (a, b) => new Date(b.updateDate || 0) - new Date(a.updateDate || 0)
    );

    setFilteredBills(bills);
  }, [searchTerm, selectedType, selectedStatus, billsIndex, categorizeStatus]);

  useEffect(() => {
    filterBills();
  }, [filterBills]);

  const getBillTypes = () => {
    if (!billsIndex || (!billsIndex.records && !billsIndex.bills)) return [];
    const billsArray = billsIndex.records || billsIndex.bills;
    const bills = Array.isArray(billsArray)
      ? billsArray
      : Object.values(billsArray);
    const types = new Set(bills.map(b => b.type).filter(Boolean));
    return Array.from(types);
  };

  // (categorizeStatus function moved above for proper initialization order)

  const getBillStatuses = () => {
    if (!billsIndex || (!billsIndex.records && !billsIndex.bills)) return [];
    const billsArray = billsIndex.records || billsIndex.bills;
    const bills = Array.isArray(billsArray)
      ? billsArray
      : Object.values(billsArray);

    const statusCounts = {};
    bills.forEach(bill => {
      const status = bill.latest_action || bill.latestAction?.text;
      const category = categorizeStatus(status);
      statusCounts[category] = (statusCounts[category] || 0) + 1;
    });

    return Object.entries(statusCounts)
      .sort((a, b) => b[1] - a[1])
      .map(([status, count]) => ({ status, count }));
  };

  const getDetailedStatuses = () => {
    if (!billsIndex || (!billsIndex.records && !billsIndex.bills)) return [];
    const billsArray = billsIndex.records || billsIndex.bills;
    const bills = Array.isArray(billsArray)
      ? billsArray
      : Object.values(billsArray);

    const statuses = new Set(
      bills.map(b => b.latest_action || b.latestAction?.text).filter(Boolean)
    );
    return Array.from(statuses);
  };

  const BillCard = ({ bill }) => {
    // Handle both API response formats
    const billNumber = bill.number || bill.bill_id;
    const billType = bill.type;
    const billTitle = bill.title || 'Untitled Bill';
    const billId = bill.id || `${bill.type}${bill.number || bill.bill_id}`;

    return (
      <Link
        to={`/bills/${billId}`}
        className='block bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow'
      >
        <div className='flex items-start justify-between'>
          <div className='flex-1'>
            <div className='flex items-center gap-2 mb-2'>
              <span className='text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded'>
                {billType && billNumber
                  ? `${billType} ${billNumber}`
                  : billId || 'Unknown'}
              </span>
              {billType && (
                <span className='text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded'>
                  {billType}
                </span>
              )}
            </div>
            <h3 className='text-sm font-medium text-gray-900 line-clamp-2'>
              {billTitle}
            </h3>
            <div className='mt-2 space-y-1'>
              {(bill.latest_action || bill.latestAction?.text) && (
                <div className='text-xs text-gray-600'>
                  <span>{bill.latest_action || bill.latestAction?.text}</span>
                </div>
              )}
              {(bill.originChamber || bill.origin_chamber) && (
                <div className='flex items-center gap-1 text-xs text-gray-600'>
                  <User size={12} />
                  <span>{bill.originChamber || bill.origin_chamber}</span>
                </div>
              )}
              {(bill.updateDate || bill.update_date) && (
                <div className='flex items-center gap-1 text-xs text-gray-600'>
                  <Calendar size={12} />
                  <span>
                    {DataService.formatDate(
                      bill.updateDate || bill.update_date
                    )}
                  </span>
                </div>
              )}
            </div>
            <div className='mt-3 pt-2 border-t border-gray-100'>
              <BillProgressBar bill={bill} compact={true} />
            </div>
          </div>
          <ChevronRight className='text-gray-400 flex-shrink-0' size={20} />
        </div>
      </Link>
    );
  };

  // Dashboard Components
  const StatCard = ({ icon: Icon, title, value, subtitle, color }) => (
    <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
      <div className='flex items-center justify-between'>
        <div>
          <p className='text-sm font-medium text-gray-600'>{title}</p>
          <p className={`text-2xl font-bold mt-1 ${color || 'text-gray-900'}`}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {subtitle && <p className='text-xs text-gray-500 mt-1'>{subtitle}</p>}
        </div>
        <div
          className={`p-3 rounded-lg ${
            color
              ? color.replace('text-', 'bg-').replace('900', '100')
              : 'bg-gray-100'
          }`}
        >
          <Icon className={`h-6 w-6 ${color || 'text-gray-600'}`} />
        </div>
      </div>
    </div>
  );

  const getStatusColor = status => {
    const colors = {
      Enacted: '#10B981',
      Passed: '#059669',
      'On Calendar': '#F59E0B',
      'In Committee': '#6366F1',
      'Cross-Chamber': '#8B5CF6',
      'Held at Desk': '#EF4444',
      Introduced: '#06B6D4',
      Administrative: '#6B7280',
      Procedural: '#9CA3AF',
      Other: '#71717A',
    };
    return colors[status] || '#6B7280';
  };

  const getBillTypeColor = type => {
    const colors = {
      HR: '#3B82F6',
      S: '#EF4444',
      HJRES: '#10B981',
      SJRES: '#F59E0B',
      HRES: '#8B5CF6',
      SRES: '#06B6D4',
      HCONRES: '#EC4899',
      SCONRES: '#F97316',
    };
    return colors[type] || '#6B7280';
  };

  const StatusFilterSelector = () => {
    const statusOptions = getBillStatuses();
    const [showDetails, setShowDetails] = useState(false);
    const detailedStatuses = getDetailedStatuses();

    return (
      <div className='relative'>
        <select
          className='px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[200px]'
          value={selectedStatus}
          onChange={e => setSelectedStatus(e.target.value)}
        >
          <option value='all'>All Status ({dashboardData.totalBills})</option>
          {statusOptions.map(({ status, count }) => (
            <option key={status} value={status}>
              {status} ({count})
            </option>
          ))}
        </select>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className='ml-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors'
          title='View detailed statuses'
        >
          <Filter size={16} />
        </button>

        {showDetails && (
          <div className='absolute top-full left-0 mt-1 w-96 max-h-64 overflow-y-auto bg-white border border-gray-200 rounded-lg shadow-lg z-10'>
            <div className='p-3 border-b border-gray-200'>
              <h4 className='font-medium text-gray-900'>
                Detailed Status Breakdown
              </h4>
            </div>
            <div className='p-2'>
              {detailedStatuses.slice(0, 20).map((status, index) => (
                <div
                  key={index}
                  className='px-2 py-1 text-xs text-gray-600 hover:bg-gray-50 rounded'
                >
                  {status.length > 80
                    ? `${status.substring(0, 80)}...`
                    : status}
                </div>
              ))}
              {detailedStatuses.length > 20 && (
                <div className='px-2 py-1 text-xs text-gray-400'>
                  ...and {detailedStatuses.length - 20} more
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const BillDetails = ({ bill }) => (
    <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
      <div className='p-6 border-b border-gray-200'>
        <button
          onClick={() => setSelectedBill(null)}
          className='text-blue-600 hover:text-blue-800 text-sm font-medium mb-4'
        >
          ← Back to list
        </button>
        <div className='space-y-3'>
          <div className='flex items-center gap-2'>
            <span className='text-sm font-semibold text-blue-600 bg-blue-50 px-3 py-1 rounded'>
              {bill.number || 'Unknown'}
            </span>
            {bill.type && (
              <span className='text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded'>
                {bill.type}
              </span>
            )}
            {bill.status && (
              <span className='text-sm text-green-600 bg-green-50 px-3 py-1 rounded'>
                {bill.status}
              </span>
            )}
          </div>
          <h2 className='text-xl font-bold text-gray-900'>
            {bill.title || 'Untitled Bill'}
          </h2>
        </div>
      </div>

      <div className='p-6 space-y-6'>
        <div>
          <h3 className='text-sm font-semibold text-gray-700 mb-2'>
            Bill Information
          </h3>
          <div className='grid grid-cols-2 gap-4'>
            {bill.sponsor && (
              <div>
                <p className='text-xs text-gray-500'>Sponsor</p>
                <p className='text-sm font-medium text-gray-900'>
                  {bill.sponsor}
                </p>
              </div>
            )}
            {bill.introduced_date && (
              <div>
                <p className='text-xs text-gray-500'>Introduced</p>
                <p className='text-sm font-medium text-gray-900'>
                  {DataService.formatDate(bill.introduced_date)}
                </p>
              </div>
            )}
            {bill.committees && (
              <div className='col-span-2'>
                <p className='text-xs text-gray-500'>Committees</p>
                <p className='text-sm font-medium text-gray-900'>
                  {bill.committees}
                </p>
              </div>
            )}
          </div>
        </div>

        {bill.summary && (
          <div>
            <h3 className='text-sm font-semibold text-gray-700 mb-2'>
              Summary
            </h3>
            <p className='text-sm text-gray-600'>{bill.summary}</p>
          </div>
        )}

        {bill.actions && bill.actions.length > 0 && (
          <div>
            <h3 className='text-sm font-semibold text-gray-700 mb-2'>
              Recent Actions
            </h3>
            <div className='space-y-2'>
              {bill.actions.slice(0, 5).map((action, index) => (
                <div key={index} className='flex gap-3 text-sm'>
                  <span className='text-gray-500'>
                    {DataService.formatDate(action.date)}
                  </span>
                  <span className='text-gray-700'>{action.description}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className='pt-4 border-t border-gray-200'>
          <div className='flex gap-3'>
            <button className='px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700'>
              View Full Details
            </button>
            <button className='px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded hover:bg-gray-50'>
              Track Voting
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className='space-y-6'>
      <div>
        <h2 className='text-2xl font-bold text-gray-900 mb-4'>
          Bills Analysis
        </h2>
        <p className='text-gray-600'>
          Track and analyze legislation in the 118th Congress
        </p>
      </div>

      {selectedBill ? (
        <BillDetails bill={selectedBill} />
      ) : (
        <>
          {/* Dashboard Overview */}
          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6'>
            <StatCard
              icon={FileText}
              title='Total Bills'
              value={dashboardData.totalBills}
              subtitle='118th Congress'
              color='text-blue-600'
            />
            <StatCard
              icon={Check}
              title='Enacted Laws'
              value={
                dashboardData.billsByStatus.find(s => s.name === 'Enacted')
                  ?.count || 0
              }
              subtitle='Became Public Law'
              color='text-green-600'
            />
            <StatCard
              icon={Building}
              title='In Committee'
              value={
                dashboardData.billsByStatus.find(s => s.name === 'In Committee')
                  ?.count || 0
              }
              subtitle='Under Review'
              color='text-indigo-600'
            />
            <StatCard
              icon={Clock}
              title='On Calendar'
              value={
                dashboardData.billsByStatus.find(s => s.name === 'On Calendar')
                  ?.count || 0
              }
              subtitle='Scheduled'
              color='text-amber-600'
            />
          </div>

          {/* Charts Section */}
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6'>
            {/* Bills by Type Chart */}
            <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                Bills by Type
              </h3>
              <div className='h-64'>
                <ResponsiveContainer width='100%' height='100%'>
                  <PieChart>
                    <Pie
                      data={dashboardData.billsByType}
                      cx='50%'
                      cy='50%'
                      outerRadius={80}
                      dataKey='value'
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {dashboardData.billsByType.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={getBillTypeColor(entry.name)}
                        />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value, name) => [value, name]} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Bills by Status Chart */}
            <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
              <h3 className='text-lg font-semibold text-gray-900 mb-4'>
                Bills by Status
              </h3>
              <div className='h-64'>
                <ResponsiveContainer width='100%' height='100%'>
                  <BarChart
                    data={dashboardData.billsByStatus.slice(0, 8)}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray='3 3' />
                    <XAxis
                      dataKey='name'
                      angle={-45}
                      textAnchor='end'
                      height={100}
                      fontSize={12}
                    />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey='value' radius={[4, 4, 0, 0]}>
                      {dashboardData.billsByStatus
                        .slice(0, 8)
                        .map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={getStatusColor(entry.name)}
                          />
                        ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4'>
              Recent Activity
            </h3>
            <div className='space-y-3'>
              {dashboardData.recentActivity.map((bill, index) => (
                <Link
                  key={bill.id || index}
                  to={`/bills/${bill.id}`}
                  className='flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg border border-gray-100'
                >
                  <div className='flex items-center space-x-3'>
                    <span className='text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded'>
                      {bill.type} {bill.number}
                    </span>
                    <div>
                      <p className='text-sm font-medium text-gray-900 line-clamp-1'>
                        {bill.title}
                      </p>
                      <p className='text-xs text-gray-500'>
                        {DataService.formatDate(
                          bill.updateDate || bill.last_updated
                        )}
                      </p>
                    </div>
                  </div>
                  <div className='flex items-center'>
                    <span
                      className='text-xs px-2 py-1 rounded-full'
                      style={{
                        backgroundColor: `${getStatusColor(
                          categorizeStatus(bill.latest_action)
                        )}20`,
                        color: getStatusColor(
                          categorizeStatus(bill.latest_action)
                        ),
                      }}
                    >
                      {categorizeStatus(bill.latest_action)}
                    </span>
                    <ChevronRight className='text-gray-400 ml-2' size={16} />
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Search and Filters */}
          <div className='bg-white p-4 rounded-lg shadow-sm border border-gray-200'>
            <div className='flex flex-col md:flex-row gap-4'>
              <div className='flex-1'>
                <div className='relative'>
                  <Search
                    className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
                    size={20}
                  />
                  <input
                    type='text'
                    placeholder='Search bills by title, number, or sponsor...'
                    className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
              <div className='flex gap-2'>
                <select
                  className='px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                  value={selectedType}
                  onChange={e => setSelectedType(e.target.value)}
                >
                  <option value='all'>All Types</option>
                  {getBillTypes().map(type => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
                <StatusFilterSelector />
              </div>
            </div>
          </div>

          {/* Results Summary */}
          <div className='flex items-center justify-between'>
            <p className='text-sm text-gray-600'>
              Found {filteredBills.length} bills
              {(searchTerm ||
                selectedType !== 'all' ||
                selectedStatus !== 'all') && (
                <span className='ml-2'>
                  <button
                    onClick={() => {
                      setSearchTerm('');
                      setSelectedType('all');
                      setSelectedStatus('all');
                    }}
                    className='text-blue-600 hover:text-blue-800 text-xs'
                  >
                    Clear filters
                  </button>
                </span>
              )}
            </p>
            <div className='flex items-center space-x-2'>
              {selectedStatus !== 'all' && (
                <span className='text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded'>
                  Status: {selectedStatus}
                </span>
              )}
              {selectedType !== 'all' && (
                <span className='text-xs bg-green-100 text-green-800 px-2 py-1 rounded'>
                  Type: {selectedType}
                </span>
              )}
            </div>
          </div>

          {/* Bills Grid */}
          {filteredBills.length > 0 ? (
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              {filteredBills.map((bill, index) => (
                <BillCard key={bill.id || index} bill={bill} />
              ))}
            </div>
          ) : (
            <div className='bg-gray-50 border border-gray-200 rounded-lg p-8 text-center'>
              <p className='text-gray-500'>
                {searchTerm ||
                selectedType !== 'all' ||
                selectedStatus !== 'all'
                  ? 'No bills found matching your criteria'
                  : 'No bill data available'}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

BillsAnalysis.propTypes = {
  data: PropTypes.shape({
    billsIndex: PropTypes.shape({
      records: PropTypes.object,
      bills: PropTypes.oneOfType([PropTypes.array, PropTypes.object]),
    }),
  }).isRequired,
};

export default BillsAnalysis;
