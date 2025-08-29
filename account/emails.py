import hashlib
import logging

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from account.backends import get_user_model
from edshop.settings import EMAIL_HOST_USER

# class EmailService:
#     def __init__(
#         self,
#         subject: str,
#         message: str | None,
#         recipient: str,
#         sender: str | None,
#         html_email_template_name: str | None,
#     ) -> None:
#         self.subject = subject
#         self.message = message or ""
#         self.sender = sender or EMAIL_HOST_USER
#         self.recipient = recipient
#         self.html_email_template_name = html_email_template_name or None


def my_send_email(
    subject: str,
    recipient: str,
    message: str = "",
    sender: str = EMAIL_HOST_USER,
    html_email_template_name: str | None = None,
) -> None:
    try:
        send_mail(
            subject,
            message,
            sender,
            [recipient],
            fail_silently=False,
            html_message=html_email_template_name,
        )
    except Exception as error:
        logger = logging.getLogger(__name__)
        msg = f"SMTP error occurred while sending email {error}"
        logger.exception(msg)


# class AccountEmailService(EmailService):
def send_account_activation_email(
    request: HttpRequest,
    email: str,
) -> None:
    subject = "Activate your account"
    activation_link = request.build_absolute_uri(
        reverse(
            "account:account_activation",
            kwargs={
                "uidb64": urlsafe_base64_encode(email.encode()),
                "token": hashlib.sha256(email.encode()).hexdigest(),
            },
        ),
    )
    recipient = email
    html_email_template_name = render_to_string(
        "account/activation/account_activation_email.html",
        {
            "activation_link": activation_link,
        },
    )
    my_send_email(
        subject,
        recipient,
        html_email_template_name=html_email_template_name,
    )

    # class PasswordResetEmailService(EmailService):


def send_password_reset_email(
    request: HttpRequest,
    email: str,
    context: dict | None = None,
) -> None:
    subject = "Password Reset"
    recipient = email
    user = get_user_model().objects.get(email=email)

    uid64 = urlsafe_base64_encode(force_bytes(email))
    token = default_token_generator.make_token(user)

    activation_link = request.build_absolute_uri(
        reverse(
            "account:password_reset_confirm",
            kwargs={
                "uidb64": uid64,
                "token": token,
            },
        ),
    )
    html_email_template_name = render_to_string(
        "account/password/reset_email.html",
        {
            "activation_link": activation_link,
        },
    )
    my_send_email(
        subject,
        recipient,
        html_email_template_name=html_email_template_name,
    )
