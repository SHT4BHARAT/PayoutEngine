import requests
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings

class ForexUnavailableError(Exception):
    pass

def get_usd_to_inr_rate() -> Decimal:
    """
    Fetches the current USD to INR exchange rate with caching and fallback logic.
    """
    cache_key = 'usd_inr_rate'
    fallback_key = 'usd_inr_rate_last_known'
    
    # 1. Check primary cache
    cached_rate = cache.get(cache_key)
    if cached_rate:
        return Decimal(str(cached_rate))
    
    # 2. Attempt API fetch
    try:
        # Using a public API - ideally this should be a managed secret/config
        url = 'https://api.exchangerate-api.com/v4/latest/USD'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        rate = response.json()['rates']['INR']
        rate_decimal = Decimal(str(rate))
        
        # Update caches
        cache.set(cache_key, str(rate_decimal), timeout=3600)  # 1 hour
        cache.set(fallback_key, str(rate_decimal), timeout=None) # Forever fallback
        
        return rate_decimal
        
    except Exception as e:
        # 3. Fallback to last known rate
        last_known = cache.get(fallback_key)
        if last_known:
            return Decimal(str(last_known))
            
        # 4. Emergency fallback from settings/env if everything fails
        emergency_rate = getattr(settings, 'FOREX_FALLBACK_RATE', None)
        if emergency_rate:
            return Decimal(str(emergency_rate))
            
        raise ForexUnavailableError(f"Forex service unavailable and no fallback found: {str(e)}")
