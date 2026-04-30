import uuid
from django.db import models
from merchants.models import Merchant

class PaymentLink(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='payment_links')
    slug = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Financials locked at creation
    amount_usd_cents = models.BigIntegerField()
    tax_amount_usd_cents = models.BigIntegerField(default=0)
    total_amount_usd_cents = models.BigIntegerField()
    
    forex_rate_locked = models.DecimalField(max_digits=10, decimal_places=4)
    platform_fee_usd_cents = models.BigIntegerField()
    merchant_receives_inr_paise = models.BigIntegerField()
    
    is_active = models.BooleanField(default=True)
    is_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.slug})"
