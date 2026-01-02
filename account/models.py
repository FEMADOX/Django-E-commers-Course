from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField

if TYPE_CHECKING:
    from order.models import Order


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.RESTRICT)
    dni = models.PositiveSmallIntegerField(blank=True, default=0)
    sex = models.CharField(max_length=1, blank=True, default="N")
    phone = PhoneNumberField(blank=True, null=False, default="")
    birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True)
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["user", "dni"])]

    def __str__(self) -> str:
        return f"DNI: {self.dni} - User: {self.user}"

    def get_absolute_url(self) -> str:
        return reverse("client_detail", kwargs={"pk": self.pk})

    if TYPE_CHECKING:
        orders: models.QuerySet["Order"]
