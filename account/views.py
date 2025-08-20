import hashlib

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from account.backends import AccountBackend
from account.forms import ClientForm
from account.models import Client
from cart.views import HttpResponse
from payment.views import HttpResponseRedirect

# Create your views here.


@login_required(login_url="/account/login/")
def user_account(request: HttpRequest) -> HttpResponse:
    user = User.objects.get(pk=request.user.pk)

    try:
        client = Client.objects.get(user=user)
        client_data = {
            "name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "dni": client.dni,
            "sex": client.sex,
            "address": client.address,
            "phone": client.phone,
            "birth": client.birth,
        }
    except Client.DoesNotExist:
        client_data = {
            "name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }

    client_form = ClientForm(client_data)

    return render(
        request,
        "account.html",
        {"client_form": client_form},
    )


@login_required(login_url="/account/login/")
def update_account(request: HttpRequest) -> HttpResponse:
    message = ""
    client_form = ClientForm()

    if request.method == "POST":
        client_form = ClientForm(request.POST)

        if client_form.is_valid():
            client_data = client_form.cleaned_data
            user = User.objects.get(pk=request.user.pk)

            user.first_name = client_data["name"]
            user.last_name = client_data["last_name"]
            user.email = client_data["email"]
            user.save()

            try:
                client = Client.objects.get(user=user)
                client.dni = client_data["dni"]
                client.sex = client_data["sex"]
                client.phone = client_data["phone"]
                client.birth = client_data["birth"]
                client.address = client_data["address"]
                client.save()
            except Client.DoesNotExist:
                client = Client(
                    user=user,
                    dni=client_data["dni"],
                    sex=client_data["sex"],
                    phone=client_data["phone"],
                    birth=client_data["birth"],
                    address=client_data["address"],
                )
                client.save()

            message = "The data has been updated."
        else:
            message = "The data hasn't been updated, "
            "because the formulary wasn't valid."

    return render(
        request,
        "account.html",
        {
            "client_form": client_form,
            "message": message,
        },
    )


def create_user(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    if request.method == "POST":
        user_email = request.POST["new_user_email"]
        user_name = user_email.split("@")[0].lower()
        password_data = request.POST["new_user_password"]

        try:
            user = User.objects.get(
                email=user_email,
            )
            if user.check_password(password_data):
                login(request, user)
                # return redirect(reverse("account:update_account"))
                return redirect("account:update_account")
            message = "The account password isn't valid."
            return render(request, "signup.html", {"message": message})

        except User.DoesNotExist:
            request.session["pending_registration"] = {
                "username": user_name,
                "email": user_email,
                "password": password_data,
            }
            AccountBackend().send_mail(request, user_email)
            messages.success(request, "We have sent an email to your address")

    return render(request, "signup.html")


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
        return redirect("account:login_user")

    expected_token = hashlib.sha256(email.encode()).hexdigest()
    if token != expected_token:
        messages.error(request, "Activation link is invalid!")
        return redirect("account:login_user")

    pending_registration = request.session.get("pending_registration")
    if not pending_registration or pending_registration["email"] != email:
        messages.error(
            request,
            "Activation link is invalid! (Pending Registration)",
        )
        return redirect("account:login_user")

    user = User.objects.create_user(
        username=pending_registration.get("username"),
        email=pending_registration.get("email"),
        is_active=True,
    )
    user.set_password(pending_registration.get("password"))
    user.save()
    login(request, user, "django.contrib.auth.backends.ModelBackend")
    # messages.success(request, "Account activated successfully!")
    return redirect("account:update_account")


def login_user(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
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
        "login.html",
        {
            "message": message,
            "destiny": destiny_page,
        },
    )


def logout_user(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    if request.method == "POST":
        logout(request)
        return redirect("/account/login/")

    return render(request, "catalog.html")
