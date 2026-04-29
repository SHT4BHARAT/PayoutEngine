from django.db.models import Sum
from .models import Merchant

class MerchantService:
    @staticmethod
    def get_balances(merchant: Merchant):
        credits = merchant.ledgerentry_set.filter(entry_type='credit').aggregate(s=Sum('amount_paise'))['s'] or 0
        debits = merchant.ledgerentry_set.filter(entry_type='debit').aggregate(s=Sum('amount_paise'))['s'] or 0
        
        available_balance = credits - debits
        held_balance = merchant.payout_set.filter(status__in=['pending', 'processing']).aggregate(s=Sum('amount_paise'))['s'] or 0
        
        return {
            "available_balance": available_balance,
            "held_balance": held_balance
        }
