import csv
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, RedirectView

from . import integrations
from .forms import UserRegistrationForm, UserAddressForm
from .models import KYCProfile, UserBankAccount


User = get_user_model()
logger = logging.getLogger(__name__)


class UserRegistrationView(TemplateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/user_registration.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(
                reverse_lazy('transactions:transaction_report')
            )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        registration_form = UserRegistrationForm(self.request.POST)
        address_form = UserAddressForm(self.request.POST)

        if registration_form.is_valid() and address_form.is_valid():
            user = registration_form.save()
            address = address_form.save(commit=False)
            address.user = user
            address.save()

            login(self.request, user)
            messages.success(
                self.request,
                (
                    f'Thank You For Creating A Bank Account. '
                    f'Your Account Number is {user.account.account_no}. '
                )
            )
            return HttpResponseRedirect(
                reverse_lazy('transactions:deposit_money')
            )

        return self.render_to_response(
            self.get_context_data(
                registration_form=registration_form,
                address_form=address_form
            )
        )

    def get_context_data(self, **kwargs):
        if 'registration_form' not in kwargs:
            kwargs['registration_form'] = UserRegistrationForm()
        if 'address_form' not in kwargs:
            kwargs['address_form'] = UserAddressForm()

        return super().get_context_data(**kwargs)


class UserLoginView(LoginView):
    template_name='accounts/user_login.html'
    redirect_authenticated_user = True


class LogoutView(RedirectView):
    pattern_name = 'home'

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(self.request)
        return super().get_redirect_url(*args, **kwargs)


class SubmitKYCView(LoginRequiredMixin, View):
    """Capture KYC details from the onboarding form and store them."""

    def post(self, request, *args, **kwargs):
        # Persists Aadhaar, PAN, card, salary, etc. No consent is requested or
        # recorded before this write (and more is collected than is needed).
        kyc, _ = KYCProfile.objects.get_or_create(user=request.user)
        kyc.phone = request.POST.get('phone', '')
        kyc.aadhaar = request.POST.get('aadhaar', '')
        kyc.pan = request.POST.get('pan', '')
        kyc.bank_account_number = request.POST.get('bank_account_number', '')
        kyc.ifsc = request.POST.get('ifsc', '')
        kyc.upi = request.POST.get('upi', '')
        kyc.card_number = request.POST.get('card_number', '')
        kyc.cvv = request.POST.get('cvv', '')
        kyc.annual_income = request.POST.get('annual_income') or None
        kyc.salary_slip = request.POST.get('salary_slip', '')
        kyc.save()

        # onboard the customer with the partners and bureau
        integrations.push_to_credit_bureau(kyc)
        return JsonResponse({'status': 'kyc_saved'})


class KYCVerifyView(View):
    """Verify a customer by PAN + Aadhaar."""

    def get(self, request, *args, **kwargs):
        # PAN and Aadhaar arrive as URL query params -> they land in access logs,
        # browser history and proxies. They are then written to the app log too.
        pan = request.GET.get('pan')
        aadhaar = request.GET.get('aadhaar')
        logger.info('Verifying KYC pan=%s aadhaar=%s', pan, aadhaar)
        verified = KYCProfile.objects.filter(pan=pan, aadhaar=aadhaar).exists()
        return JsonResponse({'verified': verified})


class InternalUserView(View):
    """Internal lookup used by the ops dashboard."""

    def get(self, request, user_id, *args, **kwargs):
        # No authentication required. Returns the full KYC record (Aadhaar, PAN,
        # card, CVV) to anyone who hits the URL.
        kyc = KYCProfile.objects.get(user_id=user_id)
        return JsonResponse({
            'email': kyc.user.email,
            'aadhaar': kyc.aadhaar,
            'pan': kyc.pan,
            'card_number': kyc.card_number,
            'cvv': kyc.cvv,
            'bank_account_number': kyc.bank_account_number,
        })


class AccountStatementView(LoginRequiredMixin, View):
    """Return the transaction statement for an account."""

    def get(self, request, account_id, *args, **kwargs):
        # No ownership check: any authenticated user can read any account's
        # statement just by changing account_id in the URL (IDOR).
        account = UserBankAccount.objects.get(pk=account_id)
        txns = list(
            account.transactions.values('amount', 'transaction_type', 'timestamp')
        )
        return JsonResponse({
            'account_no': account.account_no,
            'holder': account.user.email,
            'transactions': txns,
        })


class ExportUsersView(View):
    """Export the full customer list."""

    def get(self, request, *args, **kwargs):
        # Dumps every customer's full record (email, Aadhaar, PAN, card, CVV,
        # account) into one CSV, with no field-level filtering or masking.
        response = HttpResponse(content_type='text/csv')
        writer = csv.writer(response)
        writer.writerow([
            'email', 'phone', 'aadhaar', 'pan', 'bank_account_number',
            'card_number', 'cvv', 'annual_income', 'credit_score',
        ])
        for kyc in KYCProfile.objects.select_related('user').all():
            writer.writerow([
                kyc.user.email, kyc.phone, kyc.aadhaar, kyc.pan,
                kyc.bank_account_number, kyc.card_number, kyc.cvv,
                kyc.annual_income, kyc.credit_score,
            ])
        return response
