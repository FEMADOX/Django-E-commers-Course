from django.urls import path

from order.views import (
    ConfirmOrderView,
    CreateOrderView,
    DeletePendingOrderView,
    OrderSummaryView,
)

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
        "delete-pending-order/<int:order_id>",
        DeletePendingOrderView.as_view(),
        name="delete_pending_order",
    ),
    path(
        "order-summary/<int:order_id>",
        OrderSummaryView.as_view(),
        name="order_summary",
    ),
]
