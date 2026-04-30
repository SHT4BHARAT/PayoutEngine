import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import PaymentLink
from merchants.models import LedgerEntry
from common.fees import FeeEngine
from common.forex import get_usd_to_inr_rate
from compliance.tax import calculate_tax

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentCollectionService:
    @staticmethod
    def create_payment_link(merchant, title, amount_usd_cents, description=""):
        """
        Creates a PaymentLink with locked financials.
        """
        # 1. Get current forex rate
        forex_rate = get_usd_to_inr_rate()
        
        # 2. Calculate tax (using merchant country for MVP)
        # Assuming Merchant model has a country_code field, if not default to 'IN'
        country_code = getattr(merchant, 'country_code', 'IN')
        tax_info = calculate_tax(amount_usd_cents, country_code)
        
        # 3. Calculate fees
        fee_info = FeeEngine.calculate_fees(amount_usd_cents)
        
        # 4. Calculate final settlement in INR
        merchant_net_usd_cents = fee_info['merchant_net_usd_cents']
        merchant_receives_inr_paise = FeeEngine.usd_to_inr_paise(merchant_net_usd_cents, forex_rate)
        
        # 5. Create the link record
        payment_link = PaymentLink.objects.create(
            merchant=merchant,
            title=title,
            description=description,
            amount_usd_cents=amount_usd_cents,
            tax_amount_usd_cents=tax_info['tax_amount_usd_cents'],
            total_amount_usd_cents=tax_info['total_amount_usd_cents'],
            forex_rate_locked=forex_rate,
            platform_fee_usd_cents=fee_info['platform_fee_usd_cents'],
            merchant_receives_inr_paise=merchant_receives_inr_paise
        )
        
        return payment_link

    @staticmethod
    def create_stripe_session(payment_link, success_url, cancel_url):
        """
        Creates a Stripe Checkout Session for a PaymentLink.
        """
        session = stripe.checkout.Session.create(
            payment_method_types=['card', 'affirm', 'klarna'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': payment_link.title,
                        'description': payment_link.description,
                    },
                    'unit_amount': payment_link.total_amount_usd_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'payment_link_id': str(payment_link.id),
                'merchant_id': str(payment_link.merchant.id)
            }
        )
        return session.url

class PaymentCreditService:
    @staticmethod
    def handle_stripe_success(stripe_session_id):
        """
        Idempotently credits the merchant ledger after successful Stripe payment.
        """
        # Idempotency check using Stripe session ID
        reference_id = f"stripe_{stripe_session_id}"
        if LedgerEntry.objects.filter(reference_id=reference_id).exists():
            return "Already processed"

        try:
            session = stripe.checkout.Session.retrieve(stripe_session_id)
            payment_link_id = session.metadata.get('payment_link_id')
            payment_link = PaymentLink.objects.get(id=payment_link_id)
        except (stripe.error.StripeError, PaymentLink.DoesNotExist):
            return "Invalid session or link"

        with transaction.atomic():
            # Double check inside transaction
            if LedgerEntry.objects.filter(reference_id=reference_id).exists():
                return "Already processed"

            # 1. Create LedgerEntry (Credit)
            LedgerEntry.objects.create(
                merchant=payment_link.merchant,
                entry_type='credit',
                amount_paise=payment_link.merchant_receives_inr_paise,
                reference_id=reference_id,
                description=f"Payment for {payment_link.title} (Link: {payment_link.slug})"
            )

            # 2. Mark link as paid
            payment_link.is_paid = True
            payment_link.save()

        return "Success"
