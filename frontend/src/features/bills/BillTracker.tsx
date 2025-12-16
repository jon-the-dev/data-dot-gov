import {
  FileText,
  Calendar,
  Users,
  Search,
  Filter,
  Download,
  ExternalLink,
  Clock,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

import DataService from '@/services/dataService';
import type { Bill, SearchFilters } from '@/types';

interface BillTrackerProps {
  embedded?: boolean;
  maxItems?: number;
}

// const BILL_STATUSES = [
//   'Introduced',
//   'Referred to Committee',
//   'Reported by Committee',
//   'Passed House',
//   'Passed Senate',
//   'Sent to President',
//   'Became Law',
//   'Failed'
// ];

export default function BillTracker({
  embedded = false,
  maxItems = 50,
}: BillTrackerProps) {
  const [bills, setBills] = useState<Bill[]>([]);
  const [filteredBills, setFilteredBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'sponsors'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    loadBills();
  }, []);

  useEffect(() => {
    applyFiltersAndSort();
  }, [bills, searchQuery, filters, sortBy, sortOrder]);

  const loadBills = async () => {
    try {
      setLoading(true);
      setError(null);

      const billsIndex = await DataService.loadBillsIndex();
      if (!(billsIndex as any)?.bills) {
        throw new Error('No bills data available');
      }

      const billsArray = Array.isArray((billsIndex as any).bills)
        ? ((billsIndex as any).bills as Bill[])
        : Object.values((billsIndex as any).bills as { [key: string]: Bill });

      setBills(billsArray);
    } catch (err) {
      console.error('Error loading bills:', err);
      setError('Failed to load bills data');
    } finally {
      setLoading(false);
    }
  };

  const applyFiltersAndSort = () => {
    let filtered = [...bills];

    // Text search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        bill =>
          bill.title?.toLowerCase().includes(query) ||
          bill.bill_id?.toLowerCase().includes(query) ||
          bill.subjects?.some(subject =>
            subject.toLowerCase().includes(query)
          ) ||
          bill.sponsors?.some(sponsor =>
            sponsor.name.toLowerCase().includes(query)
          )
      );
    }

    // Date range filter
    if (filters.dateRange) {
      const startDate = new Date(filters.dateRange.start);
      const endDate = new Date(filters.dateRange.end);
      filtered = filtered.filter(bill => {
        const billDate = new Date(bill.introducedDate || bill.updateDate);
        return billDate >= startDate && billDate <= endDate;
      });
    }

    // Category filter
    if (filters.category?.length) {
      filtered = filtered.filter(
        bill =>
          bill.subjects?.some(subject =>
            filters.category!.some(category =>
              subject.toLowerCase().includes(category.toLowerCase())
            )
          ) ||
          filters.category!.some(category =>
            bill.policyArea?.toLowerCase().includes(category.toLowerCase())
          )
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortBy) {
        case 'date':
          aValue = new Date(a.updateDate || a.introducedDate || 0);
          bValue = new Date(b.updateDate || b.introducedDate || 0);
          break;
        case 'title':
          aValue = a.title || '';
          bValue = b.title || '';
          break;
        case 'sponsors':
          aValue = (a.sponsors?.length || 0) + (a.cosponsors?.length || 0);
          bValue = (b.sponsors?.length || 0) + (b.cosponsors?.length || 0);
          break;
        default:
          return 0;
      }

      if (sortBy === 'date') {
        return sortOrder === 'desc' ? bValue - aValue : aValue - bValue;
      } else if (typeof aValue === 'string') {
        return sortOrder === 'desc'
          ? bValue.localeCompare(aValue)
          : aValue.localeCompare(bValue);
      } else {
        return sortOrder === 'desc' ? bValue - aValue : aValue - bValue;
      }
    });

    // Limit results if embedded
    if (embedded && maxItems) {
      filtered = filtered.slice(0, maxItems);
    }

    setFilteredBills(filtered);
  };

  const exportBills = async () => {
    try {
      const csvData = await DataService.exportData({
        format: 'csv',
        data: 'bills',
        filters,
      });

      const blob = new Blob([csvData], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bills-tracker-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting bills:', error);
    }
  };

  const getBillStatusColor = (status: string) => {
    const statusColors = {
      'Became Law': 'bg-green-100 text-green-800',
      'Passed House': 'bg-blue-100 text-blue-800',
      'Passed Senate': 'bg-blue-100 text-blue-800',
      'Sent to President': 'bg-purple-100 text-purple-800',
      'Reported by Committee': 'bg-yellow-100 text-yellow-800',
      'Referred to Committee': 'bg-gray-100 text-gray-800',
      Introduced: 'bg-gray-100 text-gray-800',
      Failed: 'bg-red-100 text-red-800',
    };
    return (
      statusColors[status as keyof typeof statusColors] ||
      'bg-gray-100 text-gray-800'
    );
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
    <div className='space-y-4'>
      {!embedded && (
        <>
          {/* Header */}
          <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
            <div>
              <h2 className='text-2xl font-bold text-gray-900'>Bill Tracker</h2>
              <p className='text-gray-600'>
                Track legislative progress and bill details
              </p>
            </div>
            <div className='flex gap-2'>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className='flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50'
              >
                <Filter size={16} />
                Filters
              </button>
              <button
                onClick={exportBills}
                className='flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700'
              >
                <Download size={16} />
                Export
              </button>
            </div>
          </div>

          {/* Search and Controls */}
          <div className='flex flex-col sm:flex-row gap-4'>
            <div className='relative flex-1'>
              <Search
                className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
                size={20}
              />
              <input
                type='text'
                placeholder='Search bills by title, ID, subject, or sponsor...'
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
              />
            </div>
            <div className='flex gap-2'>
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value as any)}
                className='border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
              >
                <option value='date'>Sort by Date</option>
                <option value='title'>Sort by Title</option>
                <option value='sponsors'>Sort by Sponsors</option>
              </select>
              <button
                onClick={() =>
                  setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
                }
                className='px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50'
              >
                {sortOrder === 'desc' ? '↓' : '↑'}
              </button>
            </div>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className='bg-white border border-gray-200 rounded-lg p-4 space-y-4'>
              <h3 className='text-sm font-medium text-gray-900'>
                Filter Bills
              </h3>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-2'>
                    Date Range
                  </label>
                  <div className='flex gap-2'>
                    <input
                      type='date'
                      value={filters.dateRange?.start || ''}
                      onChange={e =>
                        setFilters(prev => ({
                          ...prev,
                          dateRange: {
                            ...prev.dateRange,
                            start: e.target.value,
                            end: prev.dateRange?.end || '',
                          },
                        }))
                      }
                      className='flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                    />
                    <input
                      type='date'
                      value={filters.dateRange?.end || ''}
                      onChange={e =>
                        setFilters(prev => ({
                          ...prev,
                          dateRange: {
                            ...prev.dateRange,
                            end: e.target.value,
                            start: prev.dateRange?.start || '',
                          },
                        }))
                      }
                      className='flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                    />
                  </div>
                </div>
                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-2'>
                    Category Keywords
                  </label>
                  <input
                    type='text'
                    placeholder='healthcare, defense, education...'
                    value={filters.category?.join(', ') || ''}
                    onChange={e =>
                      setFilters(prev => ({
                        ...prev,
                        category: e.target.value
                          .split(',')
                          .map(s => s.trim())
                          .filter(Boolean),
                      }))
                    }
                    className='w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                  />
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Results Summary */}
      <div className='flex items-center justify-between bg-gray-50 px-4 py-3 rounded-lg'>
        <div className='flex items-center gap-2 text-sm text-gray-600'>
          <FileText size={16} />
          <span>
            Showing {filteredBills.length.toLocaleString()} of{' '}
            {bills.length.toLocaleString()} bills
          </span>
        </div>
      </div>

      {/* Bills List */}
      <div className='space-y-4'>
        {filteredBills.length > 0 ? (
          filteredBills.map(bill => (
            <div
              key={bill.bill_id}
              className='bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow'
            >
              <div className='flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4'>
                <div className='flex-1'>
                  <div className='flex items-start gap-3'>
                    <div className='flex-shrink-0'>
                      <FileText className='h-5 w-5 text-blue-600 mt-1' />
                    </div>
                    <div className='flex-1'>
                      <div className='flex items-center gap-2 mb-2'>
                        <Link
                          to={`/bills/${bill.type}${bill.bill_id}`}
                          className='text-lg font-semibold text-blue-600 hover:text-blue-800'
                        >
                          {bill.type} {bill.bill_id}
                        </Link>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${getBillStatusColor(bill.status || 'Introduced')}`}
                        >
                          {bill.status || 'Introduced'}
                        </span>
                      </div>
                      <h3 className='text-gray-900 font-medium mb-2 line-clamp-2'>
                        {bill.title}
                      </h3>
                      <div className='flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-3'>
                        <span className='flex items-center gap-1'>
                          <Calendar size={14} />
                          Introduced{' '}
                          {DataService.formatDate(bill.introducedDate)}
                        </span>
                        {bill.updateDate &&
                          bill.updateDate !== bill.introducedDate && (
                            <span className='flex items-center gap-1'>
                              <Clock size={14} />
                              Updated {DataService.formatDate(bill.updateDate)}
                            </span>
                          )}
                        {(bill.sponsors?.length || 0) +
                          (bill.cosponsors?.length || 0) >
                          0 && (
                          <span className='flex items-center gap-1'>
                            <Users size={14} />
                            {(bill.sponsors?.length || 0) +
                              (bill.cosponsors?.length || 0)}{' '}
                            sponsors
                          </span>
                        )}
                      </div>
                      {bill.subjects && bill.subjects.length > 0 && (
                        <div className='flex flex-wrap gap-1 mb-3'>
                          {bill.subjects.slice(0, 3).map((subject, index) => (
                            <span
                              key={index}
                              className='px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded'
                            >
                              {subject}
                            </span>
                          ))}
                          {bill.subjects.length > 3 && (
                            <span className='px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded'>
                              +{bill.subjects.length - 3} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <div className='flex gap-2'>
                  <Link
                    to={`/bills/${bill.type}${bill.bill_id}`}
                    className='flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors'
                  >
                    <FileText size={16} />
                    View Details
                  </Link>
                  <a
                    href={`https://congress.gov/bill/${bill.congress}th-congress/${bill.type?.toLowerCase()}-bill/${bill.bill_id}`}
                    target='_blank'
                    rel='noopener noreferrer'
                    className='flex items-center gap-2 px-3 py-2 bg-gray-50 text-gray-600 rounded-lg hover:bg-gray-100 transition-colors'
                  >
                    <ExternalLink size={16} />
                    Congress.gov
                  </a>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className='text-center py-8 text-gray-500'>
            <FileText size={48} className='mx-auto mb-4 text-gray-300' />
            <p>No bills found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
}
