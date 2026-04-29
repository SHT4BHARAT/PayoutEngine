import React from 'react';
import { formatDistanceToNow } from 'date-fns';

const formatINR = (paise) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(paise / 100);
};

export const LedgerTable = ({ ledger }) => {
  if (!ledger || ledger.length === 0) {
    return <div className="text-sm text-muted-foreground p-4 border border-dashed rounded-lg text-center">No ledger entries found.</div>;
  }

  return (
    <div className="overflow-x-auto border border-border rounded-xl">
      <table className="w-full text-sm text-left">
        <thead className="bg-secondary/50 text-muted-foreground uppercase">
          <tr>
            <th className="px-6 py-3 font-medium">Description</th>
            <th className="px-6 py-3 font-medium">Reference</th>
            <th className="px-6 py-3 font-medium text-right">Amount</th>
            <th className="px-6 py-3 font-medium text-right">Time</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-card">
          {ledger.map((entry) => (
            <tr key={entry.id} className="hover:bg-muted/30 transition-colors">
              <td className="px-6 py-4">{entry.description}</td>
              <td className="px-6 py-4 font-mono text-xs text-muted-foreground">{entry.reference_id || '-'}</td>
              <td className={`px-6 py-4 text-right font-medium ${entry.entry_type === 'credit' ? 'text-green-500' : 'text-red-500'}`}>
                {entry.entry_type === 'credit' ? '+' : '-'}{formatINR(entry.amount_paise)}
              </td>
              <td className="px-6 py-4 text-right text-muted-foreground">
                {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
