from rest_framework import views, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import PayoutSerializer, PayoutReadSerializer
from .services import PayoutService
from common.errors import APIError
from merchants.models import BankAccount
from .models import Payout
# Duplicate BankAccount import removed

class PayoutCreateView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PayoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response(
                {"error": "Idempotency-Key header is required", "code": "missing_idempotency_key"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            merchant = request.user.merchant
        except Exception:
            return Response({"error": "Merchant not found", "code": "merchant_not_found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payout, created = PayoutService.create_payout(
                merchant.id,
                serializer.validated_data['bank_account_id'],
                serializer.validated_data['amount_paise'],
                idempotency_key
            )
        except APIError as e:
            resp_status = status.HTTP_400_BAD_REQUEST
            if e.code == 'insufficient_balance':
                resp_status = status.HTTP_402_PAYMENT_REQUIRED
            return Response({"error": e.message, "code": e.code}, status=resp_status)
        except ValueError as e:
            return Response({"error": str(e), "code": "invalid_request"}, status=status.HTTP_400_BAD_REQUEST)
        except BankAccount.DoesNotExist:
            return Response({"error": "Bank account not found", "code": "bank_account_not_found"}, status=status.HTTP_400_BAD_REQUEST)
            
        resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({
            "id": payout.id,
            "amount_paise": payout.amount_paise,
            "status": payout.status,
            "idempotency_key": payout.idempotency_key,
            "created_at": payout.created_at
        }, status=resp_status)

class PayoutListView(generics.ListAPIView):
    serializer_class = PayoutReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payout.objects.filter(
            merchant=self.request.user.merchant
        ).order_by('-created_at')

class PayoutDetailView(generics.RetrieveAPIView):
    serializer_class = PayoutReadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Payout.objects.filter(merchant=self.request.user.merchant)
