import React, { useState } from 'react';
import axios from 'axios';
import { Link as LinkIcon, Plus, Copy, ExternalLink, Check } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const AUTH_TOKEN = import.meta.env.VITE_AUTH_TOKEN;

export default function PaymentLinkCreator() {
  const [showModal, setShowModal] = useState(false);
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatedLink, setGeneratedLink] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(
        `${API_BASE}/payments/merchant/payment-links/`,
        {
          title,
          amount_usd_cents: Math.round(parseFloat(amount) * 100),
          description
        },
        {
          headers: { Authorization: `Token ${AUTH_TOKEN}` }
        }
      );
      setGeneratedLink(response.data.public_url);
    } catch (err) {
      alert('Failed to create payment link');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generatedLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mb-8">
      <button 
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-lg font-medium hover:bg-primary/20 transition-colors"
      >
        <Plus size={18} /> Create Payment Link
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border w-full max-w-md rounded-2xl shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="p-6 border-b border-border flex justify-between items-center">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <LinkIcon size={20} className="text-primary" />
                New Payment Link
              </h2>
              <button onClick={() => { setShowModal(false); setGeneratedLink(null); }} className="text-muted-foreground hover:text-foreground">✕</button>
            </div>

            <div className="p-6">
              {!generatedLink ? (
                <form onSubmit={handleCreate} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Product Name</label>
                    <input 
                      required
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="e.g. Consulting Session"
                      className="w-full bg-background border border-border rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Amount (USD)</label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                      <input 
                        required
                        type="number"
                        step="0.01"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        placeholder="0.00"
                        className="w-full bg-background border border-border rounded-lg pl-8 pr-4 py-2 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Description (Optional)</label>
                    <textarea 
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full bg-background border border-border rounded-lg px-4 py-2 h-24 focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"
                    />
                  </div>
                  <button 
                    type="submit" 
                    disabled={loading}
                    className="w-full bg-primary text-primary-foreground py-3 rounded-xl font-bold hover:opacity-90 transition-opacity disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Generate Link'}
                  </button>
                </form>
              ) : (
                <div className="space-y-6 text-center animate-in fade-in slide-in-from-bottom-4">
                  <div className="w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mx-auto">
                    <Check size={32} />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">Link Generated!</h3>
                    <p className="text-sm text-muted-foreground">Share this with your customer to collect payment.</p>
                  </div>
                  <div className="bg-muted p-3 rounded-lg flex items-center gap-2">
                    <input 
                      readOnly 
                      value={generatedLink} 
                      className="bg-transparent border-none outline-none text-xs flex-1 truncate"
                    />
                    <button 
                      onClick={copyToClipboard}
                      className="p-2 hover:bg-background rounded-md text-primary transition-colors"
                    >
                      {copied ? <Check size={16} /> : <Copy size={16} />}
                    </button>
                  </div>
                  <a 
                    href={generatedLink} 
                    target="_blank" 
                    rel="noreferrer"
                    className="flex items-center justify-center gap-2 text-sm font-medium text-primary hover:underline"
                  >
                    Preview Page <ExternalLink size={14} />
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
