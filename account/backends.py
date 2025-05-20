from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractBaseUser

from account.views import HttpRequest


class AccountBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> AbstractBaseUser | None:
        User = get_user_model()  # noqa: N806

        if request and request.method == "POST":
            email = request.POST.get("email")
            if email and username:
                try:
                    user = User.objects.get(email=email, username=username)
                except User.DoesNotExist:
                    return None
            if email or username:
                try:
                    user = (
                        User.objects.get(email=email)
                        if email
                        else User.objects.get(username=username)
                    )
                except User.DoesNotExist:
                    return None
                if password and user.check_password(password):
                    return user
                return None
            return None
        return None
