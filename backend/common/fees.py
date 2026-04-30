from decimal import Decimal

class FeeEngine:
    PLATFORM_FEE_RATE = Decimal('0.04')  # 4% flat fee
    
    @staticmethod
    def calculate_fees(amount_usd_cents: int) -> dict:
        """
        Calculate platform fee and merchant net amount in USD cents.
        """
        fee_cents = int(Decimal(amount_usd_cents) * FeeEngine.PLATFORM_FEE_RATE)
        merchant_net_cents = amount_usd_cents - fee_cents
        
        return {
            'gross_amount_usd_cents': amount_usd_cents,
            'platform_fee_usd_cents': fee_cents,
            'merchant_net_usd_cents': merchant_net_cents,
            'fee_rate': '4%'
        }
    
    @staticmethod
    def usd_to_inr_paise(usd_cents: int, forex_rate: Decimal) -> int:
        """
        Convert USD cents to INR paise using a fixed forex rate.
        """
        usd_amount = Decimal(usd_cents) / 100
        inr_amount = usd_amount * forex_rate
        return int(inr_amount * 100)
