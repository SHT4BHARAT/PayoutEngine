from django.urls import path
from .views import MerchantProfileView, LedgerEntryListView

urlpatterns = [
    path('api/v1/merchants/me/', MerchantProfileView.as_view(), name='merchant-profile'),
    path('api/v1/merchants/me/ledger/', LedgerEntryListView.as_view(), name='merchant-ledger'),
]
