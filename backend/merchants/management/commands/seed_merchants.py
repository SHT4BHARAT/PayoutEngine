from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from merchants.models import Merchant, BankAccount, LedgerEntry

class Command(BaseCommand):
    help = 'Seeds the database with initial merchants, bank accounts, and balances'

    def handle(self, *args, **kwargs):
        # Clear existing
        User.objects.all().delete()
        
        merchants_data = [
            {"username": "merchant_1", "email": "agency1@example.com", "name": "Alpha Agency", "balance": 1000000}, # 10,000 INR
            {"username": "merchant_2", "email": "agency2@example.com", "name": "Beta Studios", "balance": 2500000}, # 25,000 INR
            {"username": "merchant_3", "email": "freelancer1@example.com", "name": "Gamma Freelancer", "balance": 500000}, # 5,000 INR
        ]

        for i, data in enumerate(merchants_data):
            user = User.objects.create_user(username=data["username"], email=data["email"], password="password123")
            fixed_key = f"{i+1}4b5d28deb65a613cea091beaf7cdef6c3d2ec83"
            token = Token.objects.create(user=user, key=fixed_key)
            
            merchant = Merchant.objects.create(user=user, name=data["name"], email=data["email"])
            
            BankAccount.objects.create(
                merchant=merchant, 
                account_number=f"123456789{user.id}", 
                ifsc_code="HDFC0001234", 
                account_holder_name=data["name"]
            )
            
            # Seed 5 credits to make up the total balance
            amount_per_entry = data["balance"] // 5
            for i in range(5):
                LedgerEntry.objects.create(
                    merchant=merchant,
                    entry_type='credit',
                    amount_paise=amount_per_entry,
                    description=f"Simulated inbound customer payment {i+1}"
                )
            
            self.stdout.write(self.style.SUCCESS(f'Created merchant {merchant.name} - Token: {token.key}'))
            
        self.stdout.write(self.style.SUCCESS('Successfully seeded 3 merchants.'))
