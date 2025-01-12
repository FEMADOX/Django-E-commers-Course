from decimal import Decimal
from django.http import HttpRequest

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

    def get_total_price(self):
        total = 0
        for _, value in self.cart.items():
            total += Decimal(value["subtotal"])
        return total

    def add(self, product: Product, quantity):

        if str(product.pk) not in self.cart.keys():
            self.cart[product.pk] = {
                "product_id": product.pk,
                "title": product.title,
                "price": str(product.price),
                "quantity": quantity,
                "category": product.category.name,
                "description": product.description,
                "image": product.image.url,
                "brand": product.brand,
                "weight": product.weight,
                "dimension": product.dimension,
                "color": product.color,
                "subtotal": str(quantity * product.price),
            }
        else:
            for key, value in self.cart.items():
                if key == str(product.pk):
                    value["quantity"] = str(int(value["quantity"]) + quantity)
                    value["subtotal"] = str(Decimal(value["price"])
                                            * int(value["quantity"]))
                    break

        self.save()

    def delete(self, product: Product):
        product_id = str(product.pk)
        if product_id in self.cart:
            del self.cart[product_id]

        self.save()

    def clear(self):
        self.session["cart"] = {}

    def save(self):
        self.session["cart"] = self.cart
        self.session["cart_total_price"] = str(self.get_total_price())
        self.session.modified = True
