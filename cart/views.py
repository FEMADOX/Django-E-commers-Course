from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render

from cart.cart import Cart
from web.models import Product

# Create your views here.


def cart(request: HttpRequest):
    return render(request, "cart.html")


@login_required(login_url="login-signup/")
def add_product_cart(request: HttpRequest, product_id):

    if request.method == "POST":
        quantity = int(request.POST["quantity"])
    else:
        quantity = 1

    product = Product.objects.get(id=product_id)
    cart = Cart(request)
    cart.add(product, quantity)

    if request.method == "GET":
        return redirect("/")

    return render(request, "cart.html")


def delete_product_cart(request: HttpRequest, product_id):
    product = Product.objects.get(id=product_id)
    cart = Cart(request)
    cart.delete(product)

    return render(request, "cart.html")


def clear_cart(request: HttpRequest):
    cart = Cart(request)
    cart.clear()

    return render(request, "cart.html")
