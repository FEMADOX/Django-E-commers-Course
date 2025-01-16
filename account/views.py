from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpRequest
from django.shortcuts import redirect, render

from account.forms import ClientForm
from account.models import Client

# Create your views here.


@login_required(login_url="login/")
def user_account(request: HttpRequest):
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
            "email": user.email
        }

    client_form = ClientForm(client_data)

    return render(
        request,
        "account.html",
        {"client_form": client_form},
    )


@login_required(login_url="login/")
def update_account(request: HttpRequest):
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


def create_user(request: HttpRequest):

    if request.method == "POST":
        username = request.POST["new_user_email"].split("@")[0].lower()
        user_email = request.POST["new_user_email"]
        password_data = request.POST["new_user_password"]

        try:
            new_user = User.objects.create_user(
                username=username, email=user_email, password=password_data
            )
            login(request, new_user)
            return redirect("/account/")
        except IntegrityError:
            raise IntegrityError("A user with that email already exists.")
        except Exception as e:
            raise Exception(str(e))

        # if new_user is not None:
        #     login(request, new_user)
        #     return redirect("/account/")

    return render(request, "signup.html")


def login_user(request: HttpRequest):
    message = ""
    destiny_page = request.GET.get("next", None)

    if request.method == "POST":
        user_name = request.POST["email"].split("@")[0].lower()
        user_password = request.POST["password"]
        data_destiny = request.POST["next"]

        user = authenticate(
            request,
            username=user_name,
            password=user_password
        )

        if user is not None:
            login(request, user)

            if data_destiny != "None":
                return redirect(data_destiny)

            return redirect("/account/")
        else:
            message = "The credencials aren't valid"

    return render(
        request,
        "login.html",
        {
            "message": message,
            "destiny": destiny_page,
        },
    )


def logout_user(request: HttpRequest):

    if request.method == "POST":
        logout(request)
        return redirect("login/")

    return render(request, "catalog.html")


@login_required(login_url="login/")
def create_order(request: HttpRequest):
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
            "email": user.email
        }

    client_form = ClientForm(client_data)

    return render(
        request,
        "order.html",
        {
            "client_form": client_form,
        }
    )
