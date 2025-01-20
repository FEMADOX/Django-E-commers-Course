from decimal import Decimal
from typing import Any
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse

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

        # Storing the data in the session
        request.session["client_data"] = {
            "phone": request.POST.get("phone", ""),
            "address": request.POST.get("address", ""),
        }
    try:
        client = Client.objects.get(user=user)
        client.phone = request.session["client_data"].pop("phone", "")
        client.address = request.session["client_data"].pop("address", "")
        client.save()
    except Client.DoesNotExist:
        client = Client.objects.create(
            user=user,
            address=request.session["client_data"]["address"],
            phone=request.session["client_data"]["phone"],
        )

    # Check the cart
    order_cart: dict | Any = request.session.get("cart", None)
    if not order_cart:
        return redirect("cart:cart")

    # ORDER
    new_order = Order.objects.create(client=client)

    # # Handle pending orders
    # pending_orders = (
    #     Order.objects
    #     .filter(client=client, status="0")
    #     .exclude(pk=new_order.pk)
    # )
    # for pending_order in pending_orders:
    #     order_details = OrderDetail.objects.filter(order=pending_order)
    #     for order_detail in order_details:
    #         order_same_product_order_pending = (
    #             OrderDetail.objects.filter(
    #                 order=pending_order,
    #                 product=order_detail.product
    #             )
    #         )
    #         if order_same_product_order_pending.count() > 1:
    #             order_detail.delete()
    #         order_detail.order = new_order
    #         order_detail.save()
    #     pending_order.delete()

    # ORDER DETAIL
    for value in order_cart.values():
        cart_product = Product.objects.get(pk=value["product_id"])
        order_detail, created = OrderDetail.objects.get_or_create(
            order=new_order,
            product=cart_product,
            defaults={
                "quantity": int(value["quantity"]),
                "subtotal": Decimal(value["subtotal"]),
            }
        )
        if not created:
            order_detail.quantity = int(value["quantity"])
            order_detail.subtotal = Decimal(value["subtotal"])
            order_detail.save()

    new_order.order_num = f"Order #{new_order.pk} - "\
        f"Date {new_order.registration_date.strftime('%Y')}"
    new_order.total_price = Decimal(
        request.session.pop("cart_total_price", "0.00")
    )
    new_order.save()

    # Cleaning the cart after the order is confirmed
    order_cart.clear()

    return redirect(reverse("order:order_summary", args=[new_order.pk]))
    # return render(request, "shipping.html", {"order": new_order})


@login_required(login_url="login/")
def order_summary(request: HttpRequest, order_id: int):
    order = Order.objects.get(pk=order_id)
    request.session["order_id"] = order.pk
    return render(request, "shipping.html", {"order": order})
