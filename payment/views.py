from decimal import Decimal

import stripe
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse

from account.models import Client
from edshop.settings import STRIPE_API
from order.models import Order, OrderDetail

# # Create your views here.

stripe.api_key = STRIPE_API


@login_required(login_url="login/")
def payment_process(request: HttpRequest):
    client = Client.objects.get(user=request.user)
    order = Order.objects.get(client=client)
    order_detail = OrderDetail.objects.get(order=order)

    if request.method == "POST":
        success_url = request.build_absolute_uri(
            reverse("payment:completed")
        )
        cancel_url = request.build_absolute_uri(
            reverse("payment:canceled")
        )

        # STRIPE checkout session data
        session_data = {
            "mode": "payment",
            "client_reference_id": order.order_num,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": [],
        }

        # Add order items to the STRIPE checkout session
        for item in order_detail.objects.all():
            session_data["line_items"].append(
                {
                    "price_data": {
                        "unit_amount": Decimal(
                            item.product.price * Decimal("100")
                        ),
                        "currency": "usd",
                        "product_data": {
                            "name": item.product.title,
                        }
                    },
                    "quantity": item.quantity,
                }
            )

        # Create STRIPE checkout session
        session = stripe.checkout.Session.create(**session_data)

        return redirect(session.url if session and session.url else "/")

    return render(request, "payment.html", locals())
