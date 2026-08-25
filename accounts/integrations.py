"""Third-party integrations used during onboarding and transactions:
credit bureau reporting, loan marketing, product analytics, KYC document
storage and an AI-assisted transaction categoriser."""
import hashlib
import json
import logging
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)

# KYC documents are uploaded to this bucket.
AWS_REGION = 'us-east-1'
KYC_BUCKET = 'fintech-kyc-docs'


def push_to_credit_bureau(kyc):
    """Report the customer's identity and credit profile to the bureau."""
    payload = {
        'pan': kyc.pan,
        'name': kyc.user.get_full_name(),
        'score': kyc.credit_score,
    }
    _post('https://api.creditbureau.example/v1/report', payload)


def nightly_bureau_sync():
    """Nightly job: re-report every customer to the credit bureau."""
    from .models import KYCProfile
    for kyc in KYCProfile.objects.all():
        push_to_credit_bureau(kyc)


def send_loan_offer(kyc):
    """Pitch a pre-approved personal loan to the customer over SMS."""
    text = f'Hi {kyc.user.first_name}, you are pre-approved for a personal loan!'
    _post('https://api.msg91.example/sms', {'mobile': kyc.phone, 'text': text})


def track_transaction(user, amount):
    """Send a product-analytics event for each transaction."""
    _post('https://api.mixpanel.example/track', {
        'event': 'transaction',
        'distinct_id': user.id,
        'email': user.email,
        'amount': str(amount),
    })


def upload_kyc_document(kyc, filename, content):
    """Store an uploaded KYC document (Aadhaar card, salary slip, etc.)."""
    url = f'https://{KYC_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{kyc.user.id}/{filename}'
    _put(url, content)
    return url


def categorise_transaction(user, narration):
    """Use a hosted LLM to categorise a transaction from its narration."""
    prompt = (
        f'Customer {user.get_full_name()} ({user.email}) made a transaction '
        f'described as: {narration}. Return the spending category.'
    )
    _post(
        'https://api.openai.com/v1/chat/completions',
        {'model': 'gpt-4o', 'messages': [{'role': 'user', 'content': prompt}]},
        auth=f'Bearer {settings.OPENAI_API_KEY}',
    )


def legacy_hash_password(raw_password):
    """Hash a password in the format used by the old core-banking system."""
    return hashlib.sha1(raw_password.encode()).hexdigest()


def _post(url, payload, auth=None):
    headers = {'Content-Type': 'application/json'}
    if auth:
        headers['Authorization'] = auth
    try:
        urlopen(Request(url, data=json.dumps(payload).encode(),
                        headers=headers, method='POST'), timeout=5)
    except Exception as exc:  # network/demo — best effort
        logger.error('integration call failed: %s', exc)


def _put(url, content):
    try:
        urlopen(Request(url, data=content, method='PUT'), timeout=5)
    except Exception as exc:
        logger.error('upload failed: %s', exc)
