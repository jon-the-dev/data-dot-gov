import {
  FileText,
  Download,
  ExternalLink,
  Search,
  Filter,
  Calendar,
  Clock,
  Tag,
  Eye,
  AlertCircle,
  FolderOpen,
  File,
  Link as LinkIcon,
  Star,
  ChevronRight,
} from 'lucide-react';
import { useState, useEffect, useMemo } from 'react';
import DataService from '../services/dataService';

function CommitteeDocuments({ committeeId, loading = false }) {
  const [documents, setDocuments] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortBy, setSortBy] = useState('date'); // date, title, type
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    if (committeeId) {
      loadDocumentsData();
    }
  }, [committeeId]);

  const loadDocumentsData = async () => {
    try {
      setDataLoading(true);
      setError(null);

      // Since documents endpoint may not be implemented, provide mock data
      const mockDocuments = [
        {
          id: `${committeeId}_doc_1`,
          title: 'Committee Report on Healthcare Accessibility Act',
          type: 'report',
          category: 'committee_report',
          date: '2024-09-25T00:00:00Z',
          size: '2.4 MB',
          pages: 45,
          description: 'Comprehensive committee report analyzing the Healthcare Accessibility Act, including minority views and recommendations.',
          bill_number: 'H.R. 2345',
          status: 'published',
          public: true,
          downloads: 1247,
          url: '#',
          summary: 'Details committee findings on healthcare accessibility legislation, including cost analysis and implementation recommendations.',
          tags: ['healthcare', 'accessibility', 'committee report', 'bipartisan'],
        },
        {
          id: `${committeeId}_doc_2`,
          title: 'Infrastructure Investment Analysis - Supplemental Report',
          type: 'analysis',
          category: 'research',
          date: '2024-09-18T00:00:00Z',
          size: '1.8 MB',
          pages: 32,
          description: 'Economic analysis of proposed infrastructure investments and their projected impact on job creation and economic growth.',
          bill_number: 'H.R. 1234',
          status: 'published',
          public: true,
          downloads: 892,
          url: '#',
          summary: 'Quantitative analysis of infrastructure spending proposals with state-by-state economic impact projections.',
          tags: ['infrastructure', 'economic analysis', 'jobs', 'investment'],
        },
        {
          id: `${committeeId}_doc_3`,
          title: 'Meeting Minutes - September 20, 2024',
          type: 'minutes',
          category: 'meeting_record',
          date: '2024-09-22T00:00:00Z',
          size: '456 KB',
          pages: 12,
          description: 'Official minutes from the committee business meeting held on September 20, 2024.',
          status: 'published',
          public: true,
          downloads: 234,
          url: '#',
          summary: 'Records of committee decisions, votes taken, and administrative actions from the September business meeting.',
          tags: ['meeting minutes', 'administrative', 'official record'],
          meeting_date: '2024-09-20',
        },
        {
          id: `${committeeId}_doc_4`,
          title: 'Climate Change Policy Framework - Discussion Draft',
          type: 'draft',
          category: 'legislation',
          date: '2024-09-15T00:00:00Z',
          size: '1.2 MB',
          pages: 28,
          description: 'Working draft of climate change policy framework for committee consideration.',
          status: 'draft',
          public: true,
          downloads: 567,
          url: '#',
          summary: 'Preliminary policy framework addressing climate adaptation and mitigation strategies.',
          tags: ['climate change', 'policy framework', 'draft', 'environment'],
          version: '2.1',
        },
        {
          id: `${committeeId}_doc_5`,
          title: 'Witness Testimony - Healthcare Hearing (September 18)',
          type: 'testimony',
          category: 'hearing_record',
          date: '2024-09-19T00:00:00Z',
          size: '3.1 MB',
          pages: 67,
          description: 'Compiled written testimony from witnesses at the September 18 healthcare accessibility hearing.',
          status: 'published',
          public: true,
          downloads: 445,
          url: '#',
          summary: 'Written statements from government officials, experts, and advocates on healthcare accessibility.',
          tags: ['testimony', 'healthcare', 'hearing record', 'witnesses'],
          hearing_date: '2024-09-18',
          witnesses: 8,
        },
        {
          id: `${committeeId}_doc_6`,
          title: 'Budget Justification FY 2025',
          type: 'budget',
          category: 'administrative',
          date: '2024-09-10T00:00:00Z',
          size: '892 KB',
          pages: 15,
          description: 'Committee budget justification and resource allocation for fiscal year 2025.',
          status: 'published',
          public: false,
          downloads: 89,
          url: '#',
          summary: 'Detailed budget request including staffing, operational expenses, and special projects.',
          tags: ['budget', 'fiscal year 2025', 'administrative', 'internal'],
          restricted: true,
        },
        {
          id: `${committeeId}_doc_7`,
          title: 'Markup Transcript - Infrastructure Investment Act',
          type: 'transcript',
          category: 'meeting_record',
          date: '2024-09-12T00:00:00Z',
          size: '2.7 MB',
          pages: 89,
          description: 'Official stenographic transcript of the markup session for H.R. 1234.',
          bill_number: 'H.R. 1234',
          status: 'published',
          public: true,
          downloads: 623,
          url: '#',
          summary: 'Complete verbatim record of the markup proceedings including all statements and votes.',
          tags: ['transcript', 'markup', 'infrastructure', 'official record'],
          meeting_date: '2024-09-12',
        },
        {
          id: `${committeeId}_doc_8`,
          title: 'Policy Brief: Small Business Support Initiatives',
          type: 'brief',
          category: 'research',
          date: '2024-09-08T00:00:00Z',
          size: '745 KB',
          pages: 18,
          description: 'Policy brief examining various small business support initiatives and their effectiveness.',
          status: 'published',
          public: true,
          downloads: 356,
          url: '#',
          summary: 'Analysis of federal programs supporting small businesses with policy recommendations.',
          tags: ['small business', 'policy brief', 'economic policy', 'research'],
        },
      ];

      setDocuments(mockDocuments);
    } catch (err) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents data');
    } finally {
      setDataLoading(false);
    }
  };

  // Get document categories
  const categories = useMemo(() => {
    const categorySet = new Set(documents.map(doc => doc.category));
    return Array.from(categorySet).sort();
  }, [documents]);

  // Filter and search documents
  const filteredDocuments = useMemo(() => {
    let filtered = [...documents];

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(doc => doc.category === selectedCategory);
    }

    // Filter by type
    if (filterType !== 'all') {
      if (filterType === 'public') {
        filtered = filtered.filter(doc => doc.public === true);
      } else if (filterType === 'restricted') {
        filtered = filtered.filter(doc => doc.public === false);
      } else {
        filtered = filtered.filter(doc => doc.type === filterType);
      }
    }

    // Search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(doc =>
        doc.title.toLowerCase().includes(search) ||
        doc.description.toLowerCase().includes(search) ||
        doc.summary?.toLowerCase().includes(search) ||
        doc.tags?.some(tag => tag.toLowerCase().includes(search)) ||
        doc.bill_number?.toLowerCase().includes(search)
      );
    }

    // Sort documents
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'title':
          return a.title.localeCompare(b.title);
        case 'type':
          return a.type.localeCompare(b.type);
        case 'date':
        default:
          return new Date(b.date) - new Date(a.date);
      }
    });
  }, [documents, selectedCategory, filterType, searchTerm, sortBy]);

  // Get document type styling and icon
  const getDocumentTypeInfo = (type) => {
    switch (type) {
      case 'report':
        return {
          icon: FileText,
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          border: 'border-blue-200',
          label: 'Report',
        };
      case 'minutes':
        return {
          icon: Clock,
          bg: 'bg-green-100',
          text: 'text-green-800',
          border: 'border-green-200',
          label: 'Minutes',
        };
      case 'transcript':
        return {
          icon: File,
          bg: 'bg-purple-100',
          text: 'text-purple-800',
          border: 'border-purple-200',
          label: 'Transcript',
        };
      case 'testimony':
        return {
          icon: Eye,
          bg: 'bg-orange-100',
          text: 'text-orange-800',
          border: 'border-orange-200',
          label: 'Testimony',
        };
      case 'analysis':
        return {
          icon: Star,
          bg: 'bg-indigo-100',
          text: 'text-indigo-800',
          border: 'border-indigo-200',
          label: 'Analysis',
        };
      case 'draft':
        return {
          icon: FileText,
          bg: 'bg-yellow-100',
          text: 'text-yellow-800',
          border: 'border-yellow-200',
          label: 'Draft',
        };
      case 'budget':
        return {
          icon: FolderOpen,
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200',
          label: 'Budget',
        };
      case 'brief':
        return {
          icon: FileText,
          bg: 'bg-teal-100',
          text: 'text-teal-800',
          border: 'border-teal-200',
          label: 'Brief',
        };
      default:
        return {
          icon: File,
          bg: 'bg-gray-100',
          text: 'text-gray-800',
          border: 'border-gray-200',
          label: 'Document',
        };
    }
  };

  const formatFileSize = (sizeStr) => {
    if (!sizeStr) return 'Unknown';
    return sizeStr;
  };

  // Loading state
  if (loading || dataLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Committee Documents</h3>
        </div>

        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
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
          <FileText className="h-6 w-6 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Committee Documents</h3>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <AlertCircle className="mx-auto text-red-500 mb-3" size={32} />
          <h4 className="text-md font-medium text-red-800 mb-2">Error Loading Documents</h4>
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const DocumentCard = ({ document }) => {
    const typeInfo = getDocumentTypeInfo(document.type);
    const TypeIcon = typeInfo.icon;

    return (
      <div className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
        <div className="flex items-start gap-4">
          <div className={`p-3 ${typeInfo.bg} rounded-lg flex-shrink-0`}>
            <TypeIcon className={`h-6 w-6 ${typeInfo.text}`} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${typeInfo.bg} ${typeInfo.text} ${typeInfo.border}`}
                  >
                    {typeInfo.label}
                  </span>
                  {!document.public && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border border-orange-200 bg-orange-100 text-orange-800">
                      Restricted
                    </span>
                  )}
                  {document.status === 'draft' && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border border-yellow-200 bg-yellow-100 text-yellow-800">
                      Draft
                    </span>
                  )}
                </div>
                <h4 className="font-semibold text-gray-900 text-lg mb-2 hover:text-blue-600 cursor-pointer">
                  {document.title}
                </h4>
                <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                  {document.summary || document.description}
                </p>
              </div>
            </div>

            {/* Document metadata */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-sm">
              <div className="flex items-center gap-2">
                <Calendar size={14} className="text-gray-400" />
                <span className="text-gray-900">
                  {new Date(document.date).toLocaleDateString()}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <FileText size={14} className="text-gray-400" />
                <span className="text-gray-900">
                  {document.pages} pages
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Download size={14} className="text-gray-400" />
                <span className="text-gray-900">
                  {formatFileSize(document.size)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Eye size={14} className="text-gray-400" />
                <span className="text-gray-900">
                  {document.downloads} downloads
                </span>
              </div>
            </div>

            {/* Associated bill */}
            {document.bill_number && (
              <div className="mb-3">
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border border-blue-200 bg-blue-50 text-blue-800">
                  <LinkIcon size={10} />
                  {document.bill_number}
                </span>
              </div>
            )}

            {/* Tags */}
            {document.tags && document.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-4">
                {document.tags.slice(0, 4).map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border border-gray-300 bg-gray-100 text-gray-700"
                  >
                    <Tag size={8} />
                    {tag}
                  </span>
                ))}
                {document.tags.length > 4 && (
                  <span className="text-xs text-gray-500">
                    +{document.tags.length - 4} more
                  </span>
                )}
              </div>
            )}

            {/* Action buttons */}
            <div className="flex items-center gap-3 pt-3 border-t border-gray-200">
              <a
                href={document.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors"
              >
                <Download size={14} />
                <span>Download</span>
              </a>
              <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded hover:bg-gray-50 transition-colors">
                <Eye size={14} />
                <span>Preview</span>
              </button>
              <button className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 ml-auto">
                <span>View Details</span>
                <ChevronRight size={12} />
              </button>
            </div>
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
            <FileText className="h-6 w-6 text-green-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Committee Documents</h3>
              <p className="text-sm text-gray-600">
                {filteredDocuments.length} document{filteredDocuments.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </div>

        {/* Search and Filter Controls */}
        <div className="space-y-3">
          <div className="flex flex-col lg:flex-row gap-3">
            <div className="flex-1">
              <div className="relative">
                <Search
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                  size={16}
                />
                <input
                  type="text"
                  placeholder="Search documents by title, content, tags, or bill number..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <select
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                <option value="all">All Categories</option>
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </option>
                ))}
              </select>
              <select
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="all">All Documents</option>
                <option value="public">Public</option>
                <option value="restricted">Restricted</option>
                <option value="report">Reports</option>
                <option value="minutes">Minutes</option>
                <option value="transcript">Transcripts</option>
                <option value="testimony">Testimony</option>
              </select>
              <select
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="date">Sort by Date</option>
                <option value="title">Sort by Title</option>
                <option value="type">Sort by Type</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Documents List */}
      <div className="p-6">
        {filteredDocuments.length > 0 ? (
          <div className="space-y-6">
            {filteredDocuments.map((document) => (
              <DocumentCard key={document.id} document={document} />
            ))}
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <FileText className="mx-auto text-gray-400 mb-4" size={48} />
            <h4 className="text-lg font-medium text-gray-700 mb-2">
              No documents found
            </h4>
            <p className="text-gray-500">
              {searchTerm || filterType !== 'all' || selectedCategory !== 'all'
                ? 'Try adjusting your search or filter criteria'
                : 'This committee has no documents available at this time.'}
            </p>
            {(searchTerm || filterType !== 'all' || selectedCategory !== 'all') && (
              <button
                onClick={() => {
                  setSearchTerm('');
                  setFilterType('all');
                  setSelectedCategory('all');
                }}
                className="mt-3 text-blue-600 hover:text-blue-700 text-sm"
              >
                Clear filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Document Type Summary */}
      {documents.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-xl font-bold text-blue-700">
                {documents.filter(d => d.type === 'report').length}
              </p>
              <p className="text-xs text-blue-600">Reports</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-xl font-bold text-green-700">
                {documents.filter(d => d.type === 'minutes').length}
              </p>
              <p className="text-xs text-green-600">Minutes</p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <p className="text-xl font-bold text-purple-700">
                {documents.filter(d => d.type === 'transcript').length}
              </p>
              <p className="text-xs text-purple-600">Transcripts</p>
            </div>
            <div className="p-3 bg-orange-50 rounded-lg">
              <p className="text-xl font-bold text-orange-700">
                {documents.filter(d => d.public === true).length}
              </p>
              <p className="text-xs text-orange-600">Public</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CommitteeDocuments;