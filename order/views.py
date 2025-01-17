from decimal import Decimal
from typing import Any
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.shortcuts import render

from account.forms import ClientForm
from account.models import Client
from order.models import Order, OrderDetail
from web.models import Product

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
    user = User.objects.get(pk=request.user.pk)

    if request.method == "POST":
        user.first_name = request.POST["name"]
        user.last_name = request.POST["last_name"]
        user.email = request.POST["email"]
        user.save()
    try:
        client = Client.objects.get(user=user)
        client.phone = request.POST["phone"]
        client.address = request.POST["address"]
        client.save()
    except Client.DoesNotExist:
        client = Client.objects.create(
            user=user,
            address=request.POST["address"],
            phone=request.POST["phone"],
        )

    # ORDER
    new_order = Order()
    new_order.client = client
    new_order.save()

    # ORDER DETAIL
    order_cart: dict | Any = request.session.get("cart", None)

    for value in order_cart.values():
        order_product = Product.objects.get(pk=value["product_id"])
        order_detail = OrderDetail(
            order=new_order,
            product=order_product,
            quantity=int(value["quantity"]),
            subtotal=Decimal(value["subtotal"])
        )
        order_detail.save()

    order_num = f"Order #{new_order.pk} - "\
        f"Date {new_order.registration_date.strftime('%Y')}"
    total_price = Decimal(request.session["cart_total_price"])
    new_order.order_num = order_num
    new_order.total_price = total_price
    new_order.save()

    return render(request, "shipping.html", {"order": new_order})
