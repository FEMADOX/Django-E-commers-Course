import hashlib

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect
from django.views.generic import CreateView, TemplateView, UpdateView

from account.backends import AccountBackend
from account.forms import ClientForm
from account.models import Client
from cart.views import HttpResponse
from payment.views import HttpResponseRedirect


class UserAccountView(LoginRequiredMixin, TemplateView):
    template_name = "account/account.html"
    login_url = "/account/login/"

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

        context["client_form"] = ClientForm(client_data)
        return context


# noinspection PyTypeHints
class UserUpdateAccountView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "account/account.html"
    success_url = "/account/"
    login_url = "/account/login/"

    def get_object(self, queryset: QuerySet[Client] | None = None) -> Client:
        client, _ = Client.objects.get_or_create(user=self.request.user)
        return client

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.success(self.request, "The data has been updated.")
        return super().form_valid(form)

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(self.request, message=str(form.errors))
        return super().form_invalid(form)


class UserCreateAccountView(CreateView):
    model = User
    fields = ["email", "password"]
    template_name = "account/signup.html"
    success_url = "/account/"

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
            AccountBackend().send_mail(self.request, user_email)
            messages.success(self.request, "We have sent an email to your address")
            return redirect("account:email_validation")

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        messages.error(self.request, message=str(form.errors))
        return super().form_invalid(form)


# def create_user(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
#     if request.method == "POST":
#         user_email = request.POST["new_user_email"]
#         user_name = user_email.split("@")[0].lower()
#         password_data = request.POST["new_user_password"]
#
#         try:
#             user = User.objects.get(
#                 email=user_email,
#             )
#             if user.check_password(password_data):
#                 login(request, user)
#                 return redirect("account:update_account")
#             message = "The account password isn't valid."
#             return render(request, "account/signup.html", {"message": message})
#
#         except User.DoesNotExist:
#             request.session["pending_registration"] = {
#                 "username": user_name,
#                 "email": user_email,
#                 "password": password_data,
#             }
#             AccountBackend().send_mail(request, user_email)
#             messages.success(request, "We have sent an email to your address")
#
#     return render(request, "account/signup.html")


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


def my_login(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    message = ""
    destiny_page = request.GET.get("next", None)

    if request.method == "POST":
        user_email = request.POST["email"]
        user_password = request.POST["password"]
        data_destiny = request.POST["next"]

        user = AccountBackend().authenticate(
            request,
            email=user_email,
            password=user_password,
        )

        if user:
            login(request, user)

            if data_destiny != "None":
                return redirect(data_destiny)

            return redirect("/")
        message = "The credentials aren't valid."

    return render(
        request,
        "account/login.html",
        {
            "message": message,
            "destiny": destiny_page,
        },
    )


def logout_user(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    if request.method == "POST":
        logout(request)
        return redirect("/account/login/")

    return render(request, "web/includes/catalog.html")


@method_decorator(csrf_protect, "dispatch")
class EmailValidationView(TemplateView):
    template_name = "account/email_validation.html"

    def post(self, request: HttpRequest) -> HttpResponse:
        if (
            not request.session.get("pending_registration")
            or request.session["pending_registration"].get("email") is None
        ):
            messages.error(request, "Please start the registration process.")
            return redirect("account:signup")
        email = request.session["pending_registration"]["email"]
        AccountBackend().send_mail(request, email)
        messages.success(
            request,
            "Email re-sent successfully. Please check your inbox.",
        )
        return render(request, self.template_name)
