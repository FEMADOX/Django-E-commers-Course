from __future__ import annotations

import hashlib
import time
from typing import TYPE_CHECKING, Any

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AbstractBaseUser, User
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, TemplateView, UpdateView

from account.emails import send_account_activation_email, send_password_reset_email
from account.forms import (
    ClientForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    SmartAuthenticationForm,
)
from account.mixins import AnonymousRequiredMixin
from account.models import Client
from common.views.client import get_or_create_client_form

if TYPE_CHECKING:
    from django.contrib.auth.forms import AuthenticationForm
    from django.db.models import QuerySet
    from django.forms import Form
    from django.forms.models import BaseModelForm
    from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
    from django.http.response import HttpResponseBase


class UserAccountView(LoginRequiredMixin, TemplateView):
    template_name = "account/account.html"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.request.user.pk)

        context["form"] = get_or_create_client_form(user)
        return context


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "account/account.html"
    success_url = "/account/"

    def get_object(self, queryset: QuerySet[Client] | None = None) -> Client:
        return get_object_or_404(Client, user=self.request.user)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form = self.get_form()
        super().form_valid(form)
        cleaned_data = form.cleaned_data

        user = User.objects.get(pk=self.request.user.pk)
        user.username = cleaned_data["name"]
        user.last_name = cleaned_data["last_name"]
        user.email = cleaned_data["email"]
        user.save()

        messages.success(self.request, "The data has been updated.")
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(self.request, "Update failed!")
        return super().form_invalid(form)


class UserSignupView(AnonymousRequiredMixin, CreateView):
    model = User
    template_name = "account/signup.html"
    success_url = "/account/"
    form_class = SmartAuthenticationForm

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["is_signup"] = True
        return kwargs

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        user_email = form.cleaned_data["email"]
        user_name = user_email.split("@")[0]
        password_data = form.cleaned_data["password"]

        self.request.session["pending_registration"] = {
            "username": user_name,
            "email": user_email,
            "password": password_data,
            "timestamp": int(time.time()),
        }
        send_account_activation_email(self.request, user_email)
        messages.success(self.request, "We have sent an email to your address")
        return redirect("account:email_validation")

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(self.request, "SignUp Failed!")
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> HttpResponse:
        messages.success(request, "You have been logged out successfully.")
        return super().post(request)


class AccountActivationView(View):
    http_method_names = ["get"]
    backend = "django.contrib.auth.backends.ModelBackend"
    success_url = "account:user_account"
    failed_url = "account:login"
    token_expiration = 24 * 60 * 60

    def get_pending_registration(self) -> dict[str, str] | None:
        return self.request.session.get("pending_registration")

    def get(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        validation = self._validate_activation_data(uidb64, token)
        if not validation["valid"] and isinstance(validation["details"], str):
            return self._error_response(validation["details"])

        pending_registration = validation["pending_data"]
        if not isinstance(pending_registration, dict):
            return self._error_response("Invalid Pending Data")

        user = self._create_user(pending_registration)

        del request.session["pending_registration"]
        login(request, user, self.backend)

        messages.success(request, "Account activated successfully!")
        return redirect(self.success_url)

    def _error_response(
        self,
        detail: str | None = None,
    ) -> HttpResponse:
        if detail:
            detail = f"({detail})"
        messages.error(self.request, f"Activation link is invalid! {detail}")
        return redirect(self.failed_url)

    def _validate_activation_data(  # noqa: PLR0911
        self,
        uidb64: str,
        token: str,
    ) -> dict[str, bool | str | dict[str, str]]:
        result: dict[str, bool | str | dict[str, str]] = {"valid": False, "details": ""}

        # Email Validation
        email = self._decode_email(uidb64)
        if not email:
            result["details"] = "Invalid Email"
            return result

        # Pending Registration Validation
        pending_registration = self.get_pending_registration()
        if not pending_registration:
            result["details"] = "Pending Registration Not Found"
            return result

        # Token Validation
        if not self._validate_token(email, token):
            result["details"] = "Token Mismatch"
            return result

        # Validate email consistency
        if pending_registration.get("email") != email:
            result["details"] = "Pending Registration Email Mismatch"
            return result

        # Validate expiration
        timestamp = pending_registration.get("timestamp")
        if not timestamp:
            result["details"] = "Pending Registration Timestamp Not Found"
            return result

        current_time = int(time.time())
        if current_time - int(timestamp) > self.token_expiration:
            result["details"] = "Activation link has expired"
            return result

        # Setting result
        result["valid"] = True
        result["email"] = email
        result["pending_data"] = pending_registration
        return result

    def _validate_token(self, email: str, token: str) -> bool:
        pending_registration = self.get_pending_registration()
        if not pending_registration:
            return False

        timestamp = pending_registration.get("timestamp")
        if timestamp:
            current_time = int(time.time())
            if current_time - int(timestamp) > self.token_expiration:
                return False

        return token == hashlib.sha256(email.encode()).hexdigest()

    @staticmethod
    def _create_user(pending_data: dict[str, str]) -> User:
        user = User.objects.create_user(
            username=pending_data["username"],
            email=pending_data["email"],
            password=pending_data["password"],
            is_active=True,
        )
        Client.objects.create(user=user)
        return user

    @staticmethod
    def _decode_email(uidb64: str) -> str | None:
        try:
            return force_str(urlsafe_base64_decode(uidb64))
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            ValidationError,
        ):
            return None


class UserLoginView(LoginView):
    template_name = "account/login.html"
    redirect_authenticated_user = True
    form_class: type[Form] = SmartAuthenticationForm  # type: ignore

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["is_signup"] = False
        return kwargs

    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        messages.success(self.request, "Login successfully!")
        return super().form_valid(form)

    def form_invalid(self, form: AuthenticationForm) -> HttpResponse:
        messages.error(self.request, "Login failed!")
        return super().form_invalid(form)


@method_decorator(csrf_protect, "dispatch")
class EmailActivationView(TemplateView):
    template_name = "account/activation/account_activation.html"

    def post(self, request: HttpRequest) -> HttpResponse:
        pending_registration = request.session.get("pending_registration")
        if not pending_registration or not pending_registration.get("email"):
            messages.error(request, "Please start the registration process.")
            return redirect("account:signup")

        email = pending_registration.get("email")

        # If timestamp difference is less than 1 minute, do not resend
        current_time = int(time.time())
        timestamp = pending_registration.get("timestamp")
        time_to_wait = 60  # seconds
        if timestamp and current_time - int(timestamp) < time_to_wait:
            messages.error(request, "Please wait before requesting another email.")
            return render(request, self.template_name or "")

        send_account_activation_email(request, email)
        messages.success(
            request,
            "Email re-sent successfully. Please check your inbox.",
        )
        return render(request, self.template_name or "")


class CustomPasswordResetView(PasswordResetView):
    email_template_name = "account/password/reset_email.html"
    form_class = CustomPasswordResetForm
    template_name = "account/password/reset.html"
    success_url = "/account/password-reset/done/"

    def post(self, request: HttpRequest, *args: str, **kwargs: dict) -> HttpResponse:
        form = self.get_form()

        if form.is_valid():
            try:
                _ = get_user_model().objects.get(email=form.cleaned_data["email"])
            except get_user_model().DoesNotExist:
                messages.error(request, "No user found with this email address.")
                return super().form_invalid(form)
            request.session["password_reset_email"] = form.cleaned_data["email"]
            return super().form_valid(form)
        return super().form_invalid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "account/password/reset_done.html"

    def post(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> HttpResponseRedirect | HttpResponse:
        if "password_reset_email" not in request.session:
            messages.error(request, "Please initiate the password reset process.")
            return redirect("account:password_reset")
        send_password_reset_email(
            self.request,
            email=request.session["password_reset_email"],
        )
        return super().get(request, *args, **kwargs)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "account/password/reset_confirm.html"
    success_url = "/account/login/"
    form_class = CustomSetPasswordForm

    def dispatch(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> HttpResponseBase:
        if "uidb64" not in kwargs or "token" not in kwargs:
            msg = "The URL path must contain 'uidb64' and 'token' parameters."
            raise ImproperlyConfigured(msg)

        uidb64 = kwargs["uidb64"]
        token = kwargs["token"]

        user = self.get_user(uidb64 if isinstance(uidb64, str) else "")
        if not user:
            messages.error(
                request,
                "The password reset link is invalid (uidb64 invalid!).",
            )
            return redirect("account:login")

        if token != self.reset_url_token and not self.token_generator.check_token(
            user,
            token,
        ):
            messages.error(
                request,
                "The password reset link is invalid (token invalid!).",
            )
            return redirect("account:login")

        return super().dispatch(request, *args, **kwargs)

    def get_user(self, uidb64: str) -> AbstractBaseUser | None:
        user = get_user_model()
        try:
            email = force_str(urlsafe_base64_decode(uidb64))
            return user.objects.get(email=email)
        except (
            TypeError,
            ValueError,
            OverflowError,
            ValidationError,
            user.DoesNotExist,
        ):
            return None

    def post(self, request: HttpRequest, *args: str, **kwargs: dict) -> HttpResponse:
        form = self.get_form()
        if request.session.get("password_reset_email"):
            del request.session["password_reset_email"]
        if form.is_valid():
            messages.success(self.request, "Password has been reset successfully.")
            return super().form_valid(form)
        messages.error(request, "Error resetting password. Please try again.")
        return super().form_invalid(form)
