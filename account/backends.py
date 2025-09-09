from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpRequest


class AccountBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest | None,
        username: str | None = None,
        password: str | None = None,
        email: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> AbstractBaseUser | None:
        user_model = get_user_model()

        if not email or not password:
            return None

        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist:
            return None

        if (
            password
            and user.check_password(password)
            and self.user_can_authenticate(user)
        ):
            user.backend = "account.backends.AccountBackend"  # type: ignore
            return user

        return None
