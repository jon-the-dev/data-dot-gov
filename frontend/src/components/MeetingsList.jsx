import {
  Calendar,
  Clock,
  Users,
  MapPin,
  FileText,
  CheckCircle,
  AlertCircle,
  Search,
  Filter,
  ChevronRight,
  Gavel,
  Building2,
  Eye,
  ExternalLink,
} from 'lucide-react';
import { useState, useEffect, useMemo } from 'react';
import DataService from '../services/dataService';

function MeetingsList({ committeeId, loading = false }) {
  const [meetings, setMeetings] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // all, upcoming, past, business, markup
  const [selectedMeeting, setSelectedMeeting] = useState(null);

  useEffect(() => {
    if (committeeId) {
      loadMeetingsData();
    }
  }, [committeeId]);

  const loadMeetingsData = async () => {
    try {
      setDataLoading(true);
      setError(null);

      // Since meetings endpoint may not be implemented, provide mock data
      const mockMeetings = [
        {
          id: `${committeeId}_meeting_1`,
          title: 'Committee Business Meeting',
          date: '2024-10-18T10:00:00Z',
          time: '10:00 AM EST',
          location: 'Committee Room 216, Hart Senate Office Building',
          type: 'business',
          status: 'scheduled',
          description: 'Regular committee business meeting to discuss upcoming legislation and administrative matters.',
          agenda: [
            'Approval of previous meeting minutes',
            'Review of pending nominations',
            'Discussion of H.R. 2345 - Healthcare Accessibility Act',
            'Budget considerations for FY 2025',
            'New business',
          ],
          chair: 'Senator Smith',
          expected_duration: '2 hours',
          public_access: true,
          livestream_url: 'https://www.senate.gov/live',
          documents: [
            { title: 'Meeting Notice', url: '#' },
            { title: 'Draft Agenda', url: '#' },
          ],
        },
        {
          id: `${committeeId}_meeting_2`,
          title: 'Markup Session - Infrastructure Investment Act',
          date: '2024-10-25T14:30:00Z',
          time: '2:30 PM EST',
          location: 'Committee Room 106, Dirksen Senate Office Building',
          type: 'markup',
          status: 'scheduled',
          description: 'Committee markup session for H.R. 1234 - Infrastructure Investment and Jobs Act. Members will consider amendments and vote on final passage.',
          agenda: [
            'Opening remarks by Chairman',
            'Review of bill text',
            'Consideration of proposed amendments',
            'Member statements',
            'Final vote on passage',
          ],
          chair: 'Senator Johnson',
          bills: [
            {
              number: 'H.R. 1234',
              title: 'Infrastructure Investment and Jobs Act',
              sponsor: 'Rep. Wilson',
            },
          ],
          expected_duration: '3-4 hours',
          public_access: true,
          livestream_url: 'https://www.senate.gov/live',
          documents: [
            { title: 'Bill Text', url: '#' },
            { title: 'Amendment List', url: '#' },
            { title: 'Committee Report Draft', url: '#' },
          ],
        },
        {
          id: `${committeeId}_meeting_3`,
          title: 'Executive Session - Nominations Review',
          date: '2024-10-30T11:00:00Z',
          time: '11:00 AM EST',
          location: 'Committee Room 216, Hart Senate Office Building',
          type: 'executive',
          status: 'scheduled',
          description: 'Closed executive session to review and vote on pending nominations.',
          agenda: [
            'Review of nominee qualifications',
            'Discussion of background checks',
            'Committee vote on nominations',
          ],
          chair: 'Senator Smith',
          expected_duration: '1 hour',
          public_access: false,
          documents: [
            { title: 'Nominee Files (Confidential)', url: '#' },
          ],
        },
        {
          id: `${committeeId}_meeting_4`,
          title: 'Committee Business Meeting',
          date: '2024-09-20T09:30:00Z',
          time: '9:30 AM EST',
          location: 'Committee Room 106, Dirksen Senate Office Building',
          type: 'business',
          status: 'completed',
          description: 'Regular business meeting to address administrative matters and upcoming hearings.',
          agenda: [
            'Approval of meeting minutes from September 6th',
            'Schedule confirmation for upcoming hearings',
            'Discussion of committee budget allocation',
            'Staff appointments',
          ],
          chair: 'Senator Smith',
          expected_duration: '1.5 hours',
          actual_duration: '1 hour 45 minutes',
          public_access: true,
          outcomes: [
            'Minutes approved unanimously',
            'Three hearings scheduled for October',
            'Budget allocation approved with amendments',
            'Two new staff members appointed',
          ],
          documents: [
            { title: 'Official Minutes', url: '#' },
            { title: 'Meeting Summary', url: '#' },
            { title: 'Action Items List', url: '#' },
          ],
        },
        {
          id: `${committeeId}_meeting_5`,
          title: 'Markup Session - Climate Action Framework',
          date: '2024-09-12T13:00:00Z',
          time: '1:00 PM EST',
          location: 'Committee Room 216, Hart Senate Office Building',
          type: 'markup',
          status: 'completed',
          description: 'Committee markup of S. 567 - Climate Action and Environmental Protection Framework.',
          agenda: [
            'Opening statements',
            'Bill overview by staff',
            'Amendment consideration',
            'Final passage vote',
          ],
          chair: 'Senator Johnson',
          bills: [
            {
              number: 'S. 567',
              title: 'Climate Action and Environmental Protection Framework',
              sponsor: 'Sen. Martinez',
            },
          ],
          expected_duration: '3 hours',
          actual_duration: '4 hours 15 minutes',
          public_access: true,
          vote_result: {
            passed: true,
            vote_breakdown: {
              yes: 14,
              no: 8,
              abstain: 0,
            },
          },
          outcomes: [
            'Bill reported favorably to full Senate',
            '12 amendments considered, 4 adopted',
            'Committee report filed',
          ],
          documents: [
            { title: 'Official Transcript', url: '#' },
            { title: 'Amendment Log', url: '#' },
            { title: 'Committee Report', url: '#' },
            { title: 'Vote Tally', url: '#' },
          ],
        },
      ];

      setMeetings(mockMeetings);
    } catch (err) {
      console.error('Error loading meetings:', err);
      setError('Failed to load meetings data');
    } finally {
      setDataLoading(false);
    }
  };

  // Filter and search meetings
  const filteredMeetings = useMemo(() => {
    let filtered = [...meetings];

    // Filter by type
    if (filterType === 'upcoming') {
      filtered = filtered.filter(meeting => new Date(meeting.date) > new Date());
    } else if (filterType === 'past') {
      filtered = filtered.filter(meeting => new Date(meeting.date) <= new Date());
    } else if (filterType !== 'all') {
      filtered = filtered.filter(meeting => meeting.type === filterType);
    }

    // Search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(meeting =>
        meeting.title.toLowerCase().includes(search) ||
        meeting.description.toLowerCase().includes(search) ||
        meeting.agenda?.some(item =>
          item.toLowerCase().includes(search)
        ) ||
        meeting.bills?.some(bill =>
          bill.number.toLowerCase().includes(search) ||
          bill.title.toLowerCase().includes(search)
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
  }, [meetings, filterType, searchTerm]);

  // Get meeting type styling and icon
  const getMeetingTypeInfo = (type) => {
    switch (type) {
      case 'business':
        return {
          icon: Building2,
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          border: 'border-blue-200',
          label: 'Business Meeting',
        };
      case 'markup':
        return {
          icon: Gavel,
          bg: 'bg-purple-100',
          text: 'text-purple-800',
          border: 'border-purple-200',
          label: 'Markup Session',
        };
      case 'executive':
        return {
          icon: Eye,
          bg: 'bg-orange-100',
          text: 'text-orange-800',
          border: 'border-orange-200',
          label: 'Executive Session',
        };
      default:
        return {
          icon: Users,
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200',
          label: 'Committee Meeting',
        };
    }
  };

  const getStatusBadge = (meeting) => {
    const date = new Date(meeting.date);
    const now = new Date();
    const isUpcoming = date > now;

    if (isUpcoming) {
      return {
        bg: 'bg-green-100',
        text: 'text-green-800',
        border: 'border-green-200',
        label: 'Scheduled',
        icon: Clock,
      };
    } else {
      return {
        bg: 'bg-gray-100',
        text: 'text-gray-800',
        border: 'border-gray-200',
        label: 'Completed',
        icon: CheckCircle,
      };
    }
  };

  // Loading state
  if (loading || dataLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Committee Meetings</h3>
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
          <Users className="h-6 w-6 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Committee Meetings</h3>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertCircle className="mx-auto text-red-500 mb-3" size={32} />
          <h4 className="text-md font-medium text-red-800 mb-2">Error Loading Meetings</h4>
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const MeetingCard = ({ meeting }) => {
    const typeInfo = getMeetingTypeInfo(meeting.type);
    const statusInfo = getStatusBadge(meeting);
    const TypeIcon = typeInfo.icon;
    const StatusIcon = statusInfo.icon;
    const isUpcoming = new Date(meeting.date) > new Date();

    return (
      <div
        className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
        onClick={() => setSelectedMeeting(meeting)}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-3 flex-1">
            <div className={`p-2 ${typeInfo.bg} rounded-lg`}>
              <TypeIcon className={`h-5 w-5 ${typeInfo.text}`} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${typeInfo.bg} ${typeInfo.text} ${typeInfo.border}`}
                >
                  {typeInfo.label}
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border ${statusInfo.bg} ${statusInfo.text} ${statusInfo.border}`}
                >
                  <StatusIcon size={10} />
                  {statusInfo.label}
                </span>
              </div>
              <h4 className="font-semibold text-gray-900 text-lg mb-2 hover:text-blue-600">
                {meeting.title}
              </h4>
              <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                {meeting.description}
              </p>
            </div>
          </div>
        </div>

        {/* Date, Time, Location */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4 text-sm">
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-gray-400" />
            <span className="text-gray-900">
              {new Date(meeting.date).toLocaleDateString()}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-400" />
            <span className="text-gray-900">{meeting.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin size={16} className="text-gray-400" />
            <span className="text-gray-900 text-xs">{meeting.location}</span>
          </div>
        </div>

        {/* Bills (for markup sessions) */}
        {meeting.bills && meeting.bills.length > 0 && (
          <div className="mb-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Bills Under Consideration:</h5>
            {meeting.bills.map((bill, index) => (
              <div key={index} className="text-xs bg-gray-50 p-2 rounded mb-1">
                <span className="font-medium text-gray-900">{bill.number}</span>
                <span className="text-gray-600"> - {bill.title}</span>
                {bill.sponsor && (
                  <span className="text-gray-500"> (Sponsor: {bill.sponsor})</span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Agenda Preview */}
        {meeting.agenda && meeting.agenda.length > 0 && (
          <div className="mb-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Agenda:</h5>
            <ul className="text-xs text-gray-600 space-y-1">
              {meeting.agenda.slice(0, 3).map((item, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-gray-400">•</span>
                  <span>{item}</span>
                </li>
              ))}
              {meeting.agenda.length > 3 && (
                <li className="text-gray-500 italic">
                  +{meeting.agenda.length - 3} more agenda items
                </li>
              )}
            </ul>
          </div>
        )}

        {/* Results (for completed meetings) */}
        {!isUpcoming && meeting.outcomes && (
          <div className="mb-4">
            <h5 className="text-sm font-medium text-gray-700 mb-2">Outcomes:</h5>
            <ul className="text-xs text-gray-600 space-y-1">
              {meeting.outcomes.slice(0, 2).map((outcome, index) => (
                <li key={index} className="flex items-start gap-2">
                  <CheckCircle size={10} className="text-green-500 mt-0.5" />
                  <span>{outcome}</span>
                </li>
              ))}
              {meeting.outcomes.length > 2 && (
                <li className="text-gray-500 italic">
                  +{meeting.outcomes.length - 2} more outcomes
                </li>
              )}
            </ul>
          </div>
        )}

        {/* Vote Result (for completed markup sessions) */}
        {meeting.vote_result && (
          <div className="mb-4 p-3 bg-green-50 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle size={16} className="text-green-600" />
              <span className="text-sm font-medium text-green-800">
                Bill {meeting.vote_result.passed ? 'Passed' : 'Failed'}
              </span>
            </div>
            <div className="text-xs text-green-700">
              Vote: {meeting.vote_result.vote_breakdown.yes} Yes, {meeting.vote_result.vote_breakdown.no} No
              {meeting.vote_result.vote_breakdown.abstain > 0 &&
                `, ${meeting.vote_result.vote_breakdown.abstain} Abstain`}
            </div>
          </div>
        )}

        {/* Action Links */}
        <div className="flex items-center gap-3 pt-3 border-t border-gray-200">
          {isUpcoming && meeting.livestream_url && meeting.public_access && (
            <a
              href={meeting.livestream_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
              onClick={(e) => e.stopPropagation()}
            >
              <Eye size={12} />
              <span>Watch Live</span>
            </a>
          )}
          {!meeting.public_access && (
            <span className="flex items-center gap-1 text-xs text-orange-600">
              <AlertCircle size={12} />
              <span>Closed Session</span>
            </span>
          )}
          {meeting.documents && meeting.documents.length > 0 && (
            <span className="flex items-center gap-1 text-xs text-gray-600">
              <FileText size={12} />
              <span>{meeting.documents.length} documents</span>
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
            <Users className="h-6 w-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Committee Meetings</h3>
              <p className="text-sm text-gray-600">
                {filteredMeetings.length} meeting{filteredMeetings.length !== 1 ? 's' : ''}
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
                placeholder="Search meetings by title, agenda, or bill number..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="all">All Meetings</option>
              <option value="upcoming">Upcoming</option>
              <option value="past">Past</option>
              <option value="business">Business Meetings</option>
              <option value="markup">Markup Sessions</option>
              <option value="executive">Executive Sessions</option>
            </select>
          </div>
        </div>
      </div>

      {/* Meetings List */}
      <div className="p-6">
        {filteredMeetings.length > 0 ? (
          <div className="space-y-4">
            {filteredMeetings.map((meeting) => (
              <MeetingCard key={meeting.id} meeting={meeting} />
            ))}
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <Users className="mx-auto text-gray-400 mb-4" size={48} />
            <h4 className="text-lg font-medium text-gray-700 mb-2">
              No meetings found
            </h4>
            <p className="text-gray-500">
              {searchTerm || filterType !== 'all'
                ? 'Try adjusting your search or filter criteria'
                : 'This committee has no scheduled meetings at this time.'}
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
      {meetings.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="grid grid-cols-4 gap-3 text-center">
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-lg font-bold text-green-700">
                {meetings.filter(m => new Date(m.date) > new Date()).length}
              </p>
              <p className="text-xs text-green-600">Upcoming</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-lg font-bold text-blue-700">
                {meetings.filter(m => m.type === 'business').length}
              </p>
              <p className="text-xs text-blue-600">Business</p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <p className="text-lg font-bold text-purple-700">
                {meetings.filter(m => m.type === 'markup').length}
              </p>
              <p className="text-xs text-purple-600">Markups</p>
            </div>
            <div className="p-3 bg-orange-50 rounded-lg">
              <p className="text-lg font-bold text-orange-700">
                {meetings.filter(m => m.type === 'executive').length}
              </p>
              <p className="text-xs text-orange-600">Executive</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MeetingsList;