import { clsx } from 'clsx';
import { ChevronUp, ChevronDown, Search, Download } from 'lucide-react';
import { useState, useMemo } from 'react';

import type { TableProps } from '@/types';

interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: any, row: any) => React.ReactNode;
}

interface DataTableProps extends TableProps {
  columns: TableColumn[];
  title?: string;
  searchable?: boolean;
  exportable?: boolean;
  pagination?: boolean;
  pageSize?: number;
  emptyMessage?: string;
}

export default function DataTable({
  data,
  columns,
  title,
  loading = false,
  onRowClick,
  sortable = true,
  searchable = false,
  exportable = false,
  pagination = false,
  pageSize = 10,
  emptyMessage = 'No data available',
}: DataTableProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  // Filter and sort data
  const processedData = useMemo(() => {
    let filtered = data;

    // Search filtering
    if (searchable && searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = data.filter(row =>
        columns.some(col => {
          const value = row[col.key];
          return value?.toString().toLowerCase().includes(query);
        })
      );
    }

    // Sorting
    if (sortColumn && sortable) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortColumn];
        const bValue = b[sortColumn];

        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;

        let comparison = 0;
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          comparison = aValue - bValue;
        } else {
          comparison = aValue.toString().localeCompare(bValue.toString());
        }

        return sortDirection === 'desc' ? -comparison : comparison;
      });
    }

    return filtered;
  }, [
    data,
    columns,
    searchQuery,
    sortColumn,
    sortDirection,
    sortable,
    searchable,
  ]);

  // Pagination
  const paginatedData = useMemo(() => {
    if (!pagination) return processedData;

    const startIndex = (currentPage - 1) * pageSize;
    return processedData.slice(startIndex, startIndex + pageSize);
  }, [processedData, pagination, currentPage, pageSize]);

  const totalPages = Math.ceil(processedData.length / pageSize);

  const handleSort = (columnKey: string) => {
    if (!sortable) return;

    const column = columns.find(col => col.key === columnKey);
    if (!column?.sortable) return;

    if (sortColumn === columnKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnKey);
      setSortDirection('asc');
    }
  };

  const handleExport = () => {
    if (!exportable) return;

    const csvHeaders = columns.map(col => col.label).join(',');
    const csvRows = processedData.map(row =>
      columns
        .map(col => {
          const value = row[col.key];
          if (value === null || value === undefined) return '';
          const stringValue = value.toString();
          // Escape quotes and wrap in quotes if contains comma
          if (stringValue.includes(',') || stringValue.includes('"')) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        })
        .join(',')
    );

    const csvContent = [csvHeaders, ...csvRows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `${title?.toLowerCase().replace(/\s+/g, '-') || 'data'}-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getSortIcon = (columnKey: string) => {
    if (sortColumn !== columnKey) return null;
    return sortDirection === 'asc' ? (
      <ChevronUp size={16} />
    ) : (
      <ChevronDown size={16} />
    );
  };

  if (loading) {
    return (
      <div className='bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden'>
        {title && (
          <div className='px-6 py-4 border-b border-gray-200'>
            <h3 className='text-lg font-semibold text-gray-900'>{title}</h3>
          </div>
        )}
        <div className='p-6'>
          <div className='animate-pulse space-y-4'>
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className='flex space-x-4'>
                {columns.map((_, j) => (
                  <div key={j} className='flex-1 h-4 bg-gray-200 rounded' />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className='bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden'>
      {/* Header */}
      {(title || searchable || exportable) && (
        <div className='px-6 py-4 border-b border-gray-200'>
          <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
            {title && (
              <h3 className='text-lg font-semibold text-gray-900'>{title}</h3>
            )}
            <div className='flex gap-2'>
              {searchable && (
                <div className='relative'>
                  <Search
                    className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
                    size={16}
                  />
                  <input
                    type='text'
                    placeholder='Search...'
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    className='pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                  />
                </div>
              )}
              {exportable && (
                <button
                  onClick={handleExport}
                  className='flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm transition-colors'
                >
                  <Download size={16} />
                  Export
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className='overflow-x-auto'>
        <table className='w-full'>
          <thead className='bg-gray-50'>
            <tr>
              {columns.map(column => (
                <th
                  key={column.key}
                  className={clsx(
                    'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
                    sortable &&
                      column.sortable &&
                      'cursor-pointer hover:bg-gray-100'
                  )}
                  onClick={() => handleSort(column.key)}
                >
                  <div className='flex items-center gap-1'>
                    {column.label}
                    {sortable && column.sortable && getSortIcon(column.key)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className='bg-white divide-y divide-gray-200'>
            {paginatedData.length > 0 ? (
              paginatedData.map((row, index) => (
                <tr
                  key={index}
                  className={clsx(
                    'transition-colors',
                    onRowClick && 'cursor-pointer hover:bg-gray-50'
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map(column => (
                    <td
                      key={column.key}
                      className='px-6 py-4 whitespace-nowrap text-sm text-gray-900'
                    >
                      {column.render
                        ? column.render(row[column.key], row)
                        : row[column.key]?.toString() || ''}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={columns.length}
                  className='px-6 py-8 text-center text-gray-500'
                >
                  {emptyMessage}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && totalPages > 1 && (
        <div className='px-6 py-4 border-t border-gray-200 flex items-center justify-between'>
          <div className='text-sm text-gray-600'>
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, processedData.length)} of{' '}
            {processedData.length} results
          </div>
          <div className='flex gap-2'>
            <button
              onClick={() => setCurrentPage(page => Math.max(1, page - 1))}
              disabled={currentPage === 1}
              className='px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50'
            >
              Previous
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const page = i + Math.max(1, currentPage - 2);
              if (page > totalPages) return null;
              return (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={clsx(
                    'px-3 py-1 border rounded text-sm',
                    currentPage === page
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-300 hover:bg-gray-50'
                  )}
                >
                  {page}
                </button>
              );
            })}
            <button
              onClick={() =>
                setCurrentPage(page => Math.min(totalPages, page + 1))
              }
              disabled={currentPage === totalPages}
              className='px-3 py-1 border border-gray-300 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50'
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
