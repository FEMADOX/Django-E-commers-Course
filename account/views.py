from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpRequest
from django.shortcuts import redirect, render

from account.backends import AccountBackend
from account.forms import ClientForm
from account.models import Client
from cart.views import HttpResponse
from payment.views import HttpResponseRedirect

# Create your views here.


@login_required(login_url="login/")
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


@login_required(login_url="login/")
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
                return redirect("/account/")
            message = "The account password isn't valid."
            return render(request, "signup.html", {"message": message})
        except User.DoesNotExist:
            new_user = User.objects.create_user(
                username=user_name,
                email=user_email,
            )
            new_user.set_password(password_data)
            new_user.save()
            login(request, new_user)
            return redirect("/account/")

        except IntegrityError as error:
            msg = "A user with that email already exists."
            raise IntegrityError(msg) from error

    return render(request, "signup.html")


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

            return redirect("/account/")
        message = "The credencials aren't valid."

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
        return redirect("login/")

    return render(request, "catalog.html")
