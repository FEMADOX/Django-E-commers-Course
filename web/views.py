from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render

from web.models import Brand, Category, Product


def index(request: HttpRequest) -> HttpResponse:
    products = Product.objects.all()
    categories = Category.objects.all()
    brands = Brand.objects.all()

    return render(
        request,
        "web/index.html",
        {
            "products": products,
            "categories": categories,
            "brands": brands,
        },
    )


def filter_by_category(request: HttpRequest, category_id: int) -> HttpResponse:
    categories = Category.objects.all()
    category = Category.objects.get(id=category_id)
    brands = Brand.objects.all()
    products = Product.objects.filter(category=category)

    return render(
        request,
        "web/index.html",
        {
            "products": products,
            "categories": categories,
            "brands": brands,
        },
    )


def filter_by_brand(request: HttpRequest, brand_id: int) -> HttpResponse:
    brands = Brand.objects.all()
    brand = Brand.objects.get(id=brand_id)
    categories = Category.objects.all()
    products = Product.objects.filter(brand=brand)

    return render(
        request,
        "web/index.html",
        {
            "products": products,
            "brands": brands,
            "categories": categories,
        },
    )


def search_product_title(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        product_title = request.POST["title"]
        categories = Category.objects.all()
        products = Product.objects.filter(title__contains=product_title)

        return render(
            request,
            "web/index.html",
            {
                "products": products,
                "categories": categories,
            },
        )
    return render(request, "web/index.html")


def product_detail(request: HttpRequest, product_id: int) -> HttpResponse:
    product = Product.objects.get(id=product_id)

    return render(request, "web/product.html", {"product": product})
