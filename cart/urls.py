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
    path(
        "restore_cart/<int:order_pending_id>",
        views.restore_order_pending_cart,
        name="restore_order_pending_cart",
    ),
    path("clear-cart/", views.clear_cart, name="clear_cart"),
]
