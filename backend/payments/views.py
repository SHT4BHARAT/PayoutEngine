import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import views, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import PaymentLink
from .services import PaymentCollectionService, PaymentCreditService

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            # Invalid payload or signature
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            PaymentCreditService.handle_stripe_success(session['id'])

        return Response({'status': 'success'}, status=status.HTTP_200_OK)

class PublicPaymentLinkDetailView(generics.RetrieveAPIView):
    """
    Publicly accessible view to get payment link details.
    """
    queryset = PaymentLink.objects.filter(is_active=True)
    serializer_class = None # I'll define a serializer below
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get(self, request, *args, **kwargs):
        link = self.get_object()
        return Response({
            'title': link.title,
            'description': link.description,
            'amount_usd_cents': link.amount_usd_cents,
            'total_amount_usd_cents': link.total_amount_usd_cents,
            'is_paid': link.is_paid,
            'merchant_name': link.merchant.business_name if hasattr(link.merchant, 'business_name') else str(link.merchant)
        })

class CreateStripeSessionView(views.APIView):
    """
    Initiates a Stripe Checkout session for a public link.
    """
    permission_classes = [AllowAny]

    def post(self, request, slug):
        try:
            link = PaymentLink.objects.get(slug=slug, is_active=True)
            if link.is_paid:
                return Response({'error': 'This link has already been paid'}, status=status.HTTP_400_BAD_REQUEST)
            
            # success_url and cancel_url should ideally come from frontend or config
            success_url = request.build_absolute_uri(f'/pay/{slug}/success')
            cancel_url = request.build_absolute_uri(f'/pay/{slug}')
            
            checkout_url = PaymentCollectionService.create_stripe_session(link, success_url, cancel_url)
            return Response({'stripe_url': checkout_url})
            
        except PaymentLink.DoesNotExist:
            return Response({'error': 'Link not found'}, status=status.HTTP_404_NOT_FOUND)

class MerchantPaymentLinkView(views.APIView):
    """
    Merchant endpoint to create payment links.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        merchant = request.user.merchant # Assuming User has merchant profile
        title = request.data.get('title')
        amount_usd_cents = request.data.get('amount_usd_cents')
        description = request.data.get('description', '')

        if not title or not amount_usd_cents:
            return Response({'error': 'Title and amount are required'}, status=status.HTTP_400_BAD_REQUEST)

        link = PaymentCollectionService.create_payment_link(
            merchant, title, int(amount_usd_cents), description
        )
        
        return Response({
            'slug': str(link.slug),
            'public_url': request.build_absolute_uri(f'/pay/{link.slug}')
        }, status=status.HTTP_201_CREATED)
