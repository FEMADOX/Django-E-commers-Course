from django.contrib.auth.views import LogoutView
from django.urls import path

from account.views import (
    AccountActivationView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomPasswordResetView,
    EmailActivationView,
    UserAccountView,
    UserLoginView,
    UserSignupView,
    UserUpdateView,
)

app_name = "account"

urlpatterns = [
    path("", UserAccountView.as_view(), name="user_account"),
    path("update/", UserUpdateView.as_view(), name="update_account"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("signup/", UserSignupView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "activate/<str:uidb64>/<str:token>/",
        AccountActivationView.as_view(),
        name="account_activation",
    ),
    path("email-validation/", EmailActivationView.as_view(), name="email_validation"),
    path(
        "password-reset/",
        CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
