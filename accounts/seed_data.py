"""Demo KYC seed data.

Run with:  python manage.py shell < accounts/seed_data.py
"""
from accounts.models import User, KYCProfile

SEED = [
    {
        'email': 'rahul.mehta@gmail.com', 'phone': '+91-98200-11234',
        'aadhaar': '4321 8765 2109', 'pan': 'AKPPM1234C',
        'bank_account_number': '50100234567890', 'ifsc': 'HDFC0001234',
        'upi': 'rahul@okhdfc', 'card_number': '4111 1111 1111 1111',
        'cvv': '312', 'annual_income': 1450000, 'credit_score': 762,
    },
    {
        'email': 'sneha.iyer@gmail.com', 'phone': '+91-99300-55678',
        'aadhaar': '5678 1234 9087', 'pan': 'BLMPS5678K',
        'bank_account_number': '00123456789012', 'ifsc': 'ICIC0000123',
        'upi': 'sneha@okicici', 'card_number': '5500 0000 0000 0004',
        'cvv': '890', 'annual_income': 980000, 'credit_score': 705,
    },
    {
        'email': 'arjun.nair@gmail.com', 'phone': '+91-98765-43210',
        'aadhaar': '9012 3456 7823', 'pan': 'CNZPN9012M',
        'bank_account_number': '911010049001234', 'ifsc': 'UTIB0000456',
        'upi': 'arjun@okaxis', 'card_number': '6011 0009 9013 9424',
        'cvv': '145', 'annual_income': 2100000, 'credit_score': 811,
    },
]

for row in SEED:
    email = row.pop('email')
    user, _ = User.objects.get_or_create(email=email)
    KYCProfile.objects.update_or_create(user=user, defaults=row)
    print(f'seeded KYC for {email}')
