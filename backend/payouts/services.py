from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from merchants.models import Merchant, LedgerEntry, BankAccount
from payouts.models import Payout
from common.errors import InsufficientBalance
from workers.tasks import process_payout

class PayoutService:
    @staticmethod
    def create_payout(merchant_id, bank_account_id, amount_paise, idempotency_key):
        if amount_paise <= 0:
            raise ValueError("Amount must be greater than zero")

        with transaction.atomic():
            # 1. Lock merchant row for update
            merchant = Merchant.objects.select_for_update().get(id=merchant_id)

            # 2. Check idempotency
            payout = Payout.objects.filter(
                merchant=merchant,
                idempotency_key=idempotency_key,
                idempotency_expires_at__gt=timezone.now()
            ).first()

            if payout:
                # Same request again - return it
                return payout, False

            # 3. Check balance
            credits = LedgerEntry.objects.filter(
                merchant=merchant, entry_type='credit'
            ).aggregate(s=Sum('amount_paise'))['s'] or 0
            
            debits = LedgerEntry.objects.filter(
                merchant=merchant, entry_type='debit'
            ).aggregate(s=Sum('amount_paise'))['s'] or 0
            
            # Note: debits includes the hold created on payout creation.
            # We never create a second debit entry on payout completion.
            # This correctly computes available balance minus any held or settled funds.
            available_balance = credits - debits

            if available_balance < amount_paise:
                raise InsufficientBalance("Insufficient available balance")

            # 4. Create payout
            bank_account = BankAccount.objects.get(id=bank_account_id, merchant=merchant)
            payout = Payout.objects.create(
                merchant=merchant,
                bank_account=bank_account,
                amount_paise=amount_paise,
                status='pending',
                idempotency_key=idempotency_key,
                idempotency_expires_at=timezone.now() + timedelta(hours=24),
                held_at=timezone.now()
            )

            # 5. Create hold ledger entry
            LedgerEntry.objects.create(
                merchant=merchant,
                entry_type='debit',
                amount_paise=amount_paise,
                reference_id=f"payout_{payout.id}",
                description=f"Hold for payout {payout.id}"
            )

            # 6. Trigger processing after commit
            transaction.on_commit(lambda: process_payout.delay(payout.id))

            return payout, True
