import {
  ChevronDown,
  ChevronRight,
  Building2,
  Users,
  Search,
  Expand,
  Collapse,
  ExternalLink,
  MapPin,
  Star,
  FileText,
} from 'lucide-react';
import { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';

const CHAMBER_COLORS = {
  House: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  Senate: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  Joint: {
    bg: 'bg-purple-50',
    text: 'text-purple-700',
    border: 'border-purple-200',
  },
};

function CommitteeHierarchy({ data: _data, className = '' }) {
  const [expandedCommittees, setExpandedCommittees] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [chamberFilter, setChamberFilter] = useState('all');
  const [sizeFilter, setSizeFilter] = useState('all');
  const [showSubcommittees, setShowSubcommittees] = useState(true);

  // Mock hierarchical data - in real app this would come from props
  const mockHierarchyData = useMemo(
    () => ({
      House: [
        {
          id: 'house-judiciary',
          name: 'Committee on the Judiciary',
          shortName: 'Judiciary',
          code: 'HSJU',
          chamber: 'House',
          memberCount: 24,
          activeBills: 45,
          chair: { name: 'Rep. Jordan', party: 'Republican', state: 'OH' },
          rankingMember: {
            name: 'Rep. Nadler',
            party: 'Democratic',
            state: 'NY',
          },
          jurisdiction:
            'Constitutional law, federal courts, immigration, antitrust',
          website: 'https://judiciary.house.gov',
          subcommittees: [
            {
              id: 'house-judiciary-constitution',
              name: 'Constitution and Limited Government',
              code: 'HSJU01',
              memberCount: 12,
              activeBills: 8,
              chair: { name: 'Rep. Biggs', party: 'Republican', state: 'AZ' },
            },
            {
              id: 'house-judiciary-immigration',
              name: 'Immigration Integrity, Security, and Enforcement',
              code: 'HSJU02',
              memberCount: 14,
              activeBills: 23,
              chair: {
                name: 'Rep. McClintock',
                party: 'Republican',
                state: 'CA',
              },
            },
            {
              id: 'house-judiciary-antitrust',
              name: 'Antitrust, Commercial, and Administrative Law',
              code: 'HSJU05',
              memberCount: 16,
              activeBills: 12,
              chair: { name: 'Rep. Massie', party: 'Republican', state: 'KY' },
            },
          ],
        },
        {
          id: 'house-armed-services',
          name: 'Committee on Armed Services',
          shortName: 'Armed Services',
          code: 'HSAS',
          chamber: 'House',
          memberCount: 58,
          activeBills: 67,
          chair: { name: 'Rep. Rogers', party: 'Republican', state: 'AL' },
          rankingMember: {
            name: 'Rep. Smith',
            party: 'Democratic',
            state: 'WA',
          },
          jurisdiction: 'Defense policy, military personnel, weapons systems',
          website: 'https://armedservices.house.gov',
          subcommittees: [
            {
              id: 'house-armed-services-readiness',
              name: 'Readiness',
              code: 'HSAS03',
              memberCount: 26,
              activeBills: 15,
              chair: { name: 'Rep. Lamborn', party: 'Republican', state: 'CO' },
            },
            {
              id: 'house-armed-services-intel',
              name: 'Intelligence and Special Operations',
              code: 'HSAS06',
              memberCount: 18,
              activeBills: 8,
              chair: { name: 'Rep. Turner', party: 'Republican', state: 'OH' },
            },
          ],
        },
        {
          id: 'house-energy-commerce',
          name: 'Committee on Energy and Commerce',
          shortName: 'Energy & Commerce',
          code: 'HSIF',
          chamber: 'House',
          memberCount: 55,
          activeBills: 89,
          chair: {
            name: 'Rep. McMorris Rodgers',
            party: 'Republican',
            state: 'WA',
          },
          rankingMember: {
            name: 'Rep. Pallone',
            party: 'Democratic',
            state: 'NJ',
          },
          jurisdiction:
            'Energy policy, telecommunications, healthcare, environment',
          website: 'https://energycommerce.house.gov',
          subcommittees: [
            {
              id: 'house-energy-commerce-health',
              name: 'Health',
              code: 'HSIF14',
              memberCount: 32,
              activeBills: 45,
              chair: { name: 'Rep. Guthrie', party: 'Republican', state: 'KY' },
            },
            {
              id: 'house-energy-commerce-energy',
              name: 'Energy, Climate and Grid Security',
              code: 'HSIF18',
              memberCount: 28,
              activeBills: 23,
              chair: { name: 'Rep. Duncan', party: 'Republican', state: 'SC' },
            },
          ],
        },
      ],
      Senate: [
        {
          id: 'senate-judiciary',
          name: 'Committee on the Judiciary',
          shortName: 'Judiciary',
          code: 'SSJU',
          chamber: 'Senate',
          memberCount: 22,
          activeBills: 34,
          chair: { name: 'Sen. Durbin', party: 'Democratic', state: 'IL' },
          rankingMember: {
            name: 'Sen. Graham',
            party: 'Republican',
            state: 'SC',
          },
          jurisdiction:
            'Federal courts, constitutional amendments, federal criminal law',
          website: 'https://www.judiciary.senate.gov',
          subcommittees: [
            {
              id: 'senate-judiciary-constitution',
              name: 'Constitution',
              code: 'SSJU01',
              memberCount: 8,
              activeBills: 6,
              chair: {
                name: 'Sen. Blumenthal',
                party: 'Democratic',
                state: 'CT',
              },
            },
            {
              id: 'senate-judiciary-immigration',
              name: 'Immigration, Citizenship, and Border Safety',
              code: 'SSJU02',
              memberCount: 10,
              activeBills: 15,
              chair: { name: 'Sen. Padilla', party: 'Democratic', state: 'CA' },
            },
          ],
        },
        {
          id: 'senate-armed-services',
          name: 'Committee on Armed Services',
          shortName: 'Armed Services',
          code: 'SSAS',
          chamber: 'Senate',
          memberCount: 26,
          activeBills: 42,
          chair: { name: 'Sen. Reed', party: 'Democratic', state: 'RI' },
          rankingMember: {
            name: 'Sen. Wicker',
            party: 'Republican',
            state: 'MS',
          },
          jurisdiction:
            'Defense authorization, military construction, nuclear energy',
          website: 'https://www.armed-services.senate.gov',
          subcommittees: [
            {
              id: 'senate-armed-services-readiness',
              name: 'Readiness and Management Support',
              code: 'SSAS02',
              memberCount: 14,
              activeBills: 12,
              chair: { name: 'Sen. Kaine', party: 'Democratic', state: 'VA' },
            },
            {
              id: 'senate-armed-services-strategic',
              name: 'Strategic Forces',
              code: 'SSAS04',
              memberCount: 12,
              activeBills: 8,
              chair: { name: 'Sen. King', party: 'Independent', state: 'ME' },
            },
          ],
        },
      ],
      Joint: [
        {
          id: 'joint-economic',
          name: 'Joint Economic Committee',
          shortName: 'Economic',
          code: 'JEC',
          chamber: 'Joint',
          memberCount: 20,
          activeBills: 12,
          chair: { name: 'Sen. Heinrich', party: 'Democratic', state: 'NM' },
          viceChair: {
            name: 'Rep. Schweikert',
            party: 'Republican',
            state: 'AZ',
          },
          jurisdiction: 'Economic policy analysis and recommendations',
          website: 'https://www.jec.senate.gov',
          subcommittees: [],
        },
      ],
    }),
    []
  );

  // Filter and search logic
  const filteredData = useMemo(() => {
    let filtered = { ...mockHierarchyData };

    // Apply chamber filter
    if (chamberFilter !== 'all') {
      filtered = {
        [chamberFilter]: mockHierarchyData[chamberFilter] || [],
      };
    }

    // Apply search and size filters
    Object.keys(filtered).forEach(chamber => {
      filtered[chamber] = filtered[chamber].filter(committee => {
        let matchesSearch = true;
        let matchesSize = true;

        if (searchTerm) {
          const searchLower = searchTerm.toLowerCase();
          matchesSearch =
            committee.name.toLowerCase().includes(searchLower) ||
            committee.shortName.toLowerCase().includes(searchLower) ||
            committee.code.toLowerCase().includes(searchLower) ||
            committee.jurisdiction?.toLowerCase().includes(searchLower) ||
            committee.subcommittees.some(sub =>
              sub.name.toLowerCase().includes(searchLower)
            );
        }

        if (sizeFilter !== 'all') {
          switch (sizeFilter) {
            case 'large':
              matchesSize = committee.memberCount >= 40;
              break;
            case 'medium':
              matchesSize =
                committee.memberCount >= 20 && committee.memberCount < 40;
              break;
            case 'small':
              matchesSize = committee.memberCount < 20;
              break;
          }
        }

        return matchesSearch && matchesSize;
      });
    });

    return filtered;
  }, [mockHierarchyData, searchTerm, chamberFilter, sizeFilter]);

  const toggleExpanded = useCallback(committeeId => {
    setExpandedCommittees(prev => {
      const newSet = new Set(prev);
      if (newSet.has(committeeId)) {
        newSet.delete(committeeId);
      } else {
        newSet.add(committeeId);
      }
      return newSet;
    });
  }, []);

  const expandAll = useCallback(() => {
    const allIds = new Set();
    Object.values(filteredData)
      .flat()
      .forEach(committee => {
        if (committee.subcommittees?.length > 0) {
          allIds.add(committee.id);
        }
      });
    setExpandedCommittees(allIds);
  }, [filteredData]);

  const collapseAll = useCallback(() => {
    setExpandedCommittees(new Set());
  }, []);

  const CommitteeNode = ({ committee, level = 0 }) => {
    const isExpanded = expandedCommittees.has(committee.id);
    const hasSubcommittees = committee.subcommittees?.length > 0;
    const chamberStyle =
      CHAMBER_COLORS[committee.chamber] || CHAMBER_COLORS.House;

    return (
      <div
        className={`${level > 0 ? 'ml-6 border-l-2 border-gray-200 pl-4' : ''}`}
      >
        <div
          className='group p-4 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-all cursor-pointer'
          onClick={() => hasSubcommittees && toggleExpanded(committee.id)}
        >
          <div className='flex items-center justify-between'>
            <div className='flex items-center gap-3 flex-1'>
              {hasSubcommittees && showSubcommittees ? (
                isExpanded ? (
                  <ChevronDown className='h-4 w-4 text-gray-400 flex-shrink-0' />
                ) : (
                  <ChevronRight className='h-4 w-4 text-gray-400 flex-shrink-0' />
                )
              ) : (
                <div className='w-4 h-4 flex-shrink-0' />
              )}

              <div className='flex items-center gap-3 flex-1'>
                <div className={`p-2 rounded-lg ${chamberStyle.bg}`}>
                  <Building2 className={`h-4 w-4 ${chamberStyle.text}`} />
                </div>

                <div className='flex-1 min-w-0'>
                  <div className='flex items-center gap-2 mb-1'>
                    <Link
                      to={`/committees/${committee.id}`}
                      className='text-lg font-semibold text-gray-900 hover:text-blue-600 hover:underline'
                      onClick={e => e.stopPropagation()}
                    >
                      {committee.shortName}
                    </Link>
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${chamberStyle.bg} ${chamberStyle.text} ${chamberStyle.border} border`}
                    >
                      {committee.chamber}
                    </span>
                    {level === 0 && (
                      <span className='px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded font-mono'>
                        {committee.code}
                      </span>
                    )}
                  </div>
                  <p className='text-sm text-gray-600 line-clamp-2'>
                    {committee.name}
                  </p>
                  {committee.jurisdiction && level === 0 && (
                    <p className='text-xs text-gray-500 mt-1 line-clamp-1'>
                      {committee.jurisdiction}
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className='flex items-center gap-4 text-sm text-gray-600'>
              <div className='flex items-center gap-1'>
                <Users className='h-4 w-4' />
                <span>{committee.memberCount}</span>
              </div>
              <div className='flex items-center gap-1'>
                <FileText className='h-4 w-4' />
                <span>{committee.activeBills}</span>
              </div>
              {committee.website && (
                <button
                  onClick={e => {
                    e.stopPropagation();
                    window.open(committee.website, '_blank');
                  }}
                  className='p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded'
                  title='Visit committee website'
                >
                  <ExternalLink className='h-4 w-4' />
                </button>
              )}
            </div>
          </div>

          {/* Leadership info for main committees */}
          {level === 0 && (committee.chair || committee.rankingMember) && (
            <div className='mt-3 pt-3 border-t border-gray-100'>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-sm'>
                {committee.chair && (
                  <div className='flex items-center gap-2'>
                    <Star
                      className='h-3 w-3 text-yellow-500'
                      fill='currentColor'
                    />
                    <span className='text-gray-500'>Chair:</span>
                    <span className='font-medium text-gray-900'>
                      {committee.chair.name}
                    </span>
                    <span className='text-gray-500'>
                      ({committee.chair.party.charAt(0)}-{committee.chair.state}
                      )
                    </span>
                  </div>
                )}
                {committee.rankingMember && (
                  <div className='flex items-center gap-2'>
                    <MapPin className='h-3 w-3 text-gray-400' />
                    <span className='text-gray-500'>Ranking:</span>
                    <span className='font-medium text-gray-900'>
                      {committee.rankingMember.name}
                    </span>
                    <span className='text-gray-500'>
                      ({committee.rankingMember.party.charAt(0)}-
                      {committee.rankingMember.state})
                    </span>
                  </div>
                )}
                {committee.viceChair && (
                  <div className='flex items-center gap-2'>
                    <MapPin className='h-3 w-3 text-gray-400' />
                    <span className='text-gray-500'>Vice Chair:</span>
                    <span className='font-medium text-gray-900'>
                      {committee.viceChair.name}
                    </span>
                    <span className='text-gray-500'>
                      ({committee.viceChair.party.charAt(0)}-
                      {committee.viceChair.state})
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Subcommittees */}
        {hasSubcommittees && showSubcommittees && isExpanded && (
          <div className='mt-3 space-y-2'>
            {committee.subcommittees.map(subcommittee => (
              <CommitteeNode
                key={subcommittee.id}
                committee={subcommittee}
                level={level + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  const totalCommittees = Object.values(filteredData).flat().length;
  const totalSubcommittees = Object.values(filteredData)
    .flat()
    .reduce(
      (sum, committee) => sum + (committee.subcommittees?.length || 0),
      0
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
              <Building2 className='h-5 w-5' />
              Committee Hierarchy
            </h3>
            <p className='text-sm text-gray-600 mt-1'>
              Explore committee structure and subcommittee relationships
            </p>
          </div>
          <div className='flex items-center gap-2'>
            <button
              onClick={expandAll}
              className='flex items-center gap-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded'
            >
              <Expand size={14} />
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className='flex items-center gap-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded'
            >
              <Collapse size={14} />
              Collapse All
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
                placeholder='Search committees, codes, or jurisdiction...'
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className='w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
              />
            </div>
          </div>

          <div className='flex items-center gap-4'>
            <select
              value={chamberFilter}
              onChange={e => setChamberFilter(e.target.value)}
              className='px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            >
              <option value='all'>All Chambers</option>
              <option value='House'>House</option>
              <option value='Senate'>Senate</option>
              <option value='Joint'>Joint</option>
            </select>

            <select
              value={sizeFilter}
              onChange={e => setSizeFilter(e.target.value)}
              className='px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            >
              <option value='all'>All Sizes</option>
              <option value='large'>Large (40+ members)</option>
              <option value='medium'>Medium (20-39 members)</option>
              <option value='small'>Small (&lt;20 members)</option>
            </select>

            <label className='flex items-center gap-2 text-sm'>
              <input
                type='checkbox'
                checked={showSubcommittees}
                onChange={e => setShowSubcommittees(e.target.checked)}
                className='rounded border-gray-300 text-blue-600 focus:ring-blue-500'
              />
              Show Subcommittees
            </label>
          </div>
        </div>

        {/* Stats */}
        <div className='flex items-center justify-between mt-4 text-sm text-gray-600'>
          <div className='flex items-center gap-4'>
            <span>{totalCommittees} committees</span>
            {showSubcommittees && (
              <span>{totalSubcommittees} subcommittees</span>
            )}
          </div>
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className='text-blue-600 hover:text-blue-800'
            >
              Clear search
            </button>
          )}
        </div>
      </div>

      {/* Hierarchy Tree */}
      <div className='p-6'>
        {Object.keys(filteredData).length === 0 ? (
          <div className='text-center py-8'>
            <Building2 className='h-12 w-12 text-gray-400 mx-auto mb-4' />
            <h4 className='text-lg font-medium text-gray-900 mb-2'>
              No Committees Found
            </h4>
            <p className='text-gray-500'>
              Try adjusting your search criteria or filters to see more results.
            </p>
          </div>
        ) : (
          <div className='space-y-6'>
            {Object.entries(filteredData).map(
              ([chamber, committees]) =>
                committees.length > 0 && (
                  <div key={chamber}>
                    <div className='flex items-center gap-2 mb-4'>
                      <h4 className='text-lg font-semibold text-gray-900'>
                        {chamber} Committees
                      </h4>
                      <span className='text-sm text-gray-500'>
                        ({committees.length})
                      </span>
                    </div>
                    <div className='space-y-3'>
                      {committees.map(committee => (
                        <CommitteeNode
                          key={committee.id}
                          committee={committee}
                        />
                      ))}
                    </div>
                  </div>
                )
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className='border-t border-gray-200 p-6 bg-gray-50'>
        <div className='grid grid-cols-1 md:grid-cols-3 gap-6'>
          <div>
            <h4 className='text-sm font-semibold text-gray-700 mb-2'>
              Chamber Types
            </h4>
            <div className='space-y-1'>
              {Object.entries(CHAMBER_COLORS).map(([chamber, styles]) => (
                <div key={chamber} className='flex items-center gap-2'>
                  <div
                    className={`w-3 h-3 rounded ${styles.bg} ${styles.border} border`}
                  />
                  <span className='text-sm text-gray-600'>{chamber}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className='text-sm font-semibold text-gray-700 mb-2'>Icons</h4>
            <div className='space-y-1 text-sm text-gray-600'>
              <div className='flex items-center gap-2'>
                <Users size={14} />
                <span>Member count</span>
              </div>
              <div className='flex items-center gap-2'>
                <FileText size={14} />
                <span>Active bills</span>
              </div>
              <div className='flex items-center gap-2'>
                <ExternalLink size={14} />
                <span>Official website</span>
              </div>
            </div>
          </div>

          <div>
            <h4 className='text-sm font-semibold text-gray-700 mb-2'>
              Navigation
            </h4>
            <div className='space-y-1 text-sm text-gray-600'>
              <div>Click committee names to view details</div>
              <div>Click chevrons to expand/collapse</div>
              <div>Use filters to refine view</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CommitteeHierarchy;
