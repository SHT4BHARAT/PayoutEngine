import { useState, useEffect, useCallback } from 'react';
import { getMerchantProfile, getLedger, getPayouts } from '../api/client';

export const usePolling = (intervalMs = 5000) => {
  const [data, setData] = useState({
    profile: null,
    ledger: [],
    payouts: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [profileData, ledgerData, payoutsData] = await Promise.all([
        getMerchantProfile(),
        getLedger(),
        getPayouts()
      ]);

      setData({
        profile: profileData,
        ledger: ledgerData.results || [],
        payouts: payoutsData.results || []
      });
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch dashboard data. Please check your token or server connection.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(); // Initial fetch
    
    const intervalId = setInterval(fetchData, intervalMs);
    return () => clearInterval(intervalId);
  }, [fetchData, intervalMs]);

  return { ...data, loading, error, refetch: fetchData };
};
