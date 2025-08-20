from django.urls import path

from account import views

app_name = "account"

urlpatterns = [
    path("", views.user_account, name="user_account"),
    path("update/", views.update_account, name="update_account"),
    path("login/", views.login_user, name="login_user"),
    path("signup/", views.create_user, name="create_user"),
    path("logout/", views.logout_user, name="logout_user"),
    path(
        "activate/<uidb64>/<token>/",
        views.account_activation,
        name="account_activation",
    ),
]
