import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { ShieldCheck, CreditCard, AlertCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export default function PublicPayPage() {
  const { slug } = useParams();
  const [link, setLink] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    const fetchLink = async () => {
      try {
        const response = await axios.get(`${API_BASE}/payments/pay/${slug}/`);
        setLink(response.data);
      } catch (err) {
        if (err.response && err.response.status === 404) {
          setError('Payment link not found');
        } else {
          setError('Failed to load payment details');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchLink();
  }, [slug]);

  const handlePay = async () => {
    setCheckoutLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/payments/pay/${slug}/checkout/`);
      window.location.href = response.data.stripe_url;
    } catch (err) {
      setError('Failed to initiate checkout. Please try again.');
    } finally {
      setCheckoutLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="bg-card border border-border p-8 rounded-2xl max-w-sm w-full text-center">
          <AlertCircle className="mx-auto text-destructive mb-4" size={48} />
          <h1 className="text-xl font-bold mb-2">Something went wrong</h1>
          <p className="text-muted-foreground mb-6">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="w-full bg-primary text-primary-foreground py-3 rounded-xl font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (link?.is_paid) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="bg-card border border-border p-8 rounded-2xl max-w-sm w-full text-center">
          <div className="w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
            <ShieldCheck size={32} />
          </div>
          <h1 className="text-2xl font-bold mb-2">Already Paid</h1>
          <p className="text-muted-foreground">This payment link has already been settled successfully.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-card border border-border rounded-3xl overflow-hidden shadow-2xl">
          <div className="bg-primary/5 p-8 border-b border-border">
            <div className="flex items-center gap-2 text-primary font-medium mb-4">
              <ShieldCheck size={18} />
              <span className="text-sm tracking-wide uppercase">Secure Payment</span>
            </div>
            <h1 className="text-2xl font-bold mb-1">{link.title}</h1>
            <p className="text-muted-foreground text-sm">{link.merchant_name}</p>
          </div>
          
          <div className="p-8">
            {link.description && (
              <p className="text-muted-foreground mb-8 line-clamp-3 italic">"{link.description}"</p>
            )}
            
            <div className="flex justify-between items-end mb-8">
              <span className="text-muted-foreground">Total to pay</span>
              <span className="text-4xl font-black tracking-tighter">
                ${(link.total_amount_usd_cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
            </div>

            <button 
              onClick={handlePay}
              disabled={checkoutLoading}
              className="w-full bg-foreground text-background py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 hover:opacity-90 transition-all disabled:opacity-50 active:scale-95"
            >
              {checkoutLoading ? (
                <div className="w-5 h-5 rounded-full border-2 border-background border-t-transparent animate-spin"></div>
              ) : (
                <>
                  <CreditCard size={20} />
                  Pay Now
                </>
              )}
            </button>
            
            <div className="mt-8 pt-8 border-t border-border/50 flex flex-col gap-4 text-center">
              <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <ShieldCheck size={14} className="text-green-500" />
                No account required · SSL Encrypted
              </div>
              <p className="text-[10px] text-muted-foreground/60 uppercase tracking-widest font-bold">
                Powered by Payout Engine
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
