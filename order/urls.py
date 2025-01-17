from django.urls import path

from order.views import confirm_order, create_order

app_name = "order"

urlpatterns = [
    path(
        "creating-order/",
        create_order,
        name="create_order",
    ),
    path(
        "confirm-order/",
        confirm_order,
        name="confirm_order",
    ),
]
