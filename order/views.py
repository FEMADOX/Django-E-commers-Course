from decimal import Decimal
from typing import Any, cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import (
    HttpResponse,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, TemplateView

from account.forms import ClientForm
from account.models import Client
from cart.cart import Cart
from common.views.client import get_or_create_client_form
from order.models import Order, OrderDetail
from web.models import Product

# Create your views here.

# ============================================================================
# ORIGINAL FBV CODE (COMMENTED OUT)
# ============================================================================

# @login_required(login_url="/account/login/")
# def create_order(request: HttpRequest) -> HttpResponse:
#     user = User.objects.get(pk=request.user.pk)
#
#     try:
#         client = Client.objects.get(user=user)
#         client_data = {
#             "name": user.first_name,
#             "last_name": user.last_name,
#             "email": user.email,
#             "dni": client.dni,
#             "sex": client.sex,
#             "address": client.address,
#             "phone": client.phone,
#             "birth": client.birth,
#         }
#     except Client.DoesNotExist:
#         client_data = {
#             "name": user.first_name,
#             "last_name": user.last_name,
#             "email": user.email,
#         }
#
#     client_form = ClientForm(client_data)
#
#     return render(
#         request,
#         "order/order.html",
#         {
#             "client_form": client_form,
#         },
#     )


# @login_required(login_url="/account/login/")
# def confirm_order(
#     request: HttpRequest,
# ) -> HttpResponse:
#     user = User.objects.get(pk=request.user.pk)
#
#     if request.method == "POST":
#         user.first_name = request.POST["name"]
#         user.last_name = request.POST["last_name"]
#         user.email = request.POST["email"]
#         user.save()
#
#         # Storing the data in the session
#         request.session["client_data"] = {
#             "phone": request.POST.get("phone", ""),
#             "address": request.POST.get("address", ""),
#         }
#     try:
#         client = Client.objects.get(user=user)
#         client.phone = request.session["client_data"].pop("phone", "")
#         client.address = request.session["client_data"].pop("address", "")
#         client.save()
#     except Client.DoesNotExist:
#         client = Client.objects.create(
#             user=user,
#             address=request.session["client_data"]["address"],
#             phone=request.session["client_data"]["phone"],
#         )
#
#     # Check the cart
#     order_cart: dict | Any = request.session.get("cart", None)
#     if not order_cart:
#         return redirect("cart:cart")
#
#     # ORDER
#     new_order = Order.objects.create(client=client)
#
#     # ORDER DETAIL
#     for value in order_cart.values():
#         cart_product = Product.objects.get(pk=value["product_id"])
#         order_detail, created = OrderDetail.objects.get_or_create(
#             order=new_order,
#             product=cart_product,
#             defaults={
#                 "quantity": int(value["quantity"]),
#                 "subtotal": Decimal(value["subtotal"]),
#             },
#         )
#         if not created:
#             order_detail.quantity = int(value["quantity"])
#             order_detail.subtotal = Decimal(value["subtotal"])
#             order_detail.save()
#
#     new_order.order_num = (
#         f"Order #{new_order.pk} - Date {new_order.registration_date.strftime('%Y')}"
#     )
#     new_order.total_price = Decimal(
#         request.session.pop("cart_total_price", "0.00"),
#     )
#     new_order.save()
#
#     # Cleaning the cart after the order is confirmed
#     order_cart.clear()
#
#     return redirect(reverse("order:order_summary", args=[new_order.pk]))


# @login_required(login_url="/account/login/")
# def order_summary(request: HttpRequest, order_id: int) -> HttpResponse:
#     order = Order.objects.get(pk=order_id)
#     request.session["order_id"] = order.pk
#     return render(request, "order/shipping.html", {"order": order})


# ============================================================================
# NEW CLASS-BASED VIEWS (CBV)
# ============================================================================


class CreateOrderView(LoginRequiredMixin, TemplateView):
    """
    Displays the order creation form with client data pre-populated.
    """

    template_name = "order/order.html"
    login_url = "/account/login/"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        user = cast("User", self.request.user)

        context["client_form"] = get_or_create_client_form(user)
        return context


class ConfirmOrderView(LoginRequiredMixin, FormView):
    """
    Processes the order confirmation and creates the order.
    """

    form_class = ClientForm
    login_url = "/account/login/"

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

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # Store order ID in session for later use
        self.request.session["order_id"] = self.object.pk
        return context
