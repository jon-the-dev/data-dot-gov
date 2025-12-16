import { clsx } from 'clsx';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  icon: LucideIcon;
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string;
  trend?: {
    value: number;
    label: string;
    direction: 'up' | 'down' | 'neutral';
  };
  onClick?: () => void;
  loading?: boolean;
  className?: string;
}

export default function StatCard({
  icon: Icon,
  title,
  value,
  subtitle,
  color = 'text-gray-900',
  trend,
  onClick,
  loading = false,
  className,
}: StatCardProps) {
  const bgColor = color
    ? color.replace('text-', 'bg-').replace('900', '100')
    : 'bg-gray-100';
  const iconColor = color || 'text-gray-600';

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up':
        return '↗';
      case 'down':
        return '↘';
      default:
        return '→';
    }
  };

  if (loading) {
    return (
      <div
        className={clsx(
          'bg-white p-6 rounded-lg shadow-sm border border-gray-200 animate-pulse',
          className
        )}
      >
        <div className='flex items-center justify-between'>
          <div className='flex-1'>
            <div className='h-4 bg-gray-200 rounded w-20 mb-2' />
            <div className='h-8 bg-gray-200 rounded w-16 mb-1' />
            <div className='h-3 bg-gray-200 rounded w-24' />
          </div>
          <div className='h-12 w-12 bg-gray-200 rounded-lg' />
        </div>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'bg-white p-6 rounded-lg shadow-sm border border-gray-200 transition-all',
        onClick && 'cursor-pointer hover:shadow-md hover:border-gray-300',
        className
      )}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? e => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
    >
      <div className='flex items-center justify-between'>
        <div className='flex-1'>
          <p className='text-sm font-medium text-gray-600'>{title}</p>
          <p className={clsx('text-2xl font-bold mt-1', color)}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {subtitle && <p className='text-xs text-gray-500 mt-1'>{subtitle}</p>}
          {trend && (
            <div
              className={clsx(
                'flex items-center gap-1 mt-2 text-xs',
                getTrendColor(trend.direction)
              )}
            >
              <span>{getTrendIcon(trend.direction)}</span>
              <span className='font-medium'>{trend.value}%</span>
              <span className='text-gray-500'>{trend.label}</span>
            </div>
          )}
        </div>
        <div className={clsx('p-3 rounded-lg', bgColor)}>
          <Icon className={clsx('h-6 w-6', iconColor)} />
        </div>
      </div>
    </div>
  );
}
