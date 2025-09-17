from django.urls import path

from order.views import ConfirmOrderView, CreateOrderView, OrderSummaryView

app_name = "order"

urlpatterns = [
    path(
        "creating-order/",
        CreateOrderView.as_view(),
        name="create_order",
    ),
    path(
        "confirm-order/",
        ConfirmOrderView.as_view(),
        name="confirm_order",
    ),
    path(
        "order_summary/<int:order_id>",
        OrderSummaryView.as_view(),
        name="order_summary",
    ),
]
