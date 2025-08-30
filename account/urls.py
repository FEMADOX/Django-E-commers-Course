from django.urls import path

from account import views
from account.views import (
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomPasswordResetView,
    EmailValidationView,
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
    path("logout/", views.logout_user, name="logout_user"),
    path(
        "activate/<uidb64>/<token>/",
        views.account_activation,
        name="account_activation",
    ),
    path("email-validation/", EmailValidationView.as_view(), name="email_validation"),
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
        # auth_views.PasswordResetConfirmView.as_view(),
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
]
