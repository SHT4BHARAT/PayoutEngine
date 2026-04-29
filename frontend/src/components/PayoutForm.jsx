import React, { useState } from 'react';
import { createPayout } from '../api/client';
import { Send, AlertCircle } from 'lucide-react';

export const PayoutForm = ({ onSuccess }) => {
  const [amountINR, setAmountINR] = useState('');
  // Hardcoded bank account ID for demonstration (assumes seed_merchants creates account ID 1 or 2)
  const [bankAccountId, setBankAccountId] = useState('1'); 
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const amountPaise = Math.round(parseFloat(amountINR) * 100);
      if (isNaN(amountPaise) || amountPaise <= 0) {
        throw new Error('Please enter a valid amount');
      }

      // Generate idempotency key for this request
      const idempotencyKey = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      await createPayout(amountPaise, parseInt(bankAccountId), idempotencyKey);
      setAmountINR('');
      if (onSuccess) onSuccess();
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to create payout');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-sm mb-8">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Send size={18} /> Request Payout
      </h3>
      
      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg mb-4 flex items-start gap-2 text-sm">
          <AlertCircle size={16} className="mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 items-end">
        <div className="flex-1 w-full">
          <label className="block text-sm font-medium text-muted-foreground mb-1">Amount (INR)</label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">₹</span>
            <input 
              type="number" 
              step="0.01"
              min="1"
              required
              className="w-full bg-background border border-border rounded-lg pl-8 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
              placeholder="0.00"
              value={amountINR}
              onChange={(e) => setAmountINR(e.target.value)}
            />
          </div>
        </div>
        
        <div className="flex-1 w-full">
          <label className="block text-sm font-medium text-muted-foreground mb-1">Bank Account ID</label>
          <input 
            type="text" 
            required
            className="w-full bg-background border border-border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
            value={bankAccountId}
            onChange={(e) => setBankAccountId(e.target.value)}
          />
        </div>

        <button 
          type="submit" 
          disabled={loading}
          className="w-full sm:w-auto bg-primary text-primary-foreground font-medium px-6 py-2 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Withdraw Funds'}
        </button>
      </form>
    </div>
  );
};
