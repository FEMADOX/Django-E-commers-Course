from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.RESTRICT)
    dni = models.CharField(max_length=10)
    sex = models.CharField(max_length=1, blank=True, default="N")
    phone = models.CharField(max_length=20, blank=True, default="")
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
