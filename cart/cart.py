from decimal import Decimal
from typing import Literal

from django.http import HttpRequest

from common.web.stubs import StubsProduct
from order.models import Order
from web.models import Product


class Cart:
    def __init__(self, request: HttpRequest) -> None:
        self.request = request
        self.session = request.session

        cart = self.session.get("cart")
        total_price = self.session.get("cart_total_price")

        if not cart:
            cart = self.session["cart"] = {}
            total_price = self.session["cart_total_price"] = "0.00"

        self.cart = cart
        self.total_price = total_price

    def get_total_price(self) -> Decimal | Literal[0]:
        total = 0
        for value in self.cart.values():
            total += Decimal(value["subtotal"])
        return total

    def add(self, product: StubsProduct, quantity: int) -> None:
        if str(product.pk) not in self.cart:
            self.cart[product.pk] = {
                "product_id": product.pk,
                "title": product.title,
                "price": str(product.price),
                "quantity": quantity,
                "category": {
                    "id": product.category.pk,
                    "name": product.category.name,
                },
                "description": product.description,
                "image": product.image.url,
                "brand": {
                    "id": product.brand.pk,
                    "name": product.brand.name,
                },
                "weight": product.weight,
                "dimension": product.dimension,
                "color": product.color,
                "subtotal": str(quantity * product.price),
            }
        else:
            for key, value in self.cart.items():
                if key == str(product.pk):
                    value["quantity"] = str(int(value["quantity"]) + quantity)
                    value["subtotal"] = str(
                        Decimal(value["price"]) * int(value["quantity"]),
                    )
                    break

        self.save()

    def delete(self, product: Product) -> None:
        product_id = str(product.pk)
        if product_id in self.cart:
            del self.cart[product_id]

        self.save()

    def clear(self) -> None:
        self.session["cart"] = {}

    def restore_order_prending(self, order_id: int) -> None:
        order = Order.objects.get(pk=order_id, status="0")
        for order_detail in order.order_details.all():  # type: ignore[attr-defined]
            self.add(order_detail.product, order_detail.quantity)

    def save(self) -> None:
        self.session["cart"] = self.cart
        self.session["cart_total_price"] = str(self.get_total_price())
        self.session.modified = True
