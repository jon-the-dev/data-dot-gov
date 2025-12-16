import { clsx } from 'clsx';
import { Search, X } from 'lucide-react';
import { useState } from 'react';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSearch?: (value: string) => void;
  placeholder?: string;
  className?: string;
  loading?: boolean;
  disabled?: boolean;
  showClearButton?: boolean;
  debounceMs?: number;
}

export default function SearchInput({
  value,
  onChange,
  onSearch,
  placeholder = 'Search...',
  className,
  loading = false,
  disabled = false,
  showClearButton = true,
  debounceMs = 300,
}: SearchInputProps) {
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(
    null
  );

  const handleInputChange = (newValue: string) => {
    onChange(newValue);

    if (onSearch && debounceMs > 0) {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }

      const timer = setTimeout(() => {
        onSearch(newValue);
      }, debounceMs);

      setDebounceTimer(timer);
    } else if (onSearch) {
      onSearch(newValue);
    }
  };

  const handleClear = () => {
    handleInputChange('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && onSearch) {
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
      onSearch(value);
    }
  };

  return (
    <div className={clsx('relative', className)}>
      <div className='relative'>
        <Search
          className={clsx(
            'absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400',
            loading && 'animate-pulse'
          )}
          size={20}
        />
        <input
          type='text'
          value={value}
          onChange={e => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || loading}
          className={clsx(
            'w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg',
            'focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
            'transition-colors',
            showClearButton && value && 'pr-10'
          )}
        />
        {showClearButton && value && !disabled && (
          <button
            onClick={handleClear}
            className='absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors'
            type='button'
          >
            <X size={16} />
          </button>
        )}
      </div>
      {loading && (
        <div className='absolute right-3 top-1/2 transform -translate-y-1/2'>
          <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600' />
        </div>
      )}
    </div>
  );
}
