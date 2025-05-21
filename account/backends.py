import hashlib
import logging
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractBaseUser
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode

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

    def send_mail(  # noqa: PLR0913, PLR0917
        self,
        request: HttpRequest,
        email: str,
    ) -> None:
        subject = "Account Activation"
        message = ""
        activation_link = request.build_absolute_uri(
            reverse(
                "account:account_activation",
                kwargs={
                    "uidb64": urlsafe_base64_encode(email.encode()),
                    "token": hashlib.sha256(email.encode()).hexdigest(),
                },
            ),
        )
        html_email_template_name = render_to_string(
            "email_validation.html",
            {
                "activation_link": activation_link,
            },
        )
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
                html_message=html_email_template_name,
            )
        except Exception as error:
            logger = logging.getLogger(__name__)
            logger.exception(f"SMTP error occurred while sending email {error}")  # noqa: G004, TRY401
