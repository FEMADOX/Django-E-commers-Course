from django.urls import path
from django.contrib.auth import views as auth_views

from account import views
from account.views import (
    CustomPasswordResetDoneView,
    CustomPasswordResetView,
    EmailValidationView,
    UserAccountView,
    UserLoginView,
    UserSignupView,
    UserUpdateView,
    CustomPasswordResetConfirmView,
)

app_name = "account"

urlpatterns = [
    path("", UserAccountView.as_view(), name="user_account"),
    # path("update/", views.update_account, name="update_account"),
    path("update/", UserUpdateView.as_view(), name="update_account"),
    # path("login/", views.my_login, name="login"),
    path("login/", UserLoginView.as_view(), name="login"),
    # path("signup/", views.create_user, name="create_user"),
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
