from cloudinary.models import CloudinaryField
from django.db import models

# Create your models here.


def get_default_brand() -> "Brand":
    brand, _ = Brand.objects.get_or_create(name="None")
    return brand


class Category(models.Model):
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=50)
    fundator = models.CharField(max_length=100)
    image = CloudinaryField(
        "image",
        blank=True,
        folder="Django-E-commers/media/brands/",
        default="https://res.cloudinary.com/dd1qoripz/image/upload/v1745813449/No_Image_Available_wvog0c.jpg",
        transformation={
            "width": 300,
            "height": 300,
            "crop": "fill",
            "quality": "auto",
            "fetch_format": "auto",
        },
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        indexes = [
            models.Index(fields=["name", "fundator"]),
        ]

    def __str__(self) -> str:
        return f"{self.name}"


class Product(models.Model):
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.RESTRICT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Optionals
    description = models.TextField(
        blank=True,
        default="No description for this product",
    )
    image = CloudinaryField(
        "image",
        blank=True,
        folder="Django-E-commers/media/products/",
        default="https://res.cloudinary.com/dd1qoripz/image/upload/v1745813449/No_Image_Available_wvog0c.jpg",
        transformation={
            "width": 300,
            "height": 300,
            "crop": "fill",
            "quality": "auto",
            "fetch_format": "auto",
        },
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.RESTRICT,
        blank=True,
        default=get_default_brand,
    )
    weight = models.PositiveIntegerField(blank=True, null=True, default=0)
    dimension = models.CharField(max_length=50, blank=True, default="N/A")
    color = models.CharField(max_length=50, blank=True, default="N/A")

    class Meta:
        ordering = ["-created"]
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=["title", "category"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} - {self.category} - {self.price}"
