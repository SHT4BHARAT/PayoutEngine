from unittest.mock import patch
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from merchants.models import Merchant, BankAccount, LedgerEntry
from payouts.models import Payout
from workers.tasks import process_payout, retry_stuck_payouts

class WorkerTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', email='test@test.com')
        self.merchant = Merchant.objects.create(user=self.user, name='Test Merchant', email='test@test.com')
        self.bank_account = BankAccount.objects.create(merchant=self.merchant, account_number='123', ifsc_code='ABC', account_holder_name='Test')
        
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type='credit',
            amount_paise=10000,
            description='Initial load'
        )

        self.payout = Payout.objects.create(
            merchant=self.merchant,
            bank_account=self.bank_account,
            amount_paise=5000,
            status='pending',
            idempotency_key='test-key',
            idempotency_expires_at=timezone.now() + timedelta(hours=24)
        )
        
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type='debit',
            amount_paise=5000,
            description='Hold'
        )

    @patch('workers.tasks.random.random')
    def test_process_success(self, mock_random):
        mock_random.return_value = 0.5 
        
        process_payout(self.payout.id)
        
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, 'completed')
        self.assertIsNotNone(self.payout.completed_at)
        
    @patch('workers.tasks.random.random')
    def test_process_failure_returns_funds(self, mock_random):
        mock_random.return_value = 0.2 
        
        process_payout(self.payout.id)
        
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, 'failed')
        
        refund = LedgerEntry.objects.filter(entry_type='credit', reference_id=f'refund_{self.payout.id}').first()
        self.assertIsNotNone(refund)
        self.assertEqual(refund.amount_paise, 5000)
        
        credits = sum(e.amount_paise for e in LedgerEntry.objects.filter(entry_type='credit'))
        debits = sum(e.amount_paise for e in LedgerEntry.objects.filter(entry_type='debit'))
        self.assertEqual(credits - debits, 10000)

    @patch('workers.tasks.process_payout.delay')
    def test_retry_stuck_payouts(self, mock_delay):
        self.payout.status = 'processing'
        self.payout.attempt_count = 1
        self.payout.save()
        
        Payout.objects.filter(id=self.payout.id).update(updated_at=timezone.now() - timedelta(seconds=35))
        
        res = retry_stuck_payouts()
        self.assertIn("Retried 1", res)
        
        mock_delay.assert_called_once_with(self.payout.id)
        
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.attempt_count, 2)

    def test_max_retries_failure(self):
        self.payout.status = 'processing'
        self.payout.attempt_count = 3
        self.payout.save()
        
        Payout.objects.filter(id=self.payout.id).update(updated_at=timezone.now() - timedelta(seconds=125))
        
        res = retry_stuck_payouts()
        self.assertIn("Failed permanently 1", res)
        
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, 'failed')
