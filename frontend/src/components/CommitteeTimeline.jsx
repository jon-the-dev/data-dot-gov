import { formatDistanceToNow, format } from 'date-fns';
import {
  Calendar,
  Clock,
  FileText,
  Users,
  Gavel,
  CheckCircle,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  PlayCircle,
  Vote,
  AlertCircle,
} from 'lucide-react';
import { useState } from 'react';

function CommitteeTimeline({
  activities = [],
  loading = false,
  onLoadMore,
  hasMore = false,
}) {
  const [expandedActivities, setExpandedActivities] = useState(new Set());

  const toggleActivity = activityId => {
    const newExpanded = new Set(expandedActivities);
    if (newExpanded.has(activityId)) {
      newExpanded.delete(activityId);
    } else {
      newExpanded.add(activityId);
    }
    setExpandedActivities(newExpanded);
  };

  const getActivityIcon = type => {
    const iconMap = {
      bill_referral: FileText,
      hearing: Users,
      vote: Vote,
      markup: Gavel,
      meeting: PlayCircle,
      report: CheckCircle,
      amendment: AlertCircle,
      default: Calendar,
    };

    return iconMap[type] || iconMap['default'];
  };

  const getActivityColor = type => {
    const colorMap = {
      bill_referral: 'bg-blue-100 text-blue-600 border-blue-200',
      hearing: 'bg-purple-100 text-purple-600 border-purple-200',
      vote: 'bg-green-100 text-green-600 border-green-200',
      markup: 'bg-amber-100 text-amber-600 border-amber-200',
      meeting: 'bg-indigo-100 text-indigo-600 border-indigo-200',
      report: 'bg-emerald-100 text-emerald-600 border-emerald-200',
      amendment: 'bg-orange-100 text-orange-600 border-orange-200',
      default: 'bg-gray-100 text-gray-600 border-gray-200',
    };

    return colorMap[type] || colorMap['default'];
  };

  const getTimelineLineColor = type => {
    const colorMap = {
      bill_referral: 'border-blue-300',
      hearing: 'border-purple-300',
      vote: 'border-green-300',
      markup: 'border-amber-300',
      meeting: 'border-indigo-300',
      report: 'border-emerald-300',
      amendment: 'border-orange-300',
      default: 'border-gray-300',
    };

    return colorMap[type] || colorMap['default'];
  };

  const formatRelativeTime = date => {
    if (!date) return '';
    try {
      return formatDistanceToNow(new Date(date), { addSuffix: true });
    } catch (error) {
      return format(new Date(date), 'MMM d, yyyy');
    }
  };

  const formatDateTime = date => {
    if (!date) return '';
    try {
      return format(new Date(date), 'MMM d, yyyy • h:mm a');
    } catch (error) {
      return date;
    }
  };

  if (loading) {
    return (
      <div className='space-y-6'>
        <div>
          <h3 className='text-lg font-semibold text-gray-900 mb-2'>
            Committee Timeline
          </h3>
          <p className='text-sm text-gray-600'>
            Recent committee activities and events
          </p>
        </div>
        <div className='bg-white rounded-lg border border-gray-200 p-6'>
          <div className='flex items-center justify-center py-8'>
            <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600' />
            <span className='ml-2 text-gray-600'>Loading timeline...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <div className='space-y-6'>
        <div>
          <h3 className='text-lg font-semibold text-gray-900 mb-2'>
            Committee Timeline
          </h3>
          <p className='text-sm text-gray-600'>
            Recent committee activities and events
          </p>
        </div>
        <div className='bg-white rounded-lg border border-gray-200 p-6'>
          <div className='text-center py-8'>
            <Calendar className='mx-auto h-12 w-12 text-gray-400 mb-4' />
            <h4 className='text-lg font-medium text-gray-900 mb-2'>
              No Recent Activity
            </h4>
            <p className='text-sm text-gray-500'>
              Committee timeline will appear here when activities are available.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      <div>
        <h3 className='text-lg font-semibold text-gray-900 mb-2'>
          Committee Timeline
        </h3>
        <p className='text-sm text-gray-600'>
          Recent committee activities and events • Showing {activities.length}{' '}
          activities
        </p>
      </div>

      <div className='bg-white rounded-lg border border-gray-200'>
        <div className='p-6'>
          <div className='relative'>
            {activities.map((activity, index) => {
              const Icon = getActivityIcon(activity.type);
              const isExpanded = expandedActivities.has(activity.id);
              const isLast = index === activities.length - 1;

              return (
                <div key={activity.id} className='relative'>
                  {/* Timeline Line */}
                  {!isLast && (
                    <div
                      className={`absolute left-6 top-12 w-0.5 h-full border-l-2 border-dashed ${getTimelineLineColor(activity.type)}`}
                      style={{ height: 'calc(100% + 1rem)' }}
                    />
                  )}

                  <div className='flex items-start space-x-4 pb-6'>
                    {/* Icon */}
                    <div
                      className={`flex-shrink-0 w-12 h-12 rounded-full border-2 flex items-center justify-center ${getActivityColor(activity.type)} z-10 bg-white`}
                    >
                      <Icon className='w-5 h-5' />
                    </div>

                    {/* Content */}
                    <div className='flex-1 min-w-0'>
                      <div
                        className={`bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors ${
                          activity.details ? 'cursor-pointer' : ''
                        }`}
                        onClick={() =>
                          activity.details && toggleActivity(activity.id)
                        }
                      >
                        <div className='flex items-start justify-between'>
                          <div className='flex-1'>
                            <div className='flex items-center gap-2 mb-1'>
                              <h4 className='text-sm font-medium text-gray-900'>
                                {activity.description}
                              </h4>
                              {activity.details && (
                                <button className='text-gray-400 hover:text-gray-600'>
                                  {isExpanded ? (
                                    <ChevronDown className='w-4 h-4' />
                                  ) : (
                                    <ChevronRight className='w-4 h-4' />
                                  )}
                                </button>
                              )}
                            </div>

                            <div className='flex items-center space-x-4 text-xs text-gray-500'>
                              <div className='flex items-center space-x-1'>
                                <Clock className='w-3 h-3' />
                                <span>{formatRelativeTime(activity.date)}</span>
                              </div>
                              <span>•</span>
                              <span>{formatDateTime(activity.date)}</span>
                              {activity.type && (
                                <>
                                  <span>•</span>
                                  <span className='capitalize'>
                                    {activity.type.replace('_', ' ')}
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Expanded Details */}
                        {isExpanded && activity.details && (
                          <div className='mt-4 pt-4 border-t border-gray-200'>
                            <div className='prose prose-sm max-w-none'>
                              {typeof activity.details === 'string' ? (
                                <p className='text-sm text-gray-700 whitespace-pre-wrap'>
                                  {activity.details}
                                </p>
                              ) : (
                                <div className='space-y-3'>
                                  {activity.details.summary && (
                                    <div>
                                      <h5 className='text-sm font-medium text-gray-900 mb-1'>
                                        Summary
                                      </h5>
                                      <p className='text-sm text-gray-700'>
                                        {activity.details.summary}
                                      </p>
                                    </div>
                                  )}

                                  {activity.details.participants &&
                                    activity.details.participants.length >
                                      0 && (
                                      <div>
                                        <h5 className='text-sm font-medium text-gray-900 mb-1'>
                                          Participants
                                        </h5>
                                        <div className='flex flex-wrap gap-1'>
                                          {activity.details.participants.map(
                                            (participant, idx) => (
                                              <span
                                                key={idx}
                                                className='inline-flex items-center px-2 py-1 rounded-md text-xs bg-blue-50 text-blue-700'
                                              >
                                                {participant}
                                              </span>
                                            )
                                          )}
                                        </div>
                                      </div>
                                    )}

                                  {activity.details.bills &&
                                    activity.details.bills.length > 0 && (
                                      <div>
                                        <h5 className='text-sm font-medium text-gray-900 mb-1'>
                                          Related Bills
                                        </h5>
                                        <div className='space-y-1'>
                                          {activity.details.bills.map(
                                            (bill, idx) => (
                                              <div
                                                key={idx}
                                                className='flex items-center space-x-2 text-sm'
                                              >
                                                <FileText className='w-3 h-3 text-gray-400' />
                                                <span className='font-mono text-blue-600'>
                                                  {bill.number}
                                                </span>
                                                <span className='text-gray-700'>
                                                  {bill.title}
                                                </span>
                                              </div>
                                            )
                                          )}
                                        </div>
                                      </div>
                                    )}

                                  {activity.details.outcome && (
                                    <div>
                                      <h5 className='text-sm font-medium text-gray-900 mb-1'>
                                        Outcome
                                      </h5>
                                      <p className='text-sm text-gray-700'>
                                        {activity.details.outcome}
                                      </p>
                                    </div>
                                  )}

                                  {activity.details.nextSteps && (
                                    <div>
                                      <h5 className='text-sm font-medium text-gray-900 mb-1'>
                                        Next Steps
                                      </h5>
                                      <p className='text-sm text-gray-700'>
                                        {activity.details.nextSteps}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Load More Button */}
          {hasMore && onLoadMore && (
            <div className='flex justify-center pt-4 border-t border-gray-200'>
              <button
                onClick={onLoadMore}
                className='inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'
              >
                <Clock className='w-4 h-4 mr-2' />
                Load More Activities
                <ArrowRight className='w-4 h-4 ml-2' />
              </button>
            </div>
          )}

          {/* Activity Summary */}
          {activities.length > 0 && (
            <div className='mt-6 pt-4 border-t border-gray-200'>
              <div className='grid grid-cols-2 md:grid-cols-4 gap-4 text-center'>
                {Object.entries(
                  activities.reduce((acc, activity) => {
                    acc[activity.type] = (acc[activity.type] || 0) + 1;
                    return acc;
                  }, {})
                ).map(([type, count]) => (
                  <div key={type} className='text-xs'>
                    <div className='font-medium text-gray-900'>{count}</div>
                    <div className='text-gray-500 capitalize'>
                      {type.replace('_', ' ')}
                      {count !== 1 ? 's' : ''}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mobile-Friendly Note */}
      <div className='md:hidden bg-blue-50 border border-blue-200 rounded-lg p-3'>
        <div className='flex items-center space-x-2'>
          <AlertCircle className='w-4 h-4 text-blue-600 flex-shrink-0' />
          <p className='text-xs text-blue-700'>
            Tap activities to expand details and view more information.
          </p>
        </div>
      </div>
    </div>
  );
}

export default CommitteeTimeline;
