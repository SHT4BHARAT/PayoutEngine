from django.db import models
from django.db.models import Sum
from django.conf import settings

class Merchant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    business_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True)
    country_code = models.CharField(max_length=2, default='IN')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def available_balance(self):
        credits = self.ledgerentry_set.filter(entry_type='credit').aggregate(s=Sum('amount_paise'))['s'] or 0
        debits = self.ledgerentry_set.filter(entry_type='debit').aggregate(s=Sum('amount_paise'))['s'] or 0
        return credits - debits

    @property
    def held_balance(self):
        return self.payout_set.filter(status__in=['pending', 'processing']).aggregate(s=Sum('amount_paise'))['s'] or 0

class BankAccount(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=20)
    account_holder_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

class LedgerEntry(models.Model):
    ENTRY_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    amount_paise = models.BigIntegerField()
    reference_id = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
