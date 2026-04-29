from rest_framework import serializers
from .models import Merchant, LedgerEntry

class MerchantProfileSerializer(serializers.ModelSerializer):
    available_balance = serializers.SerializerMethodField()
    held_balance = serializers.SerializerMethodField()

    class Meta:
        model = Merchant
        fields = ['id', 'name', 'email', 'created_at', 'available_balance', 'held_balance']

    def get_balances(self, obj):
        if not hasattr(self, '_balances'):
            from .services import MerchantService
            self._balances = MerchantService.get_balances(obj)
        return self._balances

    def get_available_balance(self, obj):
        return self.get_balances(obj)['available_balance']

    def get_held_balance(self, obj):
        return self.get_balances(obj)['held_balance']

class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ['id', 'entry_type', 'amount_paise', 'reference_id', 'description', 'created_at']
