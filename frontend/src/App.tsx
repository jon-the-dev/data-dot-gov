import {
  Users,
  BarChart3,
  FileText,
  Home,
  Vote,
  Building2,
  Search,
  Download,
  Menu,
  X,
} from 'lucide-react';
import { useState, useEffect, Suspense } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  useLocation,
} from 'react-router-dom';

import BillDetail from '@/components/BillDetail';
import Dashboard from '@/components/Dashboard';
import Members from '@/components/Members';
import PartyComparison from '@/components/PartyComparison';
import BillTracker from '@/features/bills/BillTracker';
import CategoryAnalysis from '@/features/bills/CategoryAnalysis';
import MemberDetail from '@/features/members/MemberProfile';
import MemberSearch from '@/features/members/MemberSearch';
import VoteBreakdown from '@/features/votes/VoteBreakdown';
import DataService from '@/services/dataService';
import type { DashboardData } from '@/types';

import './App.css';

// Loading Component
function LoadingSpinner() {
  return (
    <div className='flex items-center justify-center h-64'>
      <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600' />
    </div>
  );
}

// Error Boundary Component
function ErrorBoundary({
  children,
  error,
}: {
  children: React.ReactNode;
  error?: string;
}) {
  if (error) {
    return (
      <div className='bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg'>
        {error}
      </div>
    );
  }
  return <>{children}</>;
}

// Committee Components
function CommitteesList() {
  return (
    <div className='bg-white rounded-lg shadow-sm p-6'>
      <h1 className='text-2xl font-bold text-gray-900 mb-4'>
        Congressional Committees
      </h1>
      <div className='bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg'>
        <div className='flex items-center gap-2'>
          <Building2 size={20} />
          <span className='font-medium'>Committee Analysis Coming Soon</span>
        </div>
        <p className='mt-2 text-sm'>
          Comprehensive committee data, membership, and bill tracking
          functionality is in development.
        </p>
      </div>
    </div>
  );
}

function CommitteeAnalysis() {
  return (
    <div className='bg-white rounded-lg shadow-sm p-6'>
      <h1 className='text-2xl font-bold text-gray-900 mb-4'>
        Committee Analysis
      </h1>
      <div className='bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg'>
        <div className='flex items-center gap-2'>
          <Building2 size={20} />
          <span className='font-medium'>
            Deep Committee Analytics Coming Soon
          </span>
        </div>
        <p className='mt-2 text-sm'>
          Advanced committee performance metrics, bill flow analysis, and
          cross-committee collaboration insights will be available here.
        </p>
      </div>
    </div>
  );
}

function CommitteeDetail() {
  return (
    <div className='bg-white rounded-lg shadow-sm p-6'>
      <h1 className='text-2xl font-bold text-gray-900 mb-4'>
        Committee Details
      </h1>
      <div className='bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded-lg'>
        <div className='flex items-center gap-2'>
          <Building2 size={20} />
          <span className='font-medium'>Committee Details Coming Soon</span>
        </div>
        <p className='mt-2 text-sm'>
          Individual committee analysis, member details, and bill processing
          data will be available here.
        </p>
      </div>
    </div>
  );
}

// Enhanced Navigation
function Navigation() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/' },
    {
      id: 'members',
      label: 'Members',
      icon: Users,
      path: '/members',
      submenu: [
        { label: 'All Members', path: '/members' },
        { label: 'Search Members', path: '/members/search' },
      ],
    },
    {
      id: 'bills',
      label: 'Bills',
      icon: FileText,
      path: '/bills',
      submenu: [
        { label: 'Bill Tracker', path: '/bills' },
        { label: 'Category Analysis', path: '/bills/categories' },
      ],
    },
    {
      id: 'committees',
      label: 'Committees',
      icon: Building2,
      path: '/committees',
      submenu: [
        { label: 'All Committees', path: '/committees' },
        { label: 'Committee Analysis', path: '/committees/analysis' },
      ],
    },
    { id: 'votes', label: 'Votes', icon: Vote, path: '/votes' },
    { id: 'lobbying', label: 'Lobbying', icon: Building2, path: '/lobbying' },
    {
      id: 'party-comparison',
      label: 'Party Analysis',
      icon: BarChart3,
      path: '/party-comparison',
    },
  ];

  const isActiveTab = (tab: { path: string }) => {
    if (tab.path === '/' && location.pathname === '/') return true;
    if (tab.path !== '/' && location.pathname.startsWith(tab.path)) return true;
    return false;
  };

  return (
    <nav className='bg-white shadow-sm border-b'>
      <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
        {/* Desktop Navigation */}
        <div className='hidden lg:flex space-x-8'>
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive = isActiveTab(tab);

            return (
              <div key={tab.id} className='relative group'>
                <Link
                  to={tab.path}
                  className={`
                    flex items-center gap-2 px-3 py-4 text-sm font-medium border-b-2 transition-colors
                    ${
                      isActive
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon size={18} />
                  {tab.label}
                </Link>

                {/* Dropdown menu */}
                {tab.submenu && (
                  <div className='absolute top-full left-0 w-48 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50'>
                    <div className='py-2'>
                      {tab.submenu.map(item => (
                        <Link
                          key={item.path}
                          to={item.path}
                          className='block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100'
                        >
                          {item.label}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Mobile Navigation */}
        <div className='lg:hidden flex items-center justify-between py-4'>
          <div className='flex items-center'>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className='p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100'
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <span className='ml-3 text-lg font-medium text-gray-900'>
              Congressional Portal
            </span>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className='lg:hidden border-t border-gray-200 py-2'>
            {tabs.map(tab => {
              const Icon = tab.icon;
              const isActive = isActiveTab(tab);

              return (
                <div key={tab.id}>
                  <Link
                    to={tab.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`
                      flex items-center gap-3 px-3 py-3 text-sm font-medium rounded-lg transition-colors
                      ${
                        isActive
                          ? 'bg-blue-50 text-blue-600'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }
                    `}
                  >
                    <Icon size={18} />
                    {tab.label}
                  </Link>
                  {tab.submenu && isActive && (
                    <div className='ml-8 space-y-1'>
                      {tab.submenu.map(item => (
                        <Link
                          key={item.path}
                          to={item.path}
                          onClick={() => setMobileMenuOpen(false)}
                          className='block px-3 py-2 text-xs text-gray-600 hover:text-gray-900'
                        >
                          {item.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
}

// Main App Content
function AppContent() {
  const [data, setData] = useState<DashboardData>({
    membersSummary: null,
    billsIndex: null,
    comprehensiveAnalysis: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setData(prev => ({ ...prev, loading: true, error: null }));

      const [membersSummary, billsIndex, comprehensiveAnalysis] =
        await Promise.all([
          DataService.loadMembersSummary(),
          DataService.loadBillsIndex(),
          DataService.loadComprehensiveAnalysis(),
        ]);

      setData({
        membersSummary: membersSummary as DashboardData['membersSummary'],
        billsIndex: billsIndex as DashboardData['billsIndex'],
        comprehensiveAnalysis:
          comprehensiveAnalysis as DashboardData['comprehensiveAnalysis'],
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Error loading data:', error);
      setData(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to load congressional data. Please try again later.',
      }));
    }
  };

  if (data.loading) {
    return <LoadingSpinner />;
  }

  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          {/* Dashboard */}
          <Route path='/' element={<Dashboard data={data} />} />

          {/* Members */}
          <Route path='/members' element={<Members data={data} />} />
          <Route path='/members/search' element={<MemberSearch />} />
          <Route path='/members/:memberId' element={<MemberDetail />} />

          {/* Bills */}
          <Route path='/bills' element={<BillTracker />} />
          <Route path='/bills/categories' element={<CategoryAnalysis />} />
          <Route path='/bills/:billId' element={<BillDetail />} />

          {/* Committees */}
          <Route path='/committees' element={<CommitteesList />} />
          <Route path='/committees/analysis' element={<CommitteeAnalysis />} />
          <Route
            path='/committees/:committeeId'
            element={<CommitteeDetail />}
          />

          {/* Votes */}
          <Route
            path='/votes'
            element={<div>Votes Dashboard Coming Soon</div>}
          />
          <Route path='/votes/:voteId' element={<VoteBreakdown />} />

          {/* Lobbying */}
          <Route
            path='/lobbying'
            element={<div>Lobbying Dashboard Coming Soon</div>}
          />

          {/* Legacy Routes */}
          <Route
            path='/party-comparison'
            element={<PartyComparison data={data} />}
          />

          {/* 404 */}
          <Route
            path='*'
            element={
              <div className='text-center py-8'>
                <h2 className='text-2xl font-bold text-gray-900 mb-4'>
                  Page Not Found
                </h2>
                <p className='text-gray-600 mb-4'>
                  The page you&apos;re looking for doesn&apos;t exist.
                </p>
                <Link to='/' className='text-blue-600 hover:text-blue-800'>
                  Return to Dashboard
                </Link>
              </div>
            }
          />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <div className='min-h-screen bg-gray-50'>
        {/* Header */}
        <header className='bg-white shadow-sm border-b sticky top-0 z-40'>
          <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
            <div className='flex items-center justify-between h-16'>
              <div className='flex items-center'>
                <Link
                  to='/'
                  className='text-2xl font-bold text-gray-900 hover:text-blue-600 transition-colors'
                >
                  Congressional Transparency Portal
                </Link>
              </div>
              <div className='hidden sm:flex items-center gap-4 text-sm text-gray-600'>
                <span className='flex items-center gap-2'>
                  <BarChart3 size={16} />
                  118th Congress Data
                </span>
                <button className='flex items-center gap-2 text-blue-600 hover:text-blue-800'>
                  <Download size={16} />
                  Export Data
                </button>
                <button className='flex items-center gap-2 text-gray-600 hover:text-gray-800'>
                  <Search size={16} />
                  Search
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8'>
          <AppContent />
        </main>

        {/* Footer */}
        <footer className='bg-white border-t border-gray-200 mt-16'>
          <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8'>
            <div className='flex flex-col md:flex-row md:items-center md:justify-between'>
              <div>
                <p className='text-sm text-gray-600'>
                  Congressional Transparency Portal • Built for government
                  accountability
                </p>
                <p className='text-xs text-gray-500 mt-1'>
                  Data sourced from Congress.gov and Senate.gov APIs
                </p>
              </div>
              <div className='flex gap-4 mt-4 md:mt-0 text-sm text-gray-600'>
                <a
                  href='https://congress.gov'
                  target='_blank'
                  rel='noopener noreferrer'
                  className='hover:text-gray-900'
                >
                  Congress.gov
                </a>
                <a
                  href='https://senate.gov'
                  target='_blank'
                  rel='noopener noreferrer'
                  className='hover:text-gray-900'
                >
                  Senate.gov
                </a>
                <a
                  href='https://github.com'
                  target='_blank'
                  rel='noopener noreferrer'
                  className='hover:text-gray-900'
                >
                  Source Code
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
