import {
  Network,
  Users,
  Star,
  Filter,
  Search,
  Download,
  Info,
  Maximize2,
  Eye,
  Zap,
} from 'lucide-react';
import { useState, useMemo, useCallback } from 'react';

const PARTY_COLORS = {
  Republican: '#dc2626',
  Democratic: '#2563eb',
  Independent: '#7c3aed',
};

const INFLUENCE_LEVELS = {
  high: { color: '#dc2626', label: 'High Influence' },
  medium: { color: '#f59e0b', label: 'Medium Influence' },
  low: { color: '#10b981', label: 'Standard' },
};

function CrossCommitteeMatrix({
  committees = [],
  members = [],
  className = '',
}) {
  const [selectedMember, setSelectedMember] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [partyFilter, setPartyFilter] = useState('all');
  const [viewMode, setViewMode] = useState('matrix'); // matrix, network, list
  const [showInfluenceOnly, setShowInfluenceOnly] = useState(false);

  // Mock data for demonstration - in real app this would come from props
  const mockData = useMemo(() => {
    const committeeNames = [
      'Judiciary',
      'Armed Services',
      'Finance',
      'Health',
      'Agriculture',
      'Commerce',
      'Energy',
      'Foreign Relations',
      'Banking',
      'Intelligence',
    ];

    const memberNames = [
      'Sen. Johnson (R-WI)',
      'Sen. Smith (D-CA)',
      'Sen. Brown (D-OH)',
      'Sen. Davis (R-TX)',
      'Sen. Wilson (D-NY)',
      'Sen. Miller (R-FL)',
      'Sen. Garcia (D-NV)',
      'Sen. Taylor (R-NC)',
      'Sen. Anderson (I-ME)',
      'Sen. Thomas (D-VA)',
      'Sen. Jackson (R-TN)',
      'Sen. White (D-OR)',
    ];

    const mockMembers = memberNames.map((name, i) => {
      const party = name.includes('(R-')
        ? 'Republican'
        : name.includes('(I-')
          ? 'Independent'
          : 'Democratic';
      const committeesCount = Math.floor(Math.random() * 4) + 1;
      const committees = Array.from(
        { length: committeesCount },
        () => committeeNames[Math.floor(Math.random() * committeeNames.length)]
      );

      return {
        id: `member-${i}`,
        name: name.split('(')[0].trim(),
        fullName: name,
        party,
        state: name.match(/\(.-(.+)\)/)?.[1] || 'XX',
        committees: [...new Set(committees)],
        influenceScore: Math.floor(Math.random() * 40) + 60,
        totalCommittees: committees.length,
        isLeadership: Math.random() > 0.7,
      };
    });

    const mockCommittees = committeeNames.map((name, i) => ({
      id: `committee-${i}`,
      name,
      shortName: name.replace(/\s/g, '').substring(0, 6),
      memberCount: Math.floor(Math.random() * 15) + 10,
      chamber: Math.random() > 0.5 ? 'Senate' : 'House',
    }));

    return { mockMembers, mockCommittees };
  }, []);

  // Filter and process data
  const filteredMembers = useMemo(() => {
    let filtered = mockData.mockMembers;

    if (searchTerm) {
      filtered = filtered.filter(
        member =>
          member.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          member.state.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (partyFilter !== 'all') {
      filtered = filtered.filter(member => member.party === partyFilter);
    }

    if (showInfluenceOnly) {
      filtered = filtered.filter(
        member => member.influenceScore >= 80 || member.isLeadership
      );
    }

    return filtered.sort((a, b) => b.influenceScore - a.influenceScore);
  }, [mockData.mockMembers, searchTerm, partyFilter, showInfluenceOnly]);

  // Calculate overlap matrix
  const overlapMatrix = useMemo(() => {
    const matrix = {};
    const { mockCommittees } = mockData;

    mockCommittees.forEach(committee => {
      matrix[committee.id] = {};
      mockCommittees.forEach(otherCommittee => {
        if (committee.id !== otherCommittee.id) {
          // Calculate overlap between committees
          const committee1Members = filteredMembers.filter(m =>
            m.committees.includes(committee.name)
          );
          const committee2Members = filteredMembers.filter(m =>
            m.committees.includes(otherCommittee.name)
          );

          const overlap = committee1Members.filter(m1 =>
            committee2Members.some(m2 => m1.id === m2.id)
          );

          matrix[committee.id][otherCommittee.id] = {
            count: overlap.length,
            members: overlap,
            percentage:
              committee1Members.length > 0
                ? Math.round((overlap.length / committee1Members.length) * 100)
                : 0,
          };
        }
      });
    });

    return matrix;
  }, [filteredMembers, mockData]);

  const getInfluenceLevel = score => {
    if (score >= 85) return 'high';
    if (score >= 70) return 'medium';
    return 'low';
  };

  const getInfluenceColor = score =>
    INFLUENCE_LEVELS[getInfluenceLevel(score)].color;

  const handleMemberClick = useCallback(member => {
    setSelectedMember(member);
  }, []);

  const renderMatrixView = () => {
    const { mockCommittees } = mockData;

    return (
      <div className='overflow-x-auto'>
        <div className='min-w-max'>
          {/* Header row */}
          <div className='flex sticky top-0 bg-gray-50 z-10'>
            <div className='w-32 p-3 border-r border-gray-200 font-medium text-sm text-gray-700'>
              Committee
            </div>
            {mockCommittees.map(committee => (
              <div
                key={committee.id}
                className='w-24 p-3 border-r border-gray-200 text-center'
              >
                <div className='text-xs font-medium text-gray-700 transform -rotate-45 origin-center h-8 flex items-center justify-center'>
                  {committee.shortName}
                </div>
              </div>
            ))}
          </div>

          {/* Matrix rows */}
          {mockCommittees.map(committee => (
            <div key={committee.id} className='flex hover:bg-gray-50'>
              <div className='w-32 p-3 border-r border-gray-200 bg-white sticky left-0 z-10'>
                <div className='text-sm font-medium text-gray-900'>
                  {committee.shortName}
                </div>
                <div className='text-xs text-gray-500'>
                  {committee.memberCount} members
                </div>
              </div>
              {mockCommittees.map(otherCommittee => {
                if (committee.id === otherCommittee.id) {
                  return (
                    <div
                      key={otherCommittee.id}
                      className='w-24 p-3 border-r border-gray-200 bg-gray-100'
                    >
                      <div className='text-center text-xs text-gray-400'>—</div>
                    </div>
                  );
                }

                const overlap = overlapMatrix[committee.id]?.[
                  otherCommittee.id
                ] || { count: 0, percentage: 0 };
                const intensity = Math.min(overlap.percentage / 20, 1); // Max intensity at 20% overlap
                const bgOpacity = intensity * 0.3;

                return (
                  <div
                    key={otherCommittee.id}
                    className='w-24 p-3 border-r border-gray-200 text-center cursor-pointer hover:bg-blue-50 transition-colors'
                    style={{
                      backgroundColor:
                        intensity > 0
                          ? `rgba(59, 130, 246, ${bgOpacity})`
                          : 'transparent',
                    }}
                    title={`${overlap.count} shared members (${overlap.percentage}%)`}
                  >
                    <div className='text-sm font-semibold text-gray-900'>
                      {overlap.count}
                    </div>
                    <div className='text-xs text-gray-500'>
                      {overlap.percentage}%
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderNetworkView = () => {
    const topInfluencers = filteredMembers
      .filter(m => m.totalCommittees >= 2)
      .slice(0, 12);

    return (
      <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4'>
        {topInfluencers.map(member => (
          <div
            key={member.id}
            className='p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer'
            onClick={() => handleMemberClick(member)}
            style={{
              borderLeftColor: PARTY_COLORS[member.party],
              borderLeftWidth: '4px',
            }}
          >
            <div className='flex items-start justify-between mb-2'>
              <div className='flex-1'>
                <h4 className='font-medium text-gray-900 text-sm'>
                  {member.name}
                </h4>
                <p className='text-xs text-gray-500'>
                  {member.party.charAt(0)} - {member.state}
                </p>
              </div>
              {member.isLeadership && (
                <Star className='h-4 w-4 text-yellow-500' fill='currentColor' />
              )}
            </div>

            <div className='space-y-2'>
              <div className='flex items-center justify-between'>
                <span className='text-xs text-gray-600'>Influence</span>
                <div className='flex items-center gap-1'>
                  <div
                    className='w-2 h-2 rounded-full'
                    style={{
                      backgroundColor: getInfluenceColor(member.influenceScore),
                    }}
                  />
                  <span className='text-xs font-medium'>
                    {member.influenceScore}
                  </span>
                </div>
              </div>

              <div className='flex items-center justify-between'>
                <span className='text-xs text-gray-600'>Committees</span>
                <span className='text-xs font-medium'>
                  {member.totalCommittees}
                </span>
              </div>
            </div>

            <div className='mt-3 pt-3 border-t border-gray-100'>
              <div className='flex flex-wrap gap-1'>
                {member.committees.slice(0, 2).map((committee, idx) => (
                  <span
                    key={idx}
                    className='text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded'
                  >
                    {committee.substring(0, 8)}
                  </span>
                ))}
                {member.committees.length > 2 && (
                  <span className='text-xs text-gray-500'>
                    +{member.committees.length - 2}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderListView = () => (
    <div className='space-y-3'>
      {filteredMembers.map(member => (
        <div
          key={member.id}
          className='flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow cursor-pointer'
          onClick={() => handleMemberClick(member)}
        >
          <div className='flex items-center gap-4'>
            <div
              className='w-1 h-12 rounded'
              style={{ backgroundColor: PARTY_COLORS[member.party] }}
            />
            <div>
              <div className='flex items-center gap-2'>
                <h4 className='font-medium text-gray-900'>{member.name}</h4>
                {member.isLeadership && (
                  <Star
                    className='h-4 w-4 text-yellow-500'
                    fill='currentColor'
                  />
                )}
              </div>
              <p className='text-sm text-gray-600'>
                {member.party} - {member.state} • {member.totalCommittees}{' '}
                committees
              </p>
            </div>
          </div>

          <div className='flex items-center gap-6'>
            <div className='text-right'>
              <p className='text-sm font-medium text-gray-900'>
                Influence: {member.influenceScore}
              </p>
              <div className='w-16 h-2 bg-gray-200 rounded-full mt-1'>
                <div
                  className='h-2 rounded-full'
                  style={{
                    width: `${member.influenceScore}%`,
                    backgroundColor: getInfluenceColor(member.influenceScore),
                  }}
                />
              </div>
            </div>

            <div className='flex flex-wrap gap-1 max-w-xs'>
              {member.committees.map((committee, idx) => (
                <span
                  key={idx}
                  className='text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded'
                >
                  {committee}
                </span>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}
    >
      {/* Header */}
      <div className='border-b border-gray-200 p-6'>
        <div className='flex items-center justify-between'>
          <div>
            <h3 className='text-xl font-semibold text-gray-900 flex items-center gap-2'>
              <Network className='h-5 w-5' />
              Cross-Committee Member Matrix
            </h3>
            <p className='text-sm text-gray-600 mt-1'>
              Visualize member overlap and influence across committees
            </p>
          </div>
          <div className='flex items-center gap-2'>
            <button className='p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded'>
              <Download size={16} />
            </button>
            <button className='p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded'>
              <Maximize2 size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className='border-b border-gray-200 p-6'>
        <div className='flex flex-col md:flex-row gap-4'>
          <div className='flex-1'>
            <div className='relative'>
              <Search
                className='absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400'
                size={16}
              />
              <input
                type='text'
                placeholder='Search members or states...'
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
              />
            </div>
          </div>

          <div className='flex items-center gap-4'>
            <select
              value={partyFilter}
              onChange={e => setPartyFilter(e.target.value)}
              className='px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            >
              <option value='all'>All Parties</option>
              <option value='Republican'>Republican</option>
              <option value='Democratic'>Democratic</option>
              <option value='Independent'>Independent</option>
            </select>

            <label className='flex items-center gap-2 text-sm'>
              <input
                type='checkbox'
                checked={showInfluenceOnly}
                onChange={e => setShowInfluenceOnly(e.target.checked)}
                className='rounded border-gray-300 text-blue-600 focus:ring-blue-500'
              />
              High Influence Only
            </label>
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className='flex items-center justify-between mt-4'>
          <div className='flex space-x-1 bg-gray-100 rounded-lg p-1'>
            {[
              { key: 'matrix', label: 'Matrix', icon: Network },
              { key: 'network', label: 'Network', icon: Users },
              { key: 'list', label: 'List', icon: Eye },
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setViewMode(key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === key
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Icon size={16} />
                {label}
              </button>
            ))}
          </div>

          <div className='text-sm text-gray-500'>
            {filteredMembers.length} members shown
          </div>
        </div>
      </div>

      {/* Content */}
      <div className='p-6'>
        {viewMode === 'matrix' && renderMatrixView()}
        {viewMode === 'network' && renderNetworkView()}
        {viewMode === 'list' && renderListView()}
      </div>

      {/* Legend */}
      <div className='border-t border-gray-200 p-6 bg-gray-50'>
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'>
          <div>
            <h4 className='text-sm font-semibold text-gray-700 mb-2'>
              Party Colors
            </h4>
            <div className='space-y-1'>
              {Object.entries(PARTY_COLORS).map(([party, color]) => (
                <div key={party} className='flex items-center gap-2'>
                  <div
                    className='w-3 h-3 rounded'
                    style={{ backgroundColor: color }}
                  />
                  <span className='text-sm text-gray-600'>{party}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className='text-sm font-semibold text-gray-700 mb-2'>
              Influence Levels
            </h4>
            <div className='space-y-1'>
              {Object.entries(INFLUENCE_LEVELS).map(
                ([level, { color, label }]) => (
                  <div key={level} className='flex items-center gap-2'>
                    <div
                      className='w-3 h-3 rounded'
                      style={{ backgroundColor: color }}
                    />
                    <span className='text-sm text-gray-600'>{label}</span>
                  </div>
                )
              )}
            </div>
          </div>

          <div>
            <h4 className='text-sm font-semibold text-gray-700 mb-2'>
              Matrix Guide
            </h4>
            <div className='text-sm text-gray-600 space-y-1'>
              <div className='flex items-center gap-2'>
                <Info size={14} />
                <span>Numbers show shared members</span>
              </div>
              <div className='flex items-center gap-2'>
                <Zap size={14} />
                <span>Darker cells = higher overlap</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Member Detail Modal */}
      {selectedMember && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
          <div className='bg-white rounded-lg shadow-xl max-w-md w-full max-h-96 overflow-y-auto'>
            <div className='p-6'>
              <div className='flex items-start justify-between mb-4'>
                <div>
                  <h3 className='text-lg font-semibold text-gray-900'>
                    {selectedMember.name}
                  </h3>
                  <p className='text-gray-600'>{selectedMember.fullName}</p>
                </div>
                <button
                  onClick={() => setSelectedMember(null)}
                  className='text-gray-400 hover:text-gray-600'
                >
                  ×
                </button>
              </div>

              <div className='space-y-4'>
                <div>
                  <h4 className='text-sm font-semibold text-gray-700 mb-2'>
                    Committee Memberships
                  </h4>
                  <div className='space-y-2'>
                    {selectedMember.committees.map((committee, idx) => (
                      <div
                        key={idx}
                        className='flex items-center justify-between p-2 bg-gray-50 rounded'
                      >
                        <span className='text-sm text-gray-900'>
                          {committee}
                        </span>
                        <span className='text-xs text-gray-500'>Active</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <p className='text-sm text-gray-500'>Influence Score</p>
                    <p
                      className='text-lg font-semibold'
                      style={{
                        color: getInfluenceColor(selectedMember.influenceScore),
                      }}
                    >
                      {selectedMember.influenceScore}
                    </p>
                  </div>
                  <div>
                    <p className='text-sm text-gray-500'>Total Committees</p>
                    <p className='text-lg font-semibold text-gray-900'>
                      {selectedMember.totalCommittees}
                    </p>
                  </div>
                </div>

                {selectedMember.isLeadership && (
                  <div className='flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg'>
                    <Star
                      className='h-4 w-4 text-yellow-600'
                      fill='currentColor'
                    />
                    <span className='text-sm text-yellow-800'>
                      Committee Leadership Position
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CrossCommitteeMatrix;
