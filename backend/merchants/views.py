from rest_framework import generics, permissions
from .models import LedgerEntry
from .serializers import MerchantProfileSerializer, LedgerEntrySerializer

class MerchantProfileView(generics.RetrieveAPIView):
    serializer_class = MerchantProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.merchant

class LedgerEntryListView(generics.ListAPIView):
    serializer_class = LedgerEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LedgerEntry.objects.filter(
            merchant=self.request.user.merchant
        ).order_by('-created_at')
