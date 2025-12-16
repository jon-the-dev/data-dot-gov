import {
  Users,
  BarChart3,
  FileText,
  Home,
  Building2,
  DollarSign,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  useLocation,
} from 'react-router-dom';

import BillDetail from './components/BillDetail';
import BillsAnalysis from './components/BillsAnalysis';
import CommitteeDetail from './components/CommitteeDetail';
import CommitteesList from './components/CommitteesList';
import Dashboard from './components/Dashboard';
import Lobbying from './components/Lobbying';
import MemberDetail from './components/MemberDetail';
import Members from './components/Members';
import PartyComparison from './components/PartyComparison';
import SubcommitteeDetail from './components/SubcommitteeDetail';
import DataService from './services/dataService';
import './App.css';

function Navigation() {
  const location = useLocation();

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Home, path: '/' },
    {
      id: 'party-comparison',
      label: 'Party Comparison',
      icon: BarChart3,
      path: '/party-comparison',
    },
    { id: 'bills', label: 'Bills Analysis', icon: FileText, path: '/bills' },
    { id: 'members', label: 'Members', icon: Users, path: '/members' },
    {
      id: 'committees',
      label: 'Committees',
      icon: Building2,
      path: '/committees',
    },
    { id: 'lobbying', label: 'Lobbying', icon: DollarSign, path: '/lobbying' },
  ];

  return (
    <nav className='bg-white shadow-sm'>
      <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
        <div className='flex space-x-8'>
          {tabs.map(tab => {
            const Icon = tab.icon;
            const isActive =
              location.pathname === tab.path ||
              (tab.path === '/' && location.pathname === '/') ||
              (tab.path === '/members' &&
                location.pathname.startsWith('/members')) ||
              (tab.path === '/bills' &&
                location.pathname.startsWith('/bills')) ||
              (tab.path === '/committees' &&
                location.pathname.startsWith('/committees')) ||
              (tab.path === '/lobbying' &&
                location.pathname.startsWith('/lobbying'));

            return (
              <Link
                key={tab.id}
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
            );
          })}
        </div>
      </div>
    </nav>
  );
}

function AppContent() {
  const location = useLocation();
  const [data, setData] = useState({
    membersSummary: null,
    billsIndex: null,
    comprehensiveAnalysis: null,
    loading: false,
    error: null,
  });

  useEffect(() => {
    // Only load initial data for routes that need it
    const needsGlobalData = ['/', '/party-comparison', '/bills'].includes(location.pathname);
    if (needsGlobalData && !data.membersSummary) {
      loadInitialData();
    }
  }, [location.pathname]);

  const loadInitialData = async () => {
    try {
      setData(prev => ({ ...prev, loading: true }));

      const [membersSummary, billsIndex, comprehensiveAnalysis] =
        await Promise.all([
          DataService.loadMembersSummary(),
          DataService.loadBillsIndex(100, 0), // Reduced from 2000 to 100 for faster initial load
          DataService.loadComprehensiveAnalysis(),
        ]);

      setData({
        membersSummary,
        billsIndex,
        comprehensiveAnalysis,
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
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600' />
      </div>
    );
  }

  if (data.error) {
    return (
      <div className='bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg'>
        {data.error}
      </div>
    );
  }

  return (
    <Routes>
      <Route path='/' element={<Dashboard data={data} />} />
      <Route
        path='/party-comparison'
        element={<PartyComparison data={data} />}
      />
      <Route path='/bills' element={<BillsAnalysis data={data} />} />
      <Route path='/bills/:billId' element={<BillDetail />} />
      <Route path='/members' element={<Members data={data} />} />
      <Route path='/members/:memberId' element={<MemberDetail />} />
      <Route path='/committees' element={<CommitteesList />} />
      <Route path='/committees/:committeeId' element={<CommitteeDetail />} />
      <Route
        path='/committees/:committeeId/subcommittees/:subcommitteeId'
        element={<SubcommitteeDetail />}
      />
      <Route path='/lobbying' element={<Lobbying />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <div className='min-h-screen bg-gray-50'>
        {/* Header */}
        <header className='bg-white shadow-sm border-b'>
          <div className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8'>
            <div className='flex items-center justify-between h-16'>
              <div className='flex items-center'>
                <Link
                  to='/'
                  className='text-2xl font-bold text-gray-900 hover:text-blue-600'
                >
                  Congressional Transparency Portal
                </Link>
              </div>
              <div className='text-sm text-gray-600'>
                118th Congress Data Analysis
              </div>
            </div>
          </div>
        </header>

        <Navigation />

        {/* Main Content */}
        <main className='max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8'>
          <AppContent />
        </main>
      </div>
    </Router>
  );
}

export default App;
