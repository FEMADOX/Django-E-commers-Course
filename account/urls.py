from django.urls import path, re_path

from account import views

app_name = "account"

urlpatterns = [
    path("", views.user_account, name="user_account"),
    path("update/", views.update_account, name="update_account"),
    re_path(r".*login-signup/$", views.create_user, name="create_user"),
    path("login/", views.login_user, name="login_user"),
    path("logout/", views.logout_user, name="logout_user"),

]
