import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { CheckCircle2, Clock, AlertCircle, RefreshCw } from 'lucide-react';

const formatINR = (paise) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(paise / 100);
};

const StatusBadge = ({ status }) => {
  switch (status) {
    case 'completed':
      return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-500 border border-green-500/20"><CheckCircle2 size={12}/> Completed</span>;
    case 'pending':
      return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-500 border border-yellow-500/20"><Clock size={12}/> Pending</span>;
    case 'processing':
      return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-500 border border-blue-500/20"><RefreshCw size={12} className="animate-spin"/> Processing</span>;
    case 'failed':
      return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-500 border border-red-500/20"><AlertCircle size={12}/> Failed</span>;
    default:
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground">{status}</span>;
  }
};

export const PayoutHistoryTable = ({ payouts }) => {
  if (!payouts || payouts.length === 0) {
    return <div className="text-sm text-muted-foreground p-4 border border-dashed rounded-lg text-center">No payouts found.</div>;
  }

  return (
    <div className="overflow-x-auto border border-border rounded-xl">
      <table className="w-full text-sm text-left">
        <thead className="bg-secondary/50 text-muted-foreground uppercase">
          <tr>
            <th className="px-6 py-3 font-medium">Status</th>
            <th className="px-6 py-3 font-medium">Amount</th>
            <th className="px-6 py-3 font-medium">Requested</th>
            <th className="px-6 py-3 font-medium">Idempotency Key</th>
            <th className="px-6 py-3 font-medium">Note</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-card">
          {payouts.map((payout) => (
            <tr key={payout.id} className="hover:bg-muted/30 transition-colors">
              <td className="px-6 py-4"><StatusBadge status={payout.status} /></td>
              <td className="px-6 py-4 font-medium">{formatINR(payout.amount_paise)}</td>
              <td className="px-6 py-4 text-muted-foreground">
                {formatDistanceToNow(new Date(payout.created_at), { addSuffix: true })}
              </td>
              <td className="px-6 py-4 font-mono text-xs text-muted-foreground">{payout.idempotency_key}</td>
              <td className="px-6 py-4 text-xs text-muted-foreground">{payout.failure_reason || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
