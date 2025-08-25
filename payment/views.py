from typing import TYPE_CHECKING, Any, cast

import stripe
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpRequest
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from account.models import Client
from cart.views import HttpResponse
from edshop import settings
from edshop.settings import STRIPE_API
from order.models import Order, OrderDetail

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from common.order.stubs import StubsClient, StubsOrder, StubsOrderDetail

# # Create your views here.

stripe.api_key = STRIPE_API


@login_required(login_url="/account/login/")
def payment_process(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    client = cast("StubsClient", Client.objects.get(user=request.user))
    order_id = request.session["order_id"]
    order = cast("StubsOrder", Order.objects.get(pk=order_id))
    order_detail = cast(
        "QuerySet[StubsOrderDetail]",
        OrderDetail.objects.filter(order=order),
    )

    if request.method == "POST":
        success_url = request.build_absolute_uri(
            reverse("payment:payment_completed"),
        )
        cancel_url = request.build_absolute_uri(
            reverse("payment:payment_canceled"),
        )

        # STRIPE checkout session data
        session_data: dict[str, Any] = {
            "mode": "payment",
            "client_reference_id": order.order_num,
            "customer_email": client.user.email,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items": [],
        }

        # Add order items to the STRIPE checkout session
        for item in order_detail:
            session_data["line_items"].append(
                {
                    "price_data": {
                        "unit_amount": int(
                            item.product.price * int("100"),
                        ),
                        "currency": "usd",
                        "product_data": {
                            "name": item.product.title,
                        },
                    },
                    "quantity": item.quantity,
                },
            )

        # Create STRIPE checkout session
        session = stripe.checkout.Session.create(**session_data)

        return redirect(session.url if session and session.url else "/")

    return render(request, "order/shipping.html")


@login_required(login_url="/account/login/")
def payment_completed(request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
    if request.session.get("order_id"):
        client = cast("StubsClient", Client.objects.get(user=request.user))
        order_id = request.session.pop("order_id", "")
        order = cast("StubsOrder", Order.objects.get(pk=order_id))

        # Changing the status of the order
        order.status = "1"  # PAID
        order.save()

        order_details_products = [
            order_detail.product.title for order_detail in order.order_details.all()
        ]

        # Sending Mail
        send_mail(
            subject="Thanks for your bough",
            message=(
                f"Thanks for your bough {client.user.first_name}\n"
                f"Your order was completed successfully\n"
                f"Your order num is {order.order_num}\n"
                f"Order products: {', '.join(order_details_products)}\n"
                f"Total Price {order.total_price}\n"
            ),
            from_email=str(settings.EMAIL_HOST_USER),
            recipient_list=[order.client.user.email],
            fail_silently=False,
        )
    else:
        return redirect(reverse("web:index"))

    return render(request, "payment/payment_completed.html", {"order": order})


@login_required(login_url="/account/login/")
def payment_canceled(request: HttpRequest) -> HttpResponse:
    return render(request, "payment/payment_canceled.html")
