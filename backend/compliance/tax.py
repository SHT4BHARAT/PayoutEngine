from decimal import Decimal

# Basic Tax Rates mapping for MVP
TAX_RATES = {
    'IN': Decimal('0.18'),   # India GST 18%
    'GB': Decimal('0.20'),   # UK VAT 20%
    'DE': Decimal('0.19'),   # Germany VAT 19%
    'AU': Decimal('0.10'),   # Australia GST 10%
    'US': Decimal('0.00'),   # US (Simplified for MVP)
}

def calculate_tax(amount_usd_cents: int, country_code: str) -> dict:
    """
    Calculate tax amount based on country code.
    Uses Merchant's country for MVP as per plan.
    """
    rate = TAX_RATES.get(country_code.upper(), Decimal('0.00'))
    tax_amount = int(Decimal(amount_usd_cents) * rate)
    total_amount = amount_usd_cents + tax_amount
    
    return {
        'base_amount_usd_cents': amount_usd_cents,
        'tax_rate': str(rate),
        'tax_amount_usd_cents': tax_amount,
        'total_amount_usd_cents': total_amount,
        'country': country_code.upper()
    }
