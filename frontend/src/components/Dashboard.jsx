import { Users, FileText, TrendingUp, Activity } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

import DataService from '../services/dataService';

function Dashboard({ data }) {
  const { membersSummary, billsIndex } = data;

  const getPartyStats = () => {
    if (!membersSummary || !membersSummary.members) return null;

    const members = membersSummary.members;
    const total = members.length;

    // Calculate party breakdown from members array
    const partyBreakdown = members.reduce((acc, member) => {
      const party = member.party || 'Unknown';
      // Normalize party names (Democrat -> Democratic)
      const normalizedParty = party === 'Democrat' ? 'Democratic' : party;
      acc[normalizedParty] = (acc[normalizedParty] || 0) + 1;
      return acc;
    }, {});

    return {
      total,
      republicans: partyBreakdown.Republican || 0,
      democrats: partyBreakdown.Democratic || 0,
      independents: partyBreakdown.Independent || 0,
      senate: {},
      house: {},
    };
  };

  const getBillStats = () => {
    if (!billsIndex) return { total: 0, recent: [] };

    // The API returns records array, not bills
    const bills = billsIndex.records || billsIndex.bills || [];
    const billsArray = Array.isArray(bills) ? bills : Object.values(bills);

    // Sort by date and get recent bills - use latest_action or last_updated field from actual data
    const recent = billsArray
      .filter(bill => bill && bill.title)
      .sort((a, b) => {
        const dateA = new Date(a.last_updated || a.updateDate || 0);
        const dateB = new Date(b.last_updated || b.updateDate || 0);
        return dateB - dateA;
      })
      .slice(0, 5);

    return {
      total: billsIndex.total || billsIndex.count || billsArray.length,
      recent,
    };
  };

  const partyStats = getPartyStats();
  const billStats = getBillStats();

  const StatCard = ({ icon: Icon, title, value, subtitle, color }) => (
    <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
      <div className='flex items-center justify-between'>
        <div>
          <p className='text-sm font-medium text-gray-600'>{title}</p>
          <p className={`text-2xl font-bold mt-1 ${color || 'text-gray-900'}`}>
            {value}
          </p>
          {subtitle && <p className='text-xs text-gray-500 mt-1'>{subtitle}</p>}
        </div>
        <div
          className={`p-3 rounded-lg ${color ? color.replace('text-', 'bg-').replace('900', '100') : 'bg-gray-100'}`}
        >
          <Icon className={`h-6 w-6 ${color || 'text-gray-600'}`} />
        </div>
      </div>
    </div>
  );

  return (
    <div className='space-y-6'>
      <div>
        <h2 className='text-2xl font-bold text-gray-900 mb-4'>
          Congressional Overview
        </h2>
        <p className='text-gray-600'>
          Real-time analysis of the 118th United States Congress
        </p>
      </div>

      {/* Stats Grid */}
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4'>
        <StatCard
          icon={Users}
          title='Total Members'
          value={partyStats?.total || 0}
          subtitle='Active members'
          color='text-blue-600'
        />
        <StatCard
          icon={TrendingUp}
          title='Republicans'
          value={partyStats?.republicans || 0}
          subtitle={`${((partyStats?.republicans / partyStats?.total) * 100).toFixed(1)}% of total`}
          color='text-republican'
        />
        <StatCard
          icon={Activity}
          title='Democrats'
          value={partyStats?.democrats || 0}
          subtitle={`${((partyStats?.democrats / partyStats?.total) * 100).toFixed(1)}% of total`}
          color='text-democrat'
        />
        <StatCard
          icon={FileText}
          title='Bills Tracked'
          value={billStats.total}
          subtitle='Legislative items'
          color='text-purple-600'
        />
      </div>

      {/* Party Distribution */}
      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4'>
            Party Distribution
          </h3>
          {partyStats && (
            <div className='space-y-4'>
              <div>
                <div className='flex justify-between items-center mb-1'>
                  <span className='text-sm font-medium text-gray-700'>
                    Democrats
                  </span>
                  <span className='text-sm text-gray-600'>
                    {partyStats.democrats}
                  </span>
                </div>
                <div className='w-full bg-gray-200 rounded-full h-2'>
                  <div
                    className='bg-democrat h-2 rounded-full'
                    style={{
                      width: `${(partyStats.democrats / partyStats.total) * 100}%`,
                    }}
                  />
                </div>
              </div>

              <div>
                <div className='flex justify-between items-center mb-1'>
                  <span className='text-sm font-medium text-gray-700'>
                    Republicans
                  </span>
                  <span className='text-sm text-gray-600'>
                    {partyStats.republicans}
                  </span>
                </div>
                <div className='w-full bg-gray-200 rounded-full h-2'>
                  <div
                    className='bg-republican h-2 rounded-full'
                    style={{
                      width: `${(partyStats.republicans / partyStats.total) * 100}%`,
                    }}
                  />
                </div>
              </div>

              <div>
                <div className='flex justify-between items-center mb-1'>
                  <span className='text-sm font-medium text-gray-700'>
                    Independents
                  </span>
                  <span className='text-sm text-gray-600'>
                    {partyStats.independents}
                  </span>
                </div>
                <div className='w-full bg-gray-200 rounded-full h-2'>
                  <div
                    className='bg-independent h-2 rounded-full'
                    style={{
                      width: `${(partyStats.independents / partyStats.total) * 100}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Recent Bills */}
        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4'>
            Recent Bills
          </h3>
          <div className='space-y-3'>
            {billStats.recent.length > 0 ? (
              billStats.recent.map((bill, index) => (
                <Link
                  key={bill.id || index}
                  to={`/bills/${bill.id || `${bill.type}${bill.number}`}`}
                  className='block border-l-2 border-blue-500 pl-3 py-1 hover:bg-gray-50 rounded'
                >
                  <p className='text-sm font-medium text-gray-900'>
                    {bill.type && bill.number
                      ? `${bill.type} ${bill.number}`
                      : bill.id || 'Unknown'}
                  </p>
                  <p className='text-xs text-gray-600 line-clamp-2'>
                    {bill.title || 'No title available'}
                  </p>
                  <p className='text-xs text-gray-500 mt-1'>
                    {bill.latest_action ||
                      DataService.formatDate(
                        bill.last_updated || bill.updateDate
                      )}
                  </p>
                </Link>
              ))
            ) : (
              <p className='text-sm text-gray-500'>No bill data available</p>
            )}
          </div>
        </div>
      </div>

      {/* State Distribution */}
      {membersSummary?.by_state && (
        <div className='bg-white p-6 rounded-lg shadow-sm border border-gray-200'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4'>
            State Representation
          </h3>
          <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3'>
            {Object.entries(membersSummary.by_state)
              .slice(0, 12)
              .map(([state, parties]) => (
                <div key={state} className='p-3 border border-gray-200 rounded'>
                  <p className='text-sm font-medium text-gray-900'>{state}</p>
                  <div className='flex gap-2 mt-1'>
                    {parties.Republican && (
                      <span className='text-xs text-republican font-medium'>
                        R: {parties.Republican}
                      </span>
                    )}
                    {parties.Democratic && (
                      <span className='text-xs text-democrat font-medium'>
                        D: {parties.Democratic}
                      </span>
                    )}
                    {parties.Independent && (
                      <span className='text-xs text-independent font-medium'>
                        I: {parties.Independent}
                      </span>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
