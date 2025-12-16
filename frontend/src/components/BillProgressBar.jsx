import {
  Building2,
  FileText,
  Users,
  ArrowRight,
  CheckCircle,
  PenTool,
  Vote,
  Crown,
} from 'lucide-react';
import PropTypes from 'prop-types';
import { useState } from 'react';

function BillProgressBar({ bill, compact = false }) {
  const [hoveredStage, setHoveredStage] = useState(null);

  // Define the legislative stages based on bill origin
  const getStages = bill => {
    const isHouseBill =
      bill?.type?.toLowerCase().startsWith('h') ||
      bill?.originChamber?.toLowerCase() === 'house';

    const stages = [
      {
        key: 'introduced',
        label: 'Introduced',
        icon: FileText,
        description: `Bill introduced in the ${isHouseBill ? 'House' : 'Senate'}`,
        chamber: isHouseBill ? 'House' : 'Senate',
      },
      {
        key: 'committee',
        label: 'Committee',
        icon: Building2,
        description: 'Referred to committee for review and markup',
        chamber: isHouseBill ? 'House' : 'Senate',
      },
      {
        key: 'subcommittee',
        label: 'Subcommittee',
        icon: Users,
        description: 'Detailed review by specialized subcommittee',
        chamber: isHouseBill ? 'House' : 'Senate',
        optional: true,
      },
      {
        key: 'markup',
        label: 'Markup',
        icon: PenTool,
        description: 'Committee marks up and votes on the bill',
        chamber: isHouseBill ? 'House' : 'Senate',
      },
      {
        key: 'floor',
        label: `${isHouseBill ? 'House' : 'Senate'} Floor`,
        icon: Vote,
        description: `Full ${isHouseBill ? 'House' : 'Senate'} votes on the bill`,
        chamber: isHouseBill ? 'House' : 'Senate',
      },
      {
        key: 'other_chamber',
        label: isHouseBill ? 'Senate' : 'House',
        icon: ArrowRight,
        description: `Sent to ${isHouseBill ? 'Senate' : 'House'} for consideration`,
        chamber: isHouseBill ? 'Senate' : 'House',
      },
      {
        key: 'president',
        label: 'President',
        icon: Crown,
        description: 'Awaiting presidential signature or veto',
        chamber: 'Executive',
      },
      {
        key: 'law',
        label: 'Became Law',
        icon: CheckCircle,
        description: 'Signed into law by the President',
        chamber: 'Complete',
      },
    ];

    return stages;
  };

  // Determine current stage based on bill status and latest action
  const getCurrentStage = bill => {
    if (!bill) return 0;

    const status = bill.status?.toLowerCase() || '';
    const latestAction = bill.latestAction?.text?.toLowerCase() || '';

    // Check for completion first
    if (
      status.includes('became law') ||
      status.includes('public law') ||
      latestAction.includes('became public law') ||
      latestAction.includes('signed by president')
    ) {
      return 7; // Became Law
    }

    if (
      latestAction.includes('presented to president') ||
      latestAction.includes('sent to president')
    ) {
      return 6; // President
    }

    if (
      latestAction.includes('passed senate') ||
      latestAction.includes('passed house')
    ) {
      return 5; // Other Chamber
    }

    if (latestAction.includes('passed/agreed to in')) {
      return 4; // Floor vote
    }

    if (
      latestAction.includes('ordered to be reported') ||
      latestAction.includes('committee agreed to report')
    ) {
      return 3; // Markup
    }

    if (
      latestAction.includes('referred to subcommittee') ||
      latestAction.includes('subcommittee')
    ) {
      return 2; // Subcommittee
    }

    if (
      latestAction.includes('referred to') ||
      latestAction.includes('committee')
    ) {
      return 1; // Committee
    }

    if (status.includes('introduced') || latestAction.includes('introduced')) {
      return 0; // Introduced
    }

    // Default fallback
    return 0;
  };

  const stages = getStages(bill);
  const currentStageIndex = getCurrentStage(bill);
  const progress = Math.round((currentStageIndex / (stages.length - 1)) * 100);

  const getStageStatus = index => {
    if (index < currentStageIndex) return 'completed';
    if (index === currentStageIndex) return 'current';
    return 'upcoming';
  };

  const getStatusColor = status => {
    switch (status) {
      case 'completed':
        return 'bg-green-500 text-white border-green-500';
      case 'current':
        return 'bg-blue-500 text-white border-blue-500';
      case 'upcoming':
        return 'bg-gray-200 text-gray-500 border-gray-200';
      default:
        return 'bg-gray-200 text-gray-500 border-gray-200';
    }
  };

  const getConnectorColor = index => {
    if (index < currentStageIndex) return 'bg-green-500';
    if (index === currentStageIndex - 1)
      return 'bg-gradient-to-r from-green-500 to-gray-300';
    return 'bg-gray-300';
  };

  const getChamberColor = chamber => {
    switch (chamber?.toLowerCase()) {
      case 'house':
        return 'text-blue-600';
      case 'senate':
        return 'text-purple-600';
      case 'executive':
        return 'text-orange-600';
      case 'complete':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  if (compact) {
    return (
      <div className='flex items-center gap-2'>
        <div className='flex items-center gap-1'>
          {stages.slice(0, 5).map((stage, index) => {
            const status = getStageStatus(index);
            const Icon = stage.icon;

            return (
              <div key={stage.key} className='flex items-center'>
                <div
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${getStatusColor(status)}`}
                  title={`${stage.label}: ${stage.description}`}
                >
                  <Icon size={12} />
                </div>
                {index < 4 && (
                  <div className={`w-3 h-0.5 ${getConnectorColor(index)}`} />
                )}
              </div>
            );
          })}
        </div>
        <span className='text-xs text-gray-600 font-medium'>{progress}%</span>
      </div>
    );
  }

  return (
    <div className='bg-white rounded-lg border border-gray-200 p-6'>
      <div className='flex items-center justify-between mb-4'>
        <h3 className='text-lg font-semibold text-gray-900'>
          Legislative Progress
        </h3>
        <div className='flex items-center gap-2'>
          <div className='text-sm text-gray-600'>Progress:</div>
          <div className='text-lg font-bold text-blue-600'>{progress}%</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className='mb-6'>
        <div className='w-full bg-gray-200 rounded-full h-2 mb-2'>
          <div
            className='bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full transition-all duration-500'
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className='flex justify-between text-xs text-gray-500'>
          <span>Introduced</span>
          <span>Became Law</span>
        </div>
      </div>

      {/* Desktop View - Horizontal */}
      <div className='hidden md:block'>
        <div className='flex items-center justify-between'>
          {stages.map((stage, index) => {
            const status = getStageStatus(index);
            const Icon = stage.icon;
            const isLast = index === stages.length - 1;

            return (
              <div key={stage.key} className='flex items-center'>
                <div
                  className='flex flex-col items-center'
                  onMouseEnter={() => setHoveredStage(index)}
                  onMouseLeave={() => setHoveredStage(null)}
                >
                  <div
                    className={`w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${getStatusColor(status)} ${hoveredStage === index ? 'scale-110 shadow-lg' : ''}`}
                  >
                    <Icon size={20} />
                  </div>
                  <div className='mt-2 text-center'>
                    <div
                      className={`text-sm font-medium ${status === 'current' ? 'text-blue-600' : status === 'completed' ? 'text-green-600' : 'text-gray-500'}`}
                    >
                      {stage.label}
                    </div>
                    <div
                      className={`text-xs ${getChamberColor(stage.chamber)} mt-1`}
                    >
                      {stage.chamber}
                    </div>
                  </div>

                  {/* Tooltip */}
                  {hoveredStage === index && (
                    <div className='absolute z-10 mt-20 w-64 p-3 bg-gray-900 text-white text-sm rounded-lg shadow-lg'>
                      <div className='font-medium mb-1'>{stage.label}</div>
                      <div>{stage.description}</div>
                      {stage.optional && (
                        <div className='text-yellow-300 text-xs mt-1'>
                          * Optional stage
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Connector Line */}
                {!isLast && (
                  <div
                    className={`flex-1 h-1 mx-2 rounded ${getConnectorColor(index)}`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Mobile View - Vertical */}
      <div className='md:hidden'>
        <div className='space-y-4'>
          {stages.map((stage, index) => {
            const status = getStageStatus(index);
            const Icon = stage.icon;

            return (
              <div key={stage.key} className='flex items-start gap-3'>
                <div
                  className={`w-10 h-10 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${getStatusColor(status)}`}
                >
                  <Icon size={16} />
                </div>
                <div className='flex-1'>
                  <div className='flex items-center justify-between'>
                    <div
                      className={`font-medium ${status === 'current' ? 'text-blue-600' : status === 'completed' ? 'text-green-600' : 'text-gray-500'}`}
                    >
                      {stage.label}
                    </div>
                    <div
                      className={`text-xs ${getChamberColor(stage.chamber)}`}
                    >
                      {stage.chamber}
                    </div>
                  </div>
                  <div className='text-sm text-gray-600 mt-1'>
                    {stage.description}
                  </div>
                  {stage.optional && (
                    <div className='text-xs text-yellow-600 mt-1'>
                      * Optional stage
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Current Status */}
      <div className='mt-6 p-4 bg-gray-50 rounded-lg'>
        <div className='flex items-center justify-between'>
          <div>
            <div className='text-sm font-medium text-gray-700'>
              Current Status
            </div>
            <div className='text-lg font-semibold text-gray-900'>
              {stages[currentStageIndex]?.label || 'Unknown'}
            </div>
          </div>
          <div className='text-right'>
            <div className='text-sm text-gray-600'>Last Action</div>
            <div className='text-sm font-medium text-gray-900'>
              {bill?.latestAction?.actionDate
                ? new Date(bill.latestAction.actionDate).toLocaleDateString()
                : 'Unknown'}
            </div>
          </div>
        </div>
        {bill?.latestAction?.text && (
          <div className='mt-2 text-sm text-gray-700'>
            {bill.latestAction.text.length > 100
              ? `${bill.latestAction.text.substring(0, 100)}...`
              : bill.latestAction.text}
          </div>
        )}
      </div>
    </div>
  );
}

BillProgressBar.propTypes = {
  bill: PropTypes.shape({
    type: PropTypes.string,
    originChamber: PropTypes.string,
    status: PropTypes.string,
    latestAction: PropTypes.shape({
      text: PropTypes.string,
      actionDate: PropTypes.string,
    }),
  }),
  compact: PropTypes.bool,
};

export default BillProgressBar;
