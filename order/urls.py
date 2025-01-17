from django.urls import path

from order.views import confirm_order, create_order, order_summary

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
    path(
        "order_summary/<int:order_id>",
        order_summary,
        name="order_summary",
    ),
]
