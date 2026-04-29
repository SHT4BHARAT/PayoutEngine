import threading
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.db import connection
from merchants.models import Merchant, BankAccount, LedgerEntry
from payouts.models import Payout
from payouts.services import PayoutService
from common.errors import InsufficientBalance, InvalidStateTransition

class PayoutServiceTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_basic', email='test_basic@test.com')
        self.merchant = Merchant.objects.create(user=self.user, name='Test Merchant', email='test_basic@test.com')
        self.bank_account = BankAccount.objects.create(merchant=self.merchant, account_number='123', ifsc_code='ABC', account_holder_name='Test')
        
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type='credit',
            amount_paise=10000,
            description='Initial load'
        )

    def test_idempotency(self):
        p1, created1 = PayoutService.create_payout(self.merchant.id, self.bank_account.id, 1000, 'same-key')
        p2, created2 = PayoutService.create_payout(self.merchant.id, self.bank_account.id, 1000, 'same-key')
        
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(p1.id, p2.id)
        self.assertEqual(Payout.objects.count(), 1)

    def test_invalid_state_transition(self):
        p, _ = PayoutService.create_payout(self.merchant.id, self.bank_account.id, 1000, 'key1')
        self.assertEqual(p.status, 'pending')
        
        p.status = 'completed'
        with self.assertRaises(InvalidStateTransition):
            p.save()
