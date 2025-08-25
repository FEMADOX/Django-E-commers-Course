from django.urls import path

from account import views
from account.views import UserAccountView, UserUpdateAccountView, UserCreateAccountView, EmailValidationView

app_name = "account"

urlpatterns = [
    path("", UserAccountView.as_view(), name="user_account"),
    # path("update/", views.update_account, name="update_account"),
    path("update/", UserUpdateAccountView.as_view(), name="update_account"),
    path("login/", views.my_login, name="login"),
    # path("signup/", views.create_user, name="create_user"),
    path("signup/", UserCreateAccountView.as_view(), name="signup"),
    path("logout/", views.logout_user, name="logout_user"),
    path(
        "activate/<uidb64>/<token>/",
        views.account_activation,
        name="account_activation",
    ),
    path("email_validation/", EmailValidationView.as_view(), name="email_validation")
]
