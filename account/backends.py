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
        email: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> AbstractBaseUser | None:
        if not (request and request.method == "POST"):
            return None

        user_model = get_user_model()

        if not email or not password:
            return None

        try:
            if email and username:
                user = user_model.objects.get(email=email, username=username)
            elif email:
                user = user_model.objects.get(email=email)
            else:
                user = user_model.objects.get(username=username)
        except user_model.DoesNotExist:
            return None

        if password and user.check_password(password):
            return user

        return None
