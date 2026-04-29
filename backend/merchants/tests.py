from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from merchants.models import Merchant, BankAccount, LedgerEntry
from merchants.services import MerchantService

class MerchantTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', email='test@test.com')
        self.merchant = Merchant.objects.create(user=self.user, name='Test Merchant', email='test@test.com')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_merchant_service_get_balances(self):
        # Initially 0
        b = MerchantService.get_balances(self.merchant)
        self.assertEqual(b['available_balance'], 0)
        self.assertEqual(b['held_balance'], 0)

        # Add 10,000 paise credit
        LedgerEntry.objects.create(merchant=self.merchant, entry_type='credit', amount_paise=10000, description='Inbound')
        b = MerchantService.get_balances(self.merchant)
        self.assertEqual(b['available_balance'], 10000)

        # Add 2,000 paise debit
        LedgerEntry.objects.create(merchant=self.merchant, entry_type='debit', amount_paise=2000, description='Payout hold')
        b = MerchantService.get_balances(self.merchant)
        self.assertEqual(b['available_balance'], 8000)

    def test_merchant_profile_api(self):
        LedgerEntry.objects.create(merchant=self.merchant, entry_type='credit', amount_paise=10000, description='Inbound')
        res = self.client.get('/api/v1/merchants/me/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['available_balance'], 10000)
        self.assertEqual(res.data['name'], 'Test Merchant')

    def test_merchant_ledger_api(self):
        LedgerEntry.objects.create(merchant=self.merchant, entry_type='credit', amount_paise=10000, description='Inbound')
        LedgerEntry.objects.create(merchant=self.merchant, entry_type='debit', amount_paise=2000, description='Hold')
        res = self.client.get('/api/v1/merchants/me/ledger/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 2)
        self.assertEqual(res.data['results'][0]['entry_type'], 'debit') # Newest first
