import React, { useState } from 'react';
import { usePolling } from './hooks/usePolling';
import { BalanceCard } from './components/BalanceCard';
import { PayoutForm } from './components/PayoutForm';
import { LedgerTable } from './components/LedgerTable';
import { PayoutHistoryTable } from './components/PayoutHistoryTable';
import { Activity, Receipt, ArrowRightLeft } from 'lucide-react';

function App() {
  const { profile, ledger, payouts, loading, error, refetch } = usePolling(5000);
  const [activeTab, setActiveTab] = useState('payouts'); // 'payouts' or 'ledger'

  if (loading && !profile) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="bg-destructive/10 border border-destructive/20 text-destructive p-6 rounded-xl max-w-md w-full">
          <h2 className="text-lg font-bold mb-2">Connection Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground pb-12">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-primary text-primary-foreground p-1.5 rounded-md">
              <Activity size={20} />
            </div>
            <h1 className="font-bold text-lg tracking-tight">Playto Payout Engine</h1>
          </div>
          {profile && (
            <div className="text-sm text-muted-foreground">
              Merchant: <span className="text-foreground font-medium">{profile.name}</span>
            </div>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 pt-8">
        <BalanceCard profile={profile} />
        
        <PayoutForm onSuccess={refetch} />

        {/* Tabs */}
        <div className="flex border-b border-border mb-6">
          <button 
            className={`px-4 py-3 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${activeTab === 'payouts' ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
            onClick={() => setActiveTab('payouts')}
          >
            <ArrowRightLeft size={16} /> Payouts History
          </button>
          <button 
            className={`px-4 py-3 text-sm font-medium border-b-2 flex items-center gap-2 transition-colors ${activeTab === 'ledger' ? 'border-primary text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
            onClick={() => setActiveTab('ledger')}
          >
            <Receipt size={16} /> Ledger Entries
          </button>
        </div>

        {/* Tab Content */}
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
          {activeTab === 'payouts' ? (
            <PayoutHistoryTable payouts={payouts} />
          ) : (
            <LedgerTable ledger={ledger} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
