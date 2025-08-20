import datetime
from decimal import Decimal

from django.db.models import QuerySet

from common.account.stubs import StubsClient
from common.web.stubs import StubsProduct
from order.models import Order, OrderDetail


class StubsOrder(Order):
    STATUS_CHOICES = (
        ("0", "Pendings"),
        ("1", "Paid"),
    )
    client: StubsClient
    registration_date: datetime.datetime
    order_num: str
    total_price: Decimal
    status: str
    order_details: QuerySet[OrderDetail]


class StubsOrderDetail(OrderDetail):
    order: StubsOrder
    product: StubsProduct
    quantity: int
    total: float
