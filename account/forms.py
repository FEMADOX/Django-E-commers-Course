import re
from datetime import UTC, datetime
from re import Match
from string import punctuation
from typing import Any

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.forms.models import ModelForm
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls.base import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.debug import sensitive_variables

from account.backends import AccountBackend
from account.emails import my_send_email
from account.models import Client


def regex_validation(
    form: ModelForm | forms.Form,
    form_field: str,
    password: str,
) -> Match[str] | None:
    """
    Validates password strength using regex patterns and
    adds errors to form if validation fails.

    Checks that the password contains at least:
      one lowercase letter
      one uppercase letter
      one digit
      one punctuation character
    If any requirement is not met,
    adds specific error messages to the specified form field.

    Args:
        form (ModelForm | forms.Form): The Django form instance to add errors to
        form_field (str): The name of the form field to associate errors with
        password (str): The password string to validate

    Returns:
        Match[str] | None: Returns the result of the regex validation (truthy if all
                          patterns match, falsy otherwise)

    Note:
        Requires 'punctuation' to be imported from string module and 're' module
        for regex operations. Adds multiple error messages to the form field if
        validation fails.
    """
    validation = (
        re.search(r"[a-z]", password)
        and re.search(r"[A-Z]", password)
        and re.search(r"[0-9]", password)
        and re.search(rf"[{punctuation}]", password)
    )
    if not validation:
        form.add_error(form_field, "Invalid password.")
        form.add_error(form_field, "Password must contain:")
        errors = []
        if not re.search(r"[a-z]", password):
            errors.append("At least one lowercase letter.")
        if not re.search(r"[A-Z]", password):
            errors.append("At least one uppercase letter.")
        if not re.search(r"[0-9]", password):
            errors.append("At least one number.")
        if not re.search(rf"[{punctuation}]", password):
            errors.append(f"At least one symbol ({punctuation}).")
        [form.add_error(form_field, error) for error in errors]
    return validation


class DateInput(forms.DateInput):
    input_type = "date"


class ClientForm(forms.ModelForm):
    SEX_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
        ("N", "Null"),
    )
    MAX_BIRTH_DATE = datetime.now(tz=UTC).date().isoformat()

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
        widget=DateInput(
            #     No Future Dates
            attrs={
                "min": "1900-01-01",
                "max": MAX_BIRTH_DATE,
            },
        ),
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
            regex_validation(self, "new_password2", password)
        return cleaned_data


class SmartAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        min_length=10,
        max_length=100,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control email-login",
                "placeholder": "email@gmail.com",
                "autocomplete": "email",
            },
        ),
        required=True,
    )
    password = forms.CharField(
        label="Password",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control password-login",
                "placeholder": (
                    "1 uppercase, 1 lowercase, 1 number, 1 special character"
                ),
                "autocomplete": "current-password",
            },
        ),
        required=True,
    )

    error_messages = {
        "invalid_login": (
            "Please enter a correct %(email)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        "invalid_signup": "Email already registered. Please use another email.",
        "inactive": "This account is inactive.",
        "invalid_field": "invalid %(field)s",
    }

    def __init__(
        self,
        is_signup: bool,
        request: HttpRequest | None = None,
        *arg: Any,  # noqa: ANN401
        **kwargs: dict,
    ) -> None:
        kwargs.pop("instance", None)
        super().__init__(*arg, **kwargs)
        self.request = request
        self.is_signup = is_signup
        self.user_cache = None
        self.email_field = self.fields["email"]

    def clean_email(self) -> str | None:
        """
        Validate that the email address is not already registered.

        This method checks if the provided email address already exists in the
        User model. If an email is found to be already registered, it raises
        a ValidationError with the 'invalid_signup' error message.

        Returns:
            str | None: The cleaned email address if validation passes, or None
                        if no email was provided.

        Raises:
            ValidationError: If the email address is already registered in the system.
        """
        if self.is_signup:
            email = self.cleaned_data.get("email")
            if email and get_user_model().objects.filter(email=email).exists():
                raise ValidationError(
                    self.error_messages["invalid_signup"],
                    code="invalid_signup",
                )
            return email

        return self.cleaned_data["email"]

    def clean_password(self) -> str | None:
        """
        Validate and clean the password field.

        Retrieves the password from cleaned_data and performs regex validation
        on it. If no password is provided, returns None.

        Returns:
            str | None: The cleaned password string if valid, None if not provided.

        Raises:
            ValidationError: If the password fails regex validation
            (raised by regex_validation).
        """
        password = self.cleaned_data.get("password")
        if not password:
            return None
        regex_validation(self, "password", password)
        return password

    @sensitive_variables()
    def clean(self) -> dict[str, Any] | None:
        """
        Validate the form data by authenticating the user with email and password.

        This method performs the following validations:
        1. Retrieves email and password from cleaned data
        2. Attempts to authenticate the user using AccountBackend
        3. Raises validation error if authentication fails
        4. Confirms that the authenticated user is allowed to login

        Returns:
            dict[str, Any]: The cleaned form data if validation passes

        Raises:
            ValidationError: If authentication fails or login is not allowed
        """
        if self.is_signup:
            return super().clean()

        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data

        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user_cache = AccountBackend().authenticate(
                self.request,
                email=email,
                password=password,
            )
            if not self.user_cache:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return cleaned_data

    def confirm_login_allowed(self, user: AbstractBaseUser) -> None:
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``ValidationError``.

        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )

    def get_user(self) -> AbstractBaseUser | None:
        return self.user_cache

    def get_invalid_login_error(self) -> ValidationError:
        """
        Generate a ValidationError for invalid login attempts.

        Creates a standardized validation error with the 'invalid_login' message
        and code, including the email field label in lowercase as a parameter
        for error message formatting.

        Returns:
            ValidationError: A validation error object with the invalid login
                            message, code, and email field label parameter.
        """
        return ValidationError(
            self.error_messages["invalid_login"],
            code="invalid_login",
            params={
                "email": self.email_field.label.lower()
                if self.email_field.label
                else "email",
            },
        )
