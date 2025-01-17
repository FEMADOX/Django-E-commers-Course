from django.http import HttpRequest
from django.shortcuts import render

from web.models import Brand, Category, Product

# Create your views here.


def index(request: HttpRequest):
    products = Product.objects.all()
    categories = Category.objects.all()
    brands = Brand.objects.all()

    return render(
        request,
        "index.html",
        {
            "products": products,
            "categories": categories,
            "brands": brands,
        },
    )


def filter_by_category(request: HttpRequest, category_id):
    categories = Category.objects.all()
    category = Category.objects.get(id=category_id)
    brands = Brand.objects.all()
    # products = category.product_set.all()
    products = Product.objects.filter(category=category)

    return render(
        request,
        "index.html",
        {
            "products": products,
            "categories": categories,
            "brands": brands,
        },
    )


def filter_by_brand(request: HttpRequest, brand_id):
    brands = Brand.objects.all()
    brand = Brand.objects.get(id=brand_id)
    categories = Category.objects.all()
    products = Product.objects.filter(brand=brand)

    return render(
        request,
        "index.html",
        {
            "products": products,
            "brands": brands,
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

    return render(request, "product.html", {"product": product})
