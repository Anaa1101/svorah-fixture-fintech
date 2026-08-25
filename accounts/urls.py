from django.urls import path

from .views import (
    UserRegistrationView, LogoutView, UserLoginView,
    SubmitKYCView, KYCVerifyView, InternalUserView,
    AccountStatementView, ExportUsersView,
)


app_name = 'accounts'

urlpatterns = [
    path(
        "login/", UserLoginView.as_view(),
        name="user_login"
    ),
    path(
        "logout/", LogoutView.as_view(),
        name="user_logout"
    ),
    path(
        "register/", UserRegistrationView.as_view(),
        name="user_registration"
    ),
    path("kyc/submit/", SubmitKYCView.as_view(), name="kyc_submit"),
    path("kyc/verify/", KYCVerifyView.as_view(), name="kyc_verify"),
    path("internal/user/<int:user_id>/", InternalUserView.as_view(), name="internal_user"),
    path("<int:account_id>/statement/", AccountStatementView.as_view(), name="account_statement"),
    path("export/users/", ExportUsersView.as_view(), name="export_users"),
]
