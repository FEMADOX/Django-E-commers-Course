import json
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, View

from cart.cart import Cart
from order.models import Order
from web.models import Product


class CartIndexView(TemplateView):
    template_name = "cart.html"

    def get_context_data(self, **kwargs: dict) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["pending_orders"] = Order.objects.filter(
            client=self.request.user.pk,
            status="0",
        )
        return context

    def get(
        self,
        request: HttpRequest,
        *args: tuple,
        **kwargs: dict,
    ) -> HttpResponse | HttpResponseRedirect:
        cart = Cart(request)

        if not cart.cart:
            return redirect("/")

        return super().get(request, *args, **kwargs)


class AddProductCartView(LoginRequiredMixin, View):
    """View to add products to the cart"""

    http_method_names = ["post"]
    login_url = "/account/login/"

    @staticmethod
    def post(
        request: HttpRequest,
        product_id: int,
    ) -> HttpResponse:
        """Add product with specified quantity and show cart"""

        quantity = int(request.POST["quantity"])
        product = get_object_or_404(Product, id=product_id)
        cart = Cart(request)
        cart.add(product, quantity)  # type: ignore

        actual_location = request.POST.get("location-url")
        if actual_location:
            return redirect(actual_location)

        return redirect("/")


class DeleteProductCartView(LoginRequiredMixin, View):
    """View to remove products from the cart"""

    http_method_names = ["post"]
    login_url = "/account/login/"

    @staticmethod
    def post(
        request: HttpRequest,
        product_id: int,
    ) -> HttpResponse:
        cart = Cart(request)
        cart.delete(str(product_id))

        actual_location = request.POST.get("location-url")
        if actual_location:
            return redirect(actual_location)

        return redirect("/")


class UpdateProductCartView(LoginRequiredMixin, View):
    """View to update a product from the cart"""

    http_method_names = ["patch"]
    login_url = "/account/login/"

    @staticmethod
    def patch(
        request: HttpRequest,
        product_id: int,
    ) -> JsonResponse:
        try:
            data = json.loads(request.body)
            quantity = data.get("quantity")

            cart = Cart(request)
            cart.update(str(product_id), quantity)

            return JsonResponse(
                {
                    "subtotal": cart.get_order_product_subtotal(str(product_id)),
                    "total_price": cart.get_total_price(),
                    "message": "Product updated successfully",
                },
                status=200,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except ValueError as error:
            return JsonResponse(
                {"error": f"Invalid quantity: {error!s}"},
                status=400,
            )
        except Exception as error:  # noqa: BLE001
            return JsonResponse({"error": str(error)}, status=400)


class ClearCartView(LoginRequiredMixin, View):
    """View to clear the entire cart"""

    http_method_names = ["post"]
    login_url = "/account/login/"

    @staticmethod
    def post(
        request: HttpRequest,
    ) -> HttpResponse:
        cart = Cart(request)
        cart.clear()

        actual_location = request.POST.get("location-url")
        if actual_location:
            return redirect(actual_location)

        return redirect("/cart/")


class RestoreOrderPendingCartView(LoginRequiredMixin, View):
    """View to restore a pending order to the cart"""

    http_method_names = ["post"]
    login_url = "/account/login/"

    @staticmethod
    def post(
        request: HttpRequest,
        order_pending_id: int,
    ) -> HttpResponse:
        cart = Cart(request)
        cart.restore_order_pending(order_pending_id)
        actual_location = request.POST.get("location-url")

        if actual_location:
            return redirect(actual_location)

        return redirect("/cart/")
