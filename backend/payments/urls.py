from django.urls import path
from .views import (
    StripeWebhookView, 
    PublicPaymentLinkDetailView, 
    CreateStripeSessionView,
    MerchantPaymentLinkView
)

urlpatterns = [
    # Public endpoints
    path('api/v1/payments/pay/<uuid:slug>/', PublicPaymentLinkDetailView.as_view(), name='public-link-detail'),
    path('api/v1/payments/pay/<uuid:slug>/checkout/', CreateStripeSessionView.as_view(), name='public-checkout'),
    
    # Webhooks
    path('api/v1/payments/webhooks/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Merchant endpoints
    path('api/v1/payments/merchant/payment-links/', MerchantPaymentLinkView.as_view(), name='merchant-create-link'),
]
