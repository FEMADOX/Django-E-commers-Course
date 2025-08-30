import hashlib

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AbstractBaseUser, User
from django.contrib.auth.views import (
    LoginView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.forms import Form
from django.forms.models import BaseModelForm
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, TemplateView, UpdateView

from account.emails import send_account_activation_email, send_password_reset_email
from account.forms import (
    ClientForm,
    CustomAuthenticationForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
)
from account.models import Client
from cart.views import HttpResponse
from payment.views import HttpResponseRedirect


class UserAccountView(LoginRequiredMixin, TemplateView):
    template_name = "account/account.html"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)
        user = User.objects.get(pk=self.request.user.pk)

        try:
            client = Client.objects.get(user=user)
            client_data = {
                "name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "dni": client.dni,
                "sex": client.sex,
                "phone": client.phone,
                "birth": client.birth,
                "address": client.address,
            }
        except Client.DoesNotExist:
            client_data = {
                "name": user.username,
                "email": user.email,
            }

        context["form"] = ClientForm(client_data)
        return context


# noinspection PyTypeHints
class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "account/account.html"
    success_url = "/account/"

    def get_object(self, queryset: QuerySet[Client] | None = None) -> Client:
        client, _ = Client.objects.get_or_create(user=self.request.user)
        return client

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.success(self.request, "The data has been updated.")
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(self.request, message=str(form.errors))
        return super().form_invalid(form)


class UserSignupView(CreateView):
    model = User
    fields = ["email", "password"]
    template_name = "account/signup.html"
    success_url = "/account/"
    # form_class = CustomSignupForm

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        user_email = form.cleaned_data["email"]
        user_name = user_email.split("@")[0]
        password_data = form.cleaned_data["password"]

        try:
            user = User.objects.get(email=user_email, username=user_name)

            if not user.check_password(password_data):
                messages.error(self.request, "The account password isn't valid.")
                return super().form_invalid(form)

            login(self.request, user)
            messages.info(
                self.request,
                "The account already exists. You have been logged in.",
            )
            return super().form_valid(form)

        except User.DoesNotExist:
            self.request.session["pending_registration"] = {
                "username": user_name,
                "email": user_email,
                "password": password_data,
            }
            send_account_activation_email(self.request, user_email)
            messages.success(self.request, "We have sent an email to your address")
            return redirect("account:email_validation")

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(self.request, message=str(form.errors))
        return super().form_invalid(form)


def account_activation(
    request: HttpRequest,
    uidb64: str,
    token: str,
) -> HttpResponseRedirect:
    try:
        email = force_str(urlsafe_base64_decode(uidb64))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist, ValidationError):
        email = None

    if not email:
        messages.error(request, "Activation link is invalid! (Invalid Email)")
        return redirect("account:login")

    expected_token = hashlib.sha256(email.encode()).hexdigest()
    if token != expected_token:
        messages.error(request, "Activation link is invalid!")
        return redirect("account:login")

    pending_registration = request.session.get("pending_registration")
    if not pending_registration or pending_registration["email"] != email:
        messages.error(
            request,
            "Activation link is invalid! (Pending Registration)",
        )
        return redirect("account:login")

    user, created = User.objects.get_or_create(
        username=pending_registration.get("username"),
        email=pending_registration.get("email"),
        is_active=True,
    )
    if created:
        user.set_password(pending_registration.get("password"))
        user.save()
    del request.session["pending_registration"]
    login(request, user, "django.contrib.auth.backends.ModelBackend")
    messages.success(request, "Account activated successfully!")
    return redirect("account:user_account")


class UserLoginView(LoginView):
    template_name = "account/login.html"
    redirect_authenticated_user = True
    form_class: type[Form] = CustomAuthenticationForm  # type: ignore

    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        messages.success(self.request, "Login successfully!")
        return super().form_valid(form)

    def form_invalid(self, form: AuthenticationForm) -> HttpResponse:
        messages.error(self.request, "Login failed!")
        return super().form_invalid(form)


def logout_user(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    if request.method == "POST":
        logout(request)
        return redirect("/account/login/")

    return render(request, "web/includes/catalog.html")


@method_decorator(csrf_protect, "dispatch")
class EmailValidationView(TemplateView):
    template_name = "account/activation/account_activation.html"

    def post(self, request: HttpRequest) -> HttpResponse:
        if (
            not request.session.get("pending_registration")
            or request.session["pending_registration"].get("email") is None
        ):
            messages.error(request, "Please start the registration process.")
            return redirect("account:signup")
        email = request.session["pending_registration"]["email"]
        send_account_activation_email(request, email)
        messages.success(
            request,
            "Email re-sent successfully. Please check your inbox.",
        )
        return render(request, self.template_name)


class CustomPasswordResetView(PasswordResetView):
    email_template_name = "account/password/reset_email.html"
    form_class = CustomPasswordResetForm
    template_name = "account/password/reset.html"
    success_url = "/account/password-reset/done/"

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> HttpResponse:
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

    def post(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> HttpResponse:
        form = self.get_form()
        if request.session.get("password_reset_email"):
            del request.session["password_reset_email"]
        if form.is_valid():
            messages.success(self.request, "Password has been reset successfully.")
            return super().form_valid(form)
        messages.error(request, "Error resetting password. Please try again.")
        return super().form_invalid(form)
