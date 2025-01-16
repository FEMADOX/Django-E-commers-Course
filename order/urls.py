from django.urls import path

from order.views import create_order

app_name = "order"

urlpatterns = [
    path(
        "creating-order/",
        create_order,
        name="create_order",
    ),
]
