import {
  ArrowLeft,
  FileText,
  Calendar,
  Users,
  Building2,
  TrendingUp,
  Clock,
  Tag,
  AlertCircle,
  CheckCircle,
  XCircle,
  ExternalLink,
  User,
} from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';

import DataService from '../services/dataService';

import BillProgressBar from './BillProgressBar';

function BillDetail() {
  const { billId } = useParams();
  const navigate = useNavigate();
  const [bill, setBill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadBillData();
  }, [billId, loadBillData]);

  const loadBillData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to load detailed bill data directly from the API
      try {
        const detailedBill = await DataService.loadBillDetails(billId);
        if (detailedBill) {
          setBill(detailedBill);
          setLoading(false);
          return;
        }
      } catch {
        console.warn(
          'Could not load bill details directly, trying bills index...'
        );
      }

      // Fall back to bills index for basic info
      const billsIndex = await DataService.loadBillsIndex();
      const basicBill = billsIndex?.bills?.find(
        b =>
          b.id === billId ||
          b.bill_id === billId ||
          `${b.type}${b.bill_id}` === billId ||
          `${b.type}-${b.bill_id}` === billId ||
          b.id === `${billId}.json` ||
          b.id === billId.replace('.json', '')
      );

      if (!basicBill) {
        setError('Bill not found');
        setLoading(false);
        return;
      }

      setBill(basicBill);
      setLoading(false);
    } catch (err) {
      console.error('Error loading bill:', err);
      setError('Failed to load bill data');
      setLoading(false);
    }
  }, [billId]);

  const getStatusColor = status => {
    if (!status) return 'bg-gray-100 text-gray-700';
    const text = status.toLowerCase();
    if (text.includes('became law') || text.includes('public law')) {
      return 'bg-green-100 text-green-700';
    } else if (text.includes('passed')) {
      return 'bg-blue-100 text-blue-700';
    } else if (text.includes('failed') || text.includes('rejected')) {
      return 'bg-red-100 text-red-700';
    } else if (text.includes('introduced')) {
      return 'bg-yellow-100 text-yellow-700';
    }
    return 'bg-gray-100 text-gray-700';
  };

  const getStatusIcon = status => {
    if (!status) return <AlertCircle size={16} />;
    const text = status.toLowerCase();
    if (text.includes('became law') || text.includes('public law')) {
      return <CheckCircle size={16} />;
    } else if (text.includes('failed') || text.includes('rejected')) {
      return <XCircle size={16} />;
    }
    return <Clock size={16} />;
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600' />
      </div>
    );
  }

  if (error || !bill) {
    return (
      <div className='bg-red-50 border border-red-200 rounded-lg p-6'>
        <h3 className='text-lg font-semibold text-red-800 mb-2'>
          Error Loading Bill
        </h3>
        <p className='text-red-700'>{error || 'Bill not found'}</p>
        <button
          onClick={() => navigate('/bills')}
          className='mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700'
        >
          Back to Bills List
        </button>
      </div>
    );
  }

  const billNumber = bill.type ? `${bill.type} ${bill.bill_id}` : bill.bill_id;
  const statusText = bill.latestAction?.text || 'Status unknown';
  const statusColor = getStatusColor(statusText);

  return (
    <div className='space-y-6'>
      {/* Breadcrumb */}
      <div className='flex items-center gap-2 text-sm text-gray-600'>
        <Link to='/bills' className='hover:text-blue-600'>
          Bills
        </Link>
        <span>/</span>
        <span className='text-gray-900'>{billNumber}</span>
      </div>

      {/* Header */}
      <div className='bg-white rounded-lg shadow-sm border border-gray-200'>
        <div className='p-6'>
          <button
            onClick={() => navigate('/bills')}
            className='flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-4'
          >
            <ArrowLeft size={20} />
            <span>Back to Bills</span>
          </button>

          <div className='flex items-start justify-between'>
            <div className='flex-1'>
              <div className='flex items-center gap-3 mb-2'>
                <h1 className='text-3xl font-bold text-gray-900'>
                  {billNumber}
                </h1>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${statusColor} flex items-center gap-1`}
                >
                  {getStatusIcon(statusText)}
                  {statusText.length > 50
                    ? `${statusText.substring(0, 50)}...`
                    : statusText}
                </span>
              </div>
              <h2 className='text-xl text-gray-700 mb-4'>
                {bill.title || 'No title available'}
              </h2>

              <div className='grid grid-cols-2 md:grid-cols-4 gap-4 mt-6'>
                <div className='flex items-center gap-2'>
                  <Building2 size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>Origin Chamber</p>
                    <p className='text-sm font-medium'>
                      {bill.originChamber || 'Unknown'}
                    </p>
                  </div>
                </div>
                <div className='flex items-center gap-2'>
                  <Calendar size={16} className='text-gray-400' />
                  <div>
                    <p className='text-xs text-gray-500'>Last Updated</p>
                    <p className='text-sm font-medium'>
                      {bill.updateDate
                        ? DataService.formatDate(bill.updateDate)
                        : 'Unknown'}
                    </p>
                  </div>
                </div>
                {bill.latestAction?.actionDate && (
                  <div className='flex items-center gap-2'>
                    <Clock size={16} className='text-gray-400' />
                    <div>
                      <p className='text-xs text-gray-500'>Last Action Date</p>
                      <p className='text-sm font-medium'>
                        {DataService.formatDate(bill.latestAction.actionDate)}
                      </p>
                    </div>
                  </div>
                )}
                {bill.policyArea && (
                  <div className='flex items-center gap-2'>
                    <Tag size={16} className='text-gray-400' />
                    <div>
                      <p className='text-xs text-gray-500'>Policy Area</p>
                      <p className='text-sm font-medium'>
                        {bill.policyArea.name}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Latest Action */}
        {bill.latestAction && (
          <div className='border-t border-gray-200 px-6 py-4'>
            <h3 className='text-lg font-semibold text-gray-900 mb-3'>
              Latest Action
            </h3>
            <div className='bg-gray-50 rounded-lg p-4'>
              <div className='flex items-start justify-between'>
                <div>
                  <p className='text-sm text-gray-700'>
                    {bill.latestAction.text}
                  </p>
                  <p className='text-xs text-gray-500 mt-1'>
                    {DataService.formatDate(bill.latestAction.actionDate)}
                  </p>
                </div>
                {bill.latestAction.actionCode && (
                  <span className='text-xs font-mono bg-gray-200 px-2 py-1 rounded'>
                    {bill.latestAction.actionCode}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bill Progress Bar */}
      <BillProgressBar bill={bill} />

      {/* Bill Details Grid */}
      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
        {/* Summary */}
        {bill.summary && (
          <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4'>
              Summary
            </h3>
            <div className='prose prose-sm max-w-none'>
              <p className='text-sm text-gray-700 whitespace-pre-wrap'>
                {bill.summary.text || bill.summary}
              </p>
            </div>
          </div>
        )}

        {/* Sponsors */}
        {(bill.sponsors || bill.cosponsors) && (
          <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
              <Users size={20} />
              Sponsors & Cosponsors
            </h3>

            {bill.sponsors && (
              <div className='mb-4'>
                <h4 className='text-sm font-medium text-gray-700 mb-2'>
                  Primary Sponsor
                </h4>
                {Array.isArray(bill.sponsors) ? (
                  bill.sponsors.map((sponsor, index) => (
                    <Link
                      key={sponsor.bioguideId || index}
                      to={`/members/${sponsor.bioguideId}`}
                      className='flex items-center gap-2 p-2 hover:bg-gray-50 rounded'
                    >
                      <User size={16} className='text-gray-400' />
                      <div>
                        <p className='text-sm font-medium text-blue-600 hover:underline'>
                          {sponsor.fullName || sponsor.name}
                        </p>
                        <p className='text-xs text-gray-500'>
                          {sponsor.party} - {sponsor.state}
                        </p>
                      </div>
                    </Link>
                  ))
                ) : (
                  <p className='text-sm text-gray-600'>{bill.sponsors}</p>
                )}
              </div>
            )}

            {bill.cosponsors && (
              <div>
                <h4 className='text-sm font-medium text-gray-700 mb-2'>
                  Cosponsors (
                  {Array.isArray(bill.cosponsors) ? bill.cosponsors.length : 0})
                </h4>
                {Array.isArray(bill.cosponsors) &&
                bill.cosponsors.length > 0 ? (
                  <div className='max-h-40 overflow-y-auto'>
                    {bill.cosponsors.slice(0, 10).map((cosponsor, index) => (
                      <Link
                        key={cosponsor.bioguideId || index}
                        to={`/members/${cosponsor.bioguideId}`}
                        className='flex items-center gap-2 p-1 hover:bg-gray-50 rounded text-sm'
                      >
                        <User size={14} className='text-gray-400' />
                        <span className='text-blue-600 hover:underline'>
                          {cosponsor.fullName || cosponsor.name}
                        </span>
                        <span className='text-gray-500'>
                          ({cosponsor.party})
                        </span>
                      </Link>
                    ))}
                    {bill.cosponsors.length > 10 && (
                      <p className='text-xs text-gray-500 mt-2 pl-5'>
                        And {bill.cosponsors.length - 10} more...
                      </p>
                    )}
                  </div>
                ) : (
                  <p className='text-sm text-gray-500'>No cosponsors</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Subjects */}
        {bill.subjects && bill.subjects.length > 0 && (
          <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
              <Tag size={20} />
              Subjects
            </h3>
            <div className='flex flex-wrap gap-2'>
              {bill.subjects.map((subject, index) => (
                <span
                  key={subject.name || subject || index}
                  className='px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm'
                >
                  {subject.name || subject}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Committees */}
        {bill.committees && bill.committees.length > 0 && (
          <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
            <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
              <Building2 size={20} />
              Committees
            </h3>
            <div className='space-y-2'>
              {bill.committees.map((committee, index) => (
                <div
                  key={committee.name || committee.code || index}
                  className='p-2 bg-gray-50 rounded'
                >
                  <p className='text-sm font-medium text-gray-900'>
                    {committee.name}
                  </p>
                  {committee.chamber && (
                    <p className='text-xs text-gray-500'>{committee.chamber}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Actions Timeline */}
      {bill.actions && bill.actions.length > 0 && (
        <div className='bg-white rounded-lg shadow-sm border border-gray-200 p-6'>
          <h3 className='text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2'>
            <TrendingUp size={20} />
            Legislative Timeline
          </h3>
          <div className='space-y-3'>
            {bill.actions.slice(0, 10).map((action, index) => (
              <div
                key={action.actionDate + action.text.slice(0, 20) || index}
                className='flex gap-4 pb-3 border-b border-gray-100 last:border-0'
              >
                <div className='flex-shrink-0'>
                  <div className='w-2 h-2 bg-blue-600 rounded-full mt-2' />
                </div>
                <div className='flex-1'>
                  <p className='text-sm text-gray-700'>{action.text}</p>
                  <p className='text-xs text-gray-500 mt-1'>
                    {DataService.formatDate(action.actionDate)} •{' '}
                    {action.sourceSystem?.name || 'Unknown'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Additional Actions */}
      <div className='flex gap-3'>
        <button
          onClick={() => {
            const congressNum = bill.congress || '118';
            const billType = bill.type?.toLowerCase() || 's';
            const billNum = bill.bill_id;
            window.open(
              `https://www.congress.gov/bill/${congressNum}th-congress/${billType === 's' ? 'senate' : 'house'}-bill/${billNum}`,
              '_blank'
            );
          }}
          className='px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-2'
        >
          <ExternalLink size={16} />
          View on Congress.gov
        </button>
        <Link
          to='/bills'
          className='px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 flex items-center gap-2'
        >
          <FileText size={16} />
          Back to All Bills
        </Link>
      </div>
    </div>
  );
}

export default BillDetail;
