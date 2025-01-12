from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.shortcuts import redirect, render

from web.cart import Cart
from web.models import Category, Product

# Create your views here.


def index(request: HttpRequest):
    products = Product.objects.all()
    categories = Category.objects.all()

    return render(
        request,
        "index.html",
        {
            "products": products,
            "categories": categories,
        },
    )


def filter_by_category(request: HttpRequest, category_id):
    categories = Category.objects.all()
    category = Category.objects.get(id=category_id)
    # products = category.product_set.all()
    products = Product.objects.filter(category=category)

    return render(
        request,
        "index.html",
        {
            "products": products,
            "categories": categories,
        },
    )


def search_product_title(request: HttpRequest):

    if request.method == "POST":
        product_title = request.POST["title"]
        categories = Category.objects.all()
        products = Product.objects.filter(title__contains=product_title)

        return render(
            request,
            "index.html",
            {
                "products": products,
                "categories": categories,
            },
        )
    return render(request, "index.html")


def product_detail(request: HttpRequest, product_id):
    product = Product.objects.get(id=product_id)

    return render(request, "producto.html", {"product": product})


""" CART VIEWS """


def cart(request: HttpRequest):
    # obj_cart = Cart(request)
    # print(obj_cart.cart.get("8").get("category"))
    return render(request, "carrito.html")


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

    return render(request, "carrito.html")


def delete_product_cart(request: HttpRequest, product_id):
    product = Product.objects.get(id=product_id)
    cart = Cart(request)
    cart.delete(product)

    return render(request, "carrito.html")


def clear_cart(request: HttpRequest):
    cart = Cart(request)
    cart.clear()

    return render(request, "carrito.html")


""" USER/CLIENT VIEWS """


def user_account(request: HttpRequest):
    return render(request, "cuenta.html")


def create_user(request: HttpRequest):

    if request.method == "POST":
        username = request.POST["new_user_gmail"].split("@")[0].capitalize()
        user_gmail = request.POST["new_user_gmail"]
        password_data = request.POST["new_user_password"]
        new_user = User.objects.create_user(
            username=username, email=user_gmail, password=password_data
        )

        if new_user is not None:
            login(request, new_user)
            return redirect("/account/")

    return render(request, "login.html")


def login_user(request: HttpRequest):
    return redirect("/account/")
