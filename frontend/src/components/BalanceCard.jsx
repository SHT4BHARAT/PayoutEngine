import React from 'react';
import { Wallet, Lock } from 'lucide-react';

const formatINR = (paise) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2
  }).format(paise / 100);
};

export const BalanceCard = ({ profile }) => {
  if (!profile) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
      <div className="bg-card text-card-foreground border border-border rounded-xl p-6 shadow-sm flex items-center justify-between transition-transform hover:scale-[1.02]">
        <div>
          <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Wallet size={16} /> Available Balance
          </p>
          <h2 className="text-3xl font-bold mt-2 tracking-tight">{formatINR(profile.available_balance)}</h2>
        </div>
      </div>
      
      <div className="bg-card text-card-foreground border border-border rounded-xl p-6 shadow-sm flex items-center justify-between transition-transform hover:scale-[1.02]">
        <div>
          <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Lock size={16} /> Held Balance (Pending Payouts)
          </p>
          <h2 className="text-3xl font-bold mt-2 tracking-tight">{formatINR(profile.held_balance)}</h2>
        </div>
      </div>
    </div>
  );
};
