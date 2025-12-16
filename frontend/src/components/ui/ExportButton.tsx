import { clsx } from 'clsx';
import { Download, FileText, Database } from 'lucide-react';
import { useState } from 'react';

import DataService from '@/services/dataService';
import type { ExportOptions } from '@/types';

interface ExportButtonProps {
  data: 'members' | 'bills' | 'votes' | 'lobbying' | 'all';
  filters?: any;
  filename?: string;
  className?: string;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  showDropdown?: boolean;
}

export default function ExportButton({
  data,
  filters,
  filename,
  className,
  variant = 'secondary',
  size = 'md',
  showDropdown = false,
}: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [showOptions, setShowOptions] = useState(false);

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      setIsExporting(true);

      const options: ExportOptions = {
        format,
        data,
        filters,
      };

      const exportData = await DataService.exportData(options);

      const blob = new Blob([exportData], {
        type: format === 'csv' ? 'text/csv' : 'application/json',
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download =
        filename ||
        `${data}-export-${new Date().toISOString().split('T')[0]}.${format}`;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setShowOptions(false);
    } catch (error) {
      console.error('Export failed:', error);
      // You could add toast notification here
    } finally {
      setIsExporting(false);
    }
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'primary':
        return 'bg-blue-600 text-white hover:bg-blue-700 border-blue-600';
      case 'secondary':
        return 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300';
      case 'ghost':
        return 'bg-transparent text-gray-600 hover:bg-gray-100 border-transparent';
      default:
        return 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300';
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'px-3 py-2 text-sm';
      case 'md':
        return 'px-4 py-2 text-sm';
      case 'lg':
        return 'px-6 py-3 text-base';
      default:
        return 'px-4 py-2 text-sm';
    }
  };

  if (showDropdown) {
    return (
      <div className='relative'>
        <button
          onClick={() => setShowOptions(!showOptions)}
          disabled={isExporting}
          className={clsx(
            'inline-flex items-center gap-2 border rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
            getVariantClasses(),
            getSizeClasses(),
            isExporting && 'opacity-50 cursor-not-allowed',
            className
          )}
        >
          {isExporting ? (
            <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-current' />
          ) : (
            <Download size={16} />
          )}
          Export{' '}
          {data === 'all'
            ? 'All Data'
            : data.charAt(0).toUpperCase() + data.slice(1)}
        </button>

        {showOptions && (
          <div className='absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-50'>
            <div className='py-2'>
              <button
                onClick={() => handleExport('csv')}
                disabled={isExporting}
                className='flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50'
              >
                <FileText size={16} />
                Export as CSV
              </button>
              <button
                onClick={() => handleExport('json')}
                disabled={isExporting}
                className='flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50'
              >
                <Database size={16} />
                Export as JSON
              </button>
            </div>
          </div>
        )}

        {/* Overlay to close dropdown */}
        {showOptions && (
          <div
            className='fixed inset-0 z-40'
            onClick={() => setShowOptions(false)}
          />
        )}
      </div>
    );
  }

  return (
    <button
      onClick={() => handleExport('csv')}
      disabled={isExporting}
      className={clsx(
        'inline-flex items-center gap-2 border rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
        getVariantClasses(),
        getSizeClasses(),
        isExporting && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      {isExporting ? (
        <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-current' />
      ) : (
        <Download size={16} />
      )}
      {isExporting ? 'Exporting...' : 'Export'}
    </button>
  );
}
