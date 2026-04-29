from django.urls import path
from .views import PayoutCreateView, PayoutListView, PayoutDetailView

urlpatterns = [
    path('api/v1/payouts/', PayoutCreateView.as_view(), name='payout-create'), # POST handled here
    path('api/v1/payouts/list/', PayoutListView.as_view(), name='payout-list'), # We separate GET list
    path('api/v1/payouts/<int:pk>/', PayoutDetailView.as_view(), name='payout-detail'),
]
