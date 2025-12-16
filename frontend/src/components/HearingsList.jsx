import {
  Calendar,
  Clock,
  Users,
  MapPin,
  ExternalLink,
  Search,
  Filter,
  ChevronRight,
  Video,
  FileText,
  AlertCircle,
  Mic,
  Eye,
} from 'lucide-react';
import { useState, useEffect, useMemo } from 'react';
import DataService from '../services/dataService';

function HearingsList({ committeeId, loading = false }) {
  const [hearings, setHearings] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, upcoming, past
  const [selectedHearing, setSelectedHearing] = useState(null);

  useEffect(() => {
    if (committeeId) {
      loadHearingsData();
    }
  }, [committeeId]);

  const loadHearingsData = async () => {
    try {
      setDataLoading(true);
      setError(null);

      // Since hearings endpoint may not be implemented, provide mock data
      const mockHearings = [
        {
          id: `${committeeId}_hearing_1`,
          title: 'Oversight of Federal Healthcare Programs',
          date: '2024-10-15T10:00:00Z',
          time: '10:00 AM EST',
          location: 'Committee Room 216, Hart Senate Office Building',
          type: 'oversight',
          status: 'scheduled',
          description: 'The Committee will hold a hearing to examine the implementation and effectiveness of federal healthcare programs, including Medicare, Medicaid, and the Affordable Care Act.',
          witnesses: [
            {
              name: 'Dr. Sarah Johnson',
              title: 'Administrator, Centers for Medicare & Medicaid Services',
              organization: 'Department of Health and Human Services',
              type: 'government',
            },
            {
              name: 'Prof. Michael Chen',
              title: 'Healthcare Policy Expert',
              organization: 'Georgetown University',
              type: 'expert',
            },
            {
              name: 'Maria Rodriguez',
              title: 'Patient Advocate',
              organization: 'National Patient Rights Association',
              type: 'advocate',
            },
          ],
          webcast_url: 'https://www.senate.gov/live',
          documents: [
            { title: 'Hearing Notice', url: '#' },
            { title: 'Witness List', url: '#' },
          ],
        },
        {
          id: `${committeeId}_hearing_2`,
          title: 'Infrastructure Investment and Economic Growth',
          date: '2024-10-22T14:30:00Z',
          time: '2:30 PM EST',
          location: 'Committee Room 106, Dirksen Senate Office Building',
          type: 'legislative',
          status: 'scheduled',
          description: 'Hearing to examine proposed infrastructure legislation and its potential economic impact on American communities.',
          witnesses: [
            {
              name: 'Secretary Janet Thompson',
              title: 'Secretary of Transportation',
              organization: 'Department of Transportation',
              type: 'government',
            },
            {
              name: 'Robert Kim',
              title: 'Chief Economist',
              organization: 'American Infrastructure Council',
              type: 'expert',
            },
          ],
          webcast_url: 'https://www.senate.gov/live',
          documents: [
            { title: 'Hearing Notice', url: '#' },
            { title: 'Infrastructure Bill Summary', url: '#' },
          ],
        },
        {
          id: `${committeeId}_hearing_3`,
          title: 'Climate Change and Environmental Policy',
          date: '2024-09-18T09:00:00Z',
          time: '9:00 AM EST',
          location: 'Committee Room 216, Hart Senate Office Building',
          type: 'oversight',
          status: 'completed',
          description: 'The Committee held a hearing to examine current climate change mitigation strategies and environmental policy effectiveness.',
          witnesses: [
            {
              name: 'Dr. Emily Rodriguez',
              title: 'Director, National Climate Assessment',
              organization: 'NOAA',
              type: 'government',
            },
            {
              name: 'James Wilson',
              title: 'Environmental Policy Director',
              organization: 'Clean Energy Institute',
              type: 'expert',
            },
          ],
          transcript_url: 'https://www.congress.gov/transcripts',
          video_url: 'https://www.senate.gov/video/archive',
          documents: [
            { title: 'Official Transcript', url: '#' },
            { title: 'Climate Data Report', url: '#' },
            { title: 'Witness Statements', url: '#' },
          ],
        },
        {
          id: `${committeeId}_hearing_4`,
          title: 'Border Security and Immigration Reform',
          date: '2024-09-05T11:00:00Z',
          time: '11:00 AM EST',
          location: 'Committee Room 106, Dirksen Senate Office Building',
          type: 'legislative',
          status: 'completed',
          description: 'Hearing on proposed immigration legislation and border security measures.',
          witnesses: [
            {
              name: 'Director Alexandra Martinez',
              title: 'Director, Immigration and Customs Enforcement',
              organization: 'Department of Homeland Security',
              type: 'government',
            },
            {
              name: 'Prof. David Lee',
              title: 'Immigration Law Professor',
              organization: 'Harvard Law School',
              type: 'expert',
            },
          ],
          transcript_url: 'https://www.congress.gov/transcripts',
          video_url: 'https://www.senate.gov/video/archive',
          documents: [
            { title: 'Official Transcript', url: '#' },
            { title: 'Border Security Report', url: '#' },
          ],
        },
      ];

      setHearings(mockHearings);
    } catch (err) {
      console.error('Error loading hearings:', err);
      setError('Failed to load hearings data');
    } finally {
      setDataLoading(false);
    }
  };

  // Filter and search hearings
  const filteredHearings = useMemo(() => {
    let filtered = [...hearings];

    // Filter by type
    if (filterType === 'upcoming') {
      filtered = filtered.filter(hearing => new Date(hearing.date) > new Date());
    } else if (filterType === 'past') {
      filtered = filtered.filter(hearing => new Date(hearing.date) <= new Date());
    }

    // Search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(hearing =>
        hearing.title.toLowerCase().includes(search) ||
        hearing.description.toLowerCase().includes(search) ||
        hearing.witnesses?.some(witness =>
          witness.name.toLowerCase().includes(search) ||
          witness.organization.toLowerCase().includes(search)
        )
      );
    }

    // Sort by date (upcoming first, then most recent past)
    return filtered.sort((a, b) => {
      const dateA = new Date(a.date);
      const dateB = new Date(b.date);
      const now = new Date();

      if (dateA > now && dateB > now) {
        return dateA - dateB; // Upcoming: earliest first
      } else if (dateA <= now && dateB <= now) {
        return dateB - dateA; // Past: most recent first
      } else {
        return dateA > now ? -1 : 1; // Upcoming before past
      }
    });
  }, [hearings, filterType, searchTerm]);

  // Get hearing status styling
  const getStatusBadge = (hearing) => {
    const date = new Date(hearing.date);
    const now = new Date();
    const isUpcoming = date > now;

    if (isUpcoming) {
      return {
        bg: 'bg-green-100',
        text: 'text-green-800',
        border: 'border-green-200',
        label: 'Upcoming',
      };
    } else {
      return {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        border: 'border-gray-200',
        label: 'Completed',
      };
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'legislative':
        return FileText;
      case 'oversight':
        return Eye;
      default:
        return Mic;
    }
  };

  // Loading state
  if (loading || dataLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">Committee Hearings</h3>
        </div>

        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse border border-gray-200 rounded-lg p-4">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-gray-300 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 bg-gray-300 rounded w-3/4" />
                  <div className="h-4 bg-gray-300 rounded w-1/2" />
                  <div className="h-3 bg-gray-300 rounded w-full" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Mic className="h-6 w-6 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">Committee Hearings</h3>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertCircle className="mx-auto text-red-500 mb-3" size={32} />
          <h4 className="text-md font-medium text-red-800 mb-2">Error Loading Hearings</h4>
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const HearingCard = ({ hearing }) => {
    const statusStyles = getStatusBadge(hearing);
    const TypeIcon = getTypeIcon(hearing.type);
    const isUpcoming = new Date(hearing.date) > new Date();

    return (
      <div
        className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
        onClick={() => setSelectedHearing(hearing)}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3 flex-1">
            <div className="p-2 bg-purple-100 rounded-lg">
              <TypeIcon className="h-5 w-5 text-purple-600" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-gray-900 text-lg mb-2 hover:text-blue-600">
                {hearing.title}
              </h4>
              <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                {hearing.description}
              </p>
            </div>
          </div>
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${statusStyles.bg} ${statusStyles.text} ${statusStyles.border}`}
          >
            {statusStyles.label}
          </span>
        </div>

        {/* Date, Time, Location */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4 text-sm">
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-gray-400" />
            <span className="text-gray-900">
              {new Date(hearing.date).toLocaleDateString()}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-400" />
            <span className="text-gray-900">{hearing.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin size={16} className="text-gray-400" />
            <span className="text-gray-900 text-xs">{hearing.location}</span>
          </div>
        </div>

        {/* Witnesses */}
        {hearing.witnesses && hearing.witnesses.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Users size={16} className="text-gray-400" />
              <span className="text-sm font-medium text-gray-700">
                Witnesses ({hearing.witnesses.length})
              </span>
            </div>
            <div className="grid gap-2">
              {hearing.witnesses.slice(0, 2).map((witness, index) => (
                <div key={index} className="text-xs bg-gray-50 p-2 rounded">
                  <p className="font-medium text-gray-900">{witness.name}</p>
                  <p className="text-gray-600">{witness.title}</p>
                  <p className="text-gray-500">{witness.organization}</p>
                </div>
              ))}
              {hearing.witnesses.length > 2 && (
                <p className="text-xs text-gray-500">
                  +{hearing.witnesses.length - 2} more witnesses
                </p>
              )}
            </div>
          </div>
        )}

        {/* Action Links */}
        <div className="flex items-center gap-3 pt-3 border-t border-gray-200">
          {isUpcoming && hearing.webcast_url && (
            <a
              href={hearing.webcast_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
              onClick={(e) => e.stopPropagation()}
            >
              <Video size={12} />
              <span>Watch Live</span>
            </a>
          )}
          {!isUpcoming && hearing.video_url && (
            <a
              href={hearing.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
              onClick={(e) => e.stopPropagation()}
            >
              <Video size={12} />
              <span>Video Archive</span>
            </a>
          )}
          {hearing.documents && hearing.documents.length > 0 && (
            <span className="flex items-center gap-1 text-xs text-gray-600">
              <FileText size={12} />
              <span>{hearing.documents.length} documents</span>
            </span>
          )}
          <div className="flex items-center gap-1 text-xs text-blue-600 ml-auto">
            <span>View Details</span>
            <ChevronRight size={12} />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Mic className="h-6 w-6 text-purple-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Committee Hearings</h3>
              <p className="text-sm text-gray-600">
                {filteredHearings.length} hearing{filteredHearings.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </div>

        {/* Search and Filter Controls */}
        <div className="flex flex-col md:flex-row gap-3">
          <div className="flex-1">
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                size={16}
              />
              <input
                type="text"
                placeholder="Search hearings by title, topic, or witness..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 text-sm"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="all">All Hearings</option>
              <option value="upcoming">Upcoming</option>
              <option value="past">Past</option>
            </select>
          </div>
        </div>
      </div>

      {/* Hearings List */}
      <div className="p-6">
        {filteredHearings.length > 0 ? (
          <div className="space-y-4">
            {filteredHearings.map((hearing) => (
              <HearingCard key={hearing.id} hearing={hearing} />
            ))}
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <Mic className="mx-auto text-gray-400 mb-4" size={48} />
            <h4 className="text-lg font-medium text-gray-700 mb-2">
              No hearings found
            </h4>
            <p className="text-gray-500">
              {searchTerm || filterType !== 'all'
                ? 'Try adjusting your search or filter criteria'
                : 'This committee has no scheduled hearings at this time.'}
            </p>
            {(searchTerm || filterType !== 'all') && (
              <button
                onClick={() => {
                  setSearchTerm('');
                  setFilterType('all');
                }}
                className="mt-3 text-blue-600 hover:text-blue-700 text-sm"
              >
                Clear filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Quick Stats */}
      {hearings.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-xl font-bold text-green-700">
                {hearings.filter(h => new Date(h.date) > new Date()).length}
              </p>
              <p className="text-xs text-green-600">Upcoming</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xl font-bold text-gray-700">
                {hearings.filter(h => new Date(h.date) <= new Date()).length}
              </p>
              <p className="text-xs text-gray-600">Completed</p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <p className="text-xl font-bold text-purple-700">
                {hearings.reduce((total, h) => total + (h.witnesses?.length || 0), 0)}
              </p>
              <p className="text-xs text-purple-600">Total Witnesses</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HearingsList;