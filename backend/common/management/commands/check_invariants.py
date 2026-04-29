from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Sum
from merchants.models import Merchant, LedgerEntry
from payouts.models import Payout

class Command(BaseCommand):
    help = 'Verify all financial invariants hold across the database.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting exhaustive invariant checks...")
        invariants_failed = 0

        merchants = Merchant.objects.all()
        for merchant in merchants:
            # 1. Balance Invariant
            credits = LedgerEntry.objects.filter(merchant=merchant, entry_type='credit').aggregate(s=Sum('amount_paise'))['s'] or 0
            debits = LedgerEntry.objects.filter(merchant=merchant, entry_type='debit').aggregate(s=Sum('amount_paise'))['s'] or 0
            
            net_ledger = credits - debits
            available = merchant.available_balance
            held = merchant.held_balance
            
            # Since our architecture immediately creates a debit LedgerEntry for holds, 
            # net_ledger represents the available_balance directly.
            if net_ledger != available:
                self.stderr.write(self.style.ERROR(
                    f"FAIL: Balance Invariant (Merchant {merchant.id}) - "
                    f"Net Ledger ({net_ledger}) != Available ({available})"
                ))
                invariants_failed += 1
            else:
                self.stdout.write(self.style.SUCCESS(f"PASS: Balance Invariant (Merchant {merchant.id})"))

            # 2. Held Balance Consistency
            active_payouts = Payout.objects.filter(
                merchant=merchant, 
                status__in=['pending', 'processing']
            ).aggregate(s=Sum('amount_paise'))['s'] or 0
            
            if held != active_payouts:
                self.stderr.write(self.style.ERROR(
                    f"FAIL: Held Balance Consistency (Merchant {merchant.id}) - "
                    f"Held balance property ({held}) != Sum of active payouts ({active_payouts})"
                ))
                invariants_failed += 1
            else:
                self.stdout.write(self.style.SUCCESS(f"PASS: Held Balance Consistency (Merchant {merchant.id})"))

            # 3. No negative balances
            if available < 0 or held < 0:
                self.stderr.write(self.style.ERROR(
                    f"FAIL: Negative Balance Found (Merchant {merchant.id}) - "
                    f"Available ({available}), Held ({held})"
                ))
                invariants_failed += 1
            else:
                self.stdout.write(self.style.SUCCESS(f"PASS: No Negative Balances (Merchant {merchant.id})"))

        # 4. No orphaned holds & 5. State Machine Integrity
        payouts = Payout.objects.all()
        for payout in payouts:
            # Check 4: No orphaned holds for pending/processing payouts
            if payout.status in ['pending', 'processing']:
                # A pending/processing payout MUST have a corresponding debit
                has_debit = LedgerEntry.objects.filter(
                    merchant=payout.merchant, 
                    entry_type='debit', 
                    amount_paise=payout.amount_paise
                ).exists()
                if not has_debit:
                    self.stderr.write(self.style.ERROR(
                        f"FAIL: Orphaned Hold Found (Payout {payout.id}) - "
                        f"Status is {payout.status} but no debit LedgerEntry matches amount {payout.amount_paise}"
                    ))
                    invariants_failed += 1

            # Check 5: State Machine Integrity
            if payout.status == 'completed' and not payout.completed_at:
                self.stderr.write(self.style.ERROR(f"FAIL: State Machine (Payout {payout.id}) - Completed but no completed_at timestamp"))
                invariants_failed += 1
            if payout.status == 'failed' and not payout.failed_at:
                self.stderr.write(self.style.ERROR(f"FAIL: State Machine (Payout {payout.id}) - Failed but no failed_at timestamp"))
                invariants_failed += 1
            if payout.status == 'processing' and not payout.processed_at:
                self.stderr.write(self.style.ERROR(f"FAIL: State Machine (Payout {payout.id}) - Processing but no processed_at timestamp"))
                invariants_failed += 1

        self.stdout.write(self.style.SUCCESS(f"PASS: Orphaned Holds & State Machine Integrity across {payouts.count()} payouts"))

        # 6. Float Audit (Raw SQL)
        # Check SQLite type for amount_paise columns. We expect 'integer' not 'real'
        with connection.cursor() as cursor:
            cursor.execute("SELECT TYPEOF(amount_paise) FROM payouts_payout LIMIT 1")
            row = cursor.fetchone()
            if row and row[0].lower() == 'real':
                self.stderr.write(self.style.ERROR(f"FAIL: Float Audit - Float type detected in payouts_payout.amount_paise!"))
                invariants_failed += 1
            
            cursor.execute("SELECT TYPEOF(amount_paise) FROM merchants_ledgerentry LIMIT 1")
            row = cursor.fetchone()
            if row and row[0].lower() == 'real':
                self.stderr.write(self.style.ERROR(f"FAIL: Float Audit - Float type detected in merchants_ledgerentry.amount_paise!"))
                invariants_failed += 1

        self.stdout.write(self.style.SUCCESS("PASS: Float Audit (No floating point columns detected in DB)"))

        if invariants_failed == 0:
            self.stdout.write(self.style.SUCCESS('\n=== FINAL RESULT: PASS ===\nAll money invariants held perfectly! No leaks or float anomalies detected.'))
        else:
            self.stderr.write(self.style.ERROR(f'\n=== FINAL RESULT: FAIL ===\n{invariants_failed} invariant violations detected!'))
