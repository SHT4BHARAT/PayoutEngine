from rest_framework import serializers
from .models import Payout

class PayoutSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1)
    bank_account_id = serializers.IntegerField()

class PayoutReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = [
            'id', 'amount_paise', 'status', 'idempotency_key', 
            'failure_reason', 'created_at', 'updated_at'
        ]
