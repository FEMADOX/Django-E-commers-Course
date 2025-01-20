from django.db import models

from account.models import Client
from web.models import Product

# Create your models here.


class Order(models.Model):

    STATUS_CHOICES = (
        ("0", "Pendings"),
        ("1", "Paid")
    )

    client = models.ForeignKey(Client, on_delete=models.RESTRICT)
    registration_date = models.DateTimeField(auto_now_add=True)
    order_num = models.CharField(max_length=20, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2,
                                      default=0)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES,
                              default="0")

    class Meta:
        ordering = ["-registration_date"]
        indexes = [
            models.Index(fields=["client", "registration_date", "status"])
        ]

    def __str__(self):
        return f"{self.client} - {self.order_num} - {self.status}"


class OrderDetail(models.Model):
    order = models.ForeignKey(
        Order, related_name="order_details", on_delete=models.RESTRICT
    )
    product = models.ForeignKey(
        Product, related_name="order_details", on_delete=models.RESTRICT
    )
    quantity = models.PositiveIntegerField(blank=True, default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2,
                                   default=0.00)

    class Meta:
        verbose_name = "OrderDetail"
        verbose_name_plural = "OrdersDetail"
        indexes = [
            models.Index(fields=["order"])
        ]

    def save(self, *args, **kwargs):
        self.subtotal = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order} - {self.product} - {self.quantity}"
