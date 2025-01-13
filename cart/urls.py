from django.urls import path

from cart import views

app_name = "cart"

urlpatterns = [
    path("", views.cart, name="cart"),
    path(
        "add-to-cart/<int:product_id>",
        views.add_product_cart,
        name="add_product_cart",
    ),
    path(
        "delete-from-cart/<int:product_id>",
        views.delete_product_cart,
        name="delete_product_cart",
    ),
    path("clear-cart/", views.clear_cart, name="clear_cart"),
]
