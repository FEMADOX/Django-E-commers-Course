from django.urls import path

# from cart import views
from cart.views import (
    AddProductCartView,
    CartIndexView,
    ClearCartView,
    DeleteProductCartView,
    RestoreOrderPendingCartView,
)

app_name = "cart"

urlpatterns = [
    path("", CartIndexView.as_view(), name="cart"),
    # path("", views.cart, name="cart"),
    path(
        "add-to-cart/<int:product_id>",
        AddProductCartView.as_view(),
        name="add_product_cart",
    ),
    path(
        "delete-from-cart/<int:product_id>",
        DeleteProductCartView.as_view(),
        name="delete_product_cart",
    ),
    path(
        "restore_cart/<int:order_pending_id>",
        RestoreOrderPendingCartView.as_view(),
        name="restore_order_pending_cart",
    ),
    path("clear-cart/", ClearCartView.as_view(), name="clear_cart"),
]
