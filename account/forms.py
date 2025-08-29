import re
from string import punctuation
from typing import Any

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from account.emails import my_send_email
from account.models import Client


class DateInput(forms.DateInput):
    input_type = "date"


class ClientForm(forms.ModelForm):
    SEX_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        ("N", "Null"),
    )

    dni = forms.CharField(label="DNI", max_length=8, required=False)
    name = forms.CharField(label="Name/s", max_length=100, required=True)
    last_name = forms.CharField(label="Last Name", max_length=100, required=False)
    sex = forms.ChoiceField(label="Sex", choices=SEX_CHOICES, required=False)
    email = forms.EmailField(label="Email", required=True)
    address = forms.CharField(label="Address", required=False, widget=forms.Textarea)
    phone = forms.CharField(label="Phone", max_length=20, required=False)
    birth = forms.DateField(
        label="Birth Date",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=DateInput(),
    )

    class Meta:
        model = Client
        fields = [
            "dni",
            "name",
            "last_name",
            "sex",
            "email",
            "address",
            "phone",
            "birth",
        ]


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="",
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control email-reset",
                "placeholder": "Enter your email",
            },
        ),
    )

    def send_mail(  # noqa: PLR0913, PLR0917
        self,
        subject_template_name: str,
        email_template_name: str,
        context: dict[str, Any],
        from_email: str | None,
        to_email: str,
        html_email_template_name: str | None = None,
    ) -> None:
        subject = "Password Reset Email"
        email = context["email"]
        user = get_user_model().objects.get(email=email)
        recipient = email
        uid64 = urlsafe_base64_encode(force_bytes(email))
        # token = hashlib.sha256(email.encode()).hexdigest()
        token = default_token_generator.make_token(user)

        # Generate activation link
        site = context["domain"]
        protocol = context["protocol"]
        activation_link = f"{protocol}://{site}" + reverse(
            "account:password_reset_confirm",
            kwargs={
                "uidb64": uid64,
                "token": token,
            },
        )

        # Add activation link to context
        context["activation_link"] = activation_link
        html_email_template_name = render_to_string(
            "account/password/reset_email.html",
            context,
        )

        my_send_email(
            subject,
            recipient,
            html_email_template_name=html_email_template_name,
        )


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control password-reset",
                "placeholder": "Enter new password",
                "autocomplete": "new-password",
            },
        ),
        help_text=(
            "At least 8 characters (at least "
            "1 uppercase letter, 1 lowercase letter, 1 number and 1 special character)."
        ),
    )
    new_password2 = forms.CharField(
        label="",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control password-reset",
                "placeholder": "Confirm new password",
                "autocomplete": "new-password",
            },
        ),
        help_text="Enter the same password as before, for verification.",
    )

    def clean(self) -> dict[str, Any] | None:
        cleaned_data = super().clean()

        if not cleaned_data:
            return None

        password = cleaned_data.get("new_password1")
        if password:
            regex_validation = (
                re.search(r"[a-z]", password)
                and re.search(r"[A-Z]", password)
                and re.search(r"[0-9]", password)
                and re.search(rf"[{punctuation}]", password)
            )
            if not regex_validation:
                self.add_error("new_password2", "Password must contain:")
                errors = []
                if not re.search(r"[a-z]", password):
                    errors.append("At least one lowercase letter.")
                if not re.search(r"[A-Z]", password):
                    errors.append("At least one uppercase letter.")
                if not re.search(r"[0-9]", password):
                    errors.append("At least one number.")
                if not re.search(rf"[{punctuation}]", password):
                    errors.append(f"At least one symbol ({punctuation}).")
                [self.add_error("new_password2", error) for error in errors]
        return cleaned_data
