from collections.abc import Iterable

from django.db import models
from django.db.models.base import ModelBase

from account.models import Client
from web.models import Product

# Create your models here.


class Order(models.Model):
    STATUS_CHOICES = (
        ("0", "Pendings"),
        ("1", "Paid"),
    )

    client = models.ForeignKey(Client, on_delete=models.RESTRICT)
    registration_date = models.DateTimeField(auto_now_add=True)
    order_num = models.CharField(max_length=20, blank=True, default="0000")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="0")

    class Meta:
        ordering = ["-registration_date"]
        indexes = [
            models.Index(fields=["client", "registration_date", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.client} - {self.order_num} - {self.status}"


class OrderDetail(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="order_details",
        on_delete=models.RESTRICT,
    )
    product = models.ForeignKey(
        Product,
        related_name="order_details",
        on_delete=models.RESTRICT,
    )
    quantity = models.PositiveIntegerField(blank=True, default=1)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Order Detail"
        verbose_name_plural = "Orders Detail"
        indexes = [
            models.Index(fields=["order"]),
        ]

    def __str__(self) -> str:
        return f"{self.order} - {self.product} - {self.quantity}"

    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        self.subtotal = self.product.price * self.quantity
        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
