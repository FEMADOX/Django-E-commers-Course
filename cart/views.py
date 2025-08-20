from typing import TYPE_CHECKING, cast

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from cart.cart import Cart
from order.models import Order
from web.models import Product

if TYPE_CHECKING:
    from common.web.stubs import StubsProduct


def cart(request: HttpRequest) -> HttpResponse:
    pending_orders = Order.objects.filter(client=request.user.pk, status="0")

    return render(request, "cart.html", {"pending_orders": pending_orders})


@login_required(login_url="/account/login/")
def add_product_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    quantity = int(request.POST["quantity"]) if request.method == "POST" else 1

    product = cast("StubsProduct", Product.objects.get(id=product_id))
    cart = Cart(request)
    cart.add(product, quantity)

    if request.method == "GET":
        return redirect("/")

    return render(request, "cart.html")


def delete_product_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    product = cast("StubsProduct", Product.objects.get(id=product_id))
    cart = Cart(request)
    cart.delete(product)

    return render(request, "cart.html")


def clear_cart(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)
    cart.clear()

    return render(request, "cart.html")


def restore_order_pending_cart(
    request: HttpRequest,
    order_pending_id: int,
) -> HttpResponse:
    cart = Cart(request)
    cart.restore_order_prending(order_pending_id)

    return render(request, "cart.html")
