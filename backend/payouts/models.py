from django.db import models
from django.utils import timezone
from merchants.models import Merchant, BankAccount
from common.errors import InvalidStateTransition

class Payout(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    amount_paise = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    idempotency_key = models.CharField(max_length=255)
    idempotency_expires_at = models.DateTimeField()
    
    held_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    failure_reason = models.TextField(null=True, blank=True)
    attempt_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('merchant', 'idempotency_key')

    def save(self, *args, **kwargs):
        if self.pk:
            orig = Payout.objects.get(pk=self.pk)
            # pending -> processing -> completed
            # pending -> processing -> failed
            if orig.status == 'pending' and self.status not in ['pending', 'processing']:
                raise InvalidStateTransition("Invalid state transition from pending")
            if orig.status == 'processing' and self.status not in ['processing', 'completed', 'failed']:
                raise InvalidStateTransition("Invalid state transition from processing")
            if orig.status in ['completed', 'failed'] and self.status != orig.status:
                raise InvalidStateTransition("Invalid state transition from terminal state")
        super().save(*args, **kwargs)
