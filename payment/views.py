from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import stripe
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponsePermanentRedirect,
)
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from account.models import Client
from edshop import settings
from edshop.settings import STRIPE_API
from order.models import Order

if TYPE_CHECKING:
    from django.http import HttpRequest

    from cart.cart import Cart

# Create your views here.

stripe.api_key = STRIPE_API
logger = logging.getLogger(__name__)


class PaymentProcessView(LoginRequiredMixin, View):
    """Handle payment processing with Stripe checkout."""

    login_url = "/account/login/"

    def post(self, request: HttpRequest) -> HttpResponse:
        """Process payment and create Stripe checkout session."""

        session_data = self.order_preprocessing(request)

        if isinstance(session_data, (HttpResponseBadRequest, HttpResponseRedirect)):
            return session_data

        # Create STRIPE checkout session
        try:
            session = stripe.checkout.Session.create(**session_data)
            return redirect(
                session.url if session and session.url else reverse("web:index")
            )
        except Exception as e:
            msg = f"Unexpected error during checkout session creation: {e}"
            logger.exception(msg)
            return HttpResponseBadRequest(
                "An unexpected error occurred. Please try again later.",
            )

    @staticmethod
    def order_preprocessing(
            request: HttpRequest,
    ) -> HttpResponseBadRequest | HttpResponseRedirect | dict[str, Any]:
        """Perform any necessary preprocessing on the order before payment."""

        try:
            client = Client.objects.get(user=request.user)
            order_id = request.session.get("order_id")
            error_msg = None

            # Validate order data
            if not order_id:
                error_msg = "No order found in session"
                return HttpResponseBadRequest(error_msg)

            order = Order.objects.prefetch_related("order_details").get(pk=order_id)
            order_detail = order.order_details.all()
            if not order_detail.exists():
                error_msg = "Order has no items"
                return HttpResponseBadRequest(error_msg)

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
            return session_data
        except (Client.DoesNotExist, Order.DoesNotExist) as e:
            return HttpResponseBadRequest(f"Error: {e}")
        except KeyError:
            # Handle session key errors
            return HttpResponseBadRequest("Invalid session data")
        except (ValueError, TypeError):
            # Handle other specific errors
            return redirect("/")  # type: ignore


class PaymentCompletedView(LoginRequiredMixin, View):
    """Handle completed payment processing."""

    login_url = "/account/login/"

    def get(self, request: HttpRequest) -> HttpResponseRedirect | HttpResponse:
        """Process completed payment and send confirmation email."""

        if not request.session.get("order_id"):
            return HttpResponseNotFound()

        try:
            client = Client.objects.get(user=request.user)
            order_id = request.session.pop("order_id", "")
            order = Order.objects.prefetch_related("order_details").get(pk=order_id)
            order_cart: Cart | None = request.session.get("cart")

            # Changing the status of the order
            order.status = "1"  # PAID
            order.save()
            order_cart.clear() if order_cart else None

            order_details = order.order_details.all()
            order_details_products = [
                order_detail.product.title for order_detail in order.order_details.all()
            ]

            # Sending Mail
            self._send_confirmation_email(
                order=order,
                client=client,
                order_details_products=order_details_products,
            )

            return render(
                request,
                "payment/payment-completed.html",
                {"order": order, "order_details": order_details, "client": client},
            )

        except (Client.DoesNotExist, Order.DoesNotExist):
            # Clean up session and redirect to home
            request.session.pop("order_id", None)
            return redirect(reverse("web:index"))

    @staticmethod
    def _send_confirmation_email(
            order: Order,
            client: Client,
            order_details_products: list[str],
    ) -> bool:
        """
        Send order confirmation email.

        :param order: Description
        :type order: Order
        :param client: Description
        :type client: Client
        :param order_details_products: Description
        :type order_details_products: list[str]

        Returns:
            bool: True if email was sent successfully, False otherwise
        """

        try:
            send_mail(
                subject="Thanks for your purchase",
                message=(
                    f"Thanks for your purchase {client.user.first_name}\n"  # type: ignore
                    f"Your order was completed successfully\n"
                    f"Your order num is {order.order_num}\n"
                    f"Order products: {', '.join(order_details_products)}\n"
                    f"Total Price {order.total_price}\n"
                ),
                from_email=str(settings.EMAIL_HOST_USER),
                recipient_list=[order.client.user.email],  # type: ignore
                fail_silently=False,
            )
            logger.info(f"Confirmation email sent for order {order.order_num}")
            return True
        except Exception as e:
            msg = f"Failed to send confirmation email for order {order.order_num}: {e}"
            logger.exception(msg)
            return False


class PaymentCanceledView(LoginRequiredMixin, View):
    """Handle canceled payment."""

    login_url = "/account/login/"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Redirect to order confirmation page on payment cancellation."""
        if not request.session.get("order_id"):
            return HttpResponseNotFound()

        request.session.pop("order_id", None)

        messages.warning(request, "Payment was canceled.")

        return redirect("order:create_order")
