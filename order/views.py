from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.shortcuts import render

from account.forms import ClientForm
from account.models import Client

# Create your views here.


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


@login_required(login_url="login/")
def confirm_order(request: HttpRequest):
    return render(request, "order.html")
