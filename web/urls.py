from django.urls import path

from web import views

app_name = "web"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "by-category/<int:category_id>",
        views.filter_by_category,
        name="filter_by_category",
    ),
    path(
        "by-name",
        views.search_product_title,
        name="search_product_title",
    ),
    path(
        "product/<int:product_id>",
        views.product_detail,
        name="product_detail",
    ),
]
