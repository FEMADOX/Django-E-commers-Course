from __future__ import annotations

import json
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, TemplateView

from account.forms import ClientForm
from account.models import Client
from cart.cart import Cart
from common.views.client import get_or_create_client_form
from order.models import Order, OrderDetail
from tests.common.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from web.models import Product

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from django.db.models import QuerySet
    from django.http import HttpRequest, HttpResponse


# Create your views here.
class CreateOrderView(LoginRequiredMixin, TemplateView):
    """
    Displays the order creation form with client data pre-populated.

    Note: This view uses TemplateView and only renders the template with context.
    """

    http_method_names = ["get", "patch"]
    template_name = "order/order.html"
    login_url = "/account/login/"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = cast("User", self.request.user)

        context["client_form"] = get_or_create_client_form(user)
        return context

    def get(self, request: HttpRequest, **kwargs: dict) -> HttpResponse:
        cart = Cart(request)

        # If not products in cart redirect to catalog dashboard
        if not cart.cart:
            return redirect(reverse("web:index"))

        return super().get(request)


class ConfirmOrderView(LoginRequiredMixin, FormView):
    """
    Processes the order confirmation and creates the order.
    """

    form_class = ClientForm
    template_name = "order/order.html"  # For form errors
    login_url = "/account/login/"

    def get(self, request: HttpRequest, *args: tuple, **kwargs: dict) -> HttpResponse:
        """Redirect GET requests to create order page."""
        return redirect("order:create_order")

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        """Add additional context data for the template."""
        context = super().get_context_data(**kwargs)

        # Ensure the form is in context with the correct key
        if "form" in context:
            context["client_form"] = context["form"]

        return context

    def form_valid(self, form: ClientForm) -> HttpResponse:
        """Process valid form data and create order."""
        user = cast("User", self.request.user)

        # Update user data
        user.first_name = form.cleaned_data.get("name", "")
        user.last_name = form.cleaned_data.get("last_name", "")
        user.email = form.cleaned_data.get("email", "")
        user.save()

        # Store client data in session
        self.request.session["client_data"] = {
            "phone": form.cleaned_data.get("phone", ""),
            "address": form.cleaned_data.get("address", ""),
        }

        # Get or create client
        client = self._get_or_create_client(user)

        # Check cart
        order_cart = self.request.session.get("cart")
        if not order_cart:
            return redirect("cart:cart")

        # Create order
        new_order = self._create_order(client, order_cart)

        # Clean cart
        order_cart.clear()

        return redirect(reverse("order:order_summary", args=[new_order.pk]))

    def form_invalid(self, form: ClientForm) -> HttpResponse:
        """Handle invalid form data by re-rendering the order page with errors."""
        # Check if cart still exists
        cart = Cart(self.request)
        if not cart.cart:
            return redirect("web:index")

        # Return the form with errors and full context
        context = self.get_context_data()
        context["form"] = form
        return self.render_to_response(context)

    def _get_or_create_client(self, user: User) -> Client:
        """Get existing client or create new one with session data."""
        try:
            client = Client.objects.get(user=user)
            client.phone = self.request.session["client_data"].pop("phone", "")
            client.address = self.request.session["client_data"].pop("address", "")
            client.save()
            return client
        except Client.DoesNotExist:
            return Client.objects.create(
                user=user,
                address=self.request.session["client_data"]["address"],
                phone=self.request.session["client_data"]["phone"],
            )

    def _create_order(self, client: Client, order_cart: Cart) -> Order:
        """Create order and order details from cart data."""
        new_order = Order.objects.create(client=client)

        # Create | Get order details
        for product_pk, order_cart_detail in order_cart.items():
            try:
                product = Product.objects.get(pk=product_pk)
                quantity = int(order_cart_detail["quantity"])
                subtotal = Decimal(order_cart_detail["subtotal"])

                new_order_detail, created = OrderDetail.objects.get_or_create(
                    order=new_order,
                    product=product,
                    defaults={"quantity": quantity, "subtotal": subtotal},
                )
                if not created:
                    new_order_detail.quantity = quantity
                    new_order_detail.subtotal = subtotal
                    new_order_detail.save()
            except Product.DoesNotExist:
                # Skip products that don't exist in the database
                # This could happen if a product was deleted after being added to cart
                continue

        # Update order metadata
        new_order.order_num = (
            f"Order #{new_order.pk} - Date {new_order.registration_date.strftime('%Y')}"
        )
        new_order.total_price = Decimal(
            self.request.session.pop("cart_total_price", "0.00"),
        )
        new_order.save()

        return new_order


class OrderSummaryView(LoginRequiredMixin, DetailView):
    """
    Displays order summary and stores order ID in session.
    """

    model = Order
    template_name = "order/shipping.html"
    context_object_name = "order"
    pk_url_kwarg = "order_id"
    login_url = "/account/login/"

    def get_queryset(self) -> QuerySet[Order]:
        """Restrict queryset to only orders belonging to the current user."""
        return Order.objects.filter(client__user=self.request.user)

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Store order ID in session for later use
        self.request.session["order_id"] = self.object.pk
        return context
