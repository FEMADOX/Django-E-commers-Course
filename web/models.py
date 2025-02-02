from django.db import models

# Create your models here.


def get_default_brand() -> int:
    brand, _ = Brand.objects.get_or_create(name="None")
    return brand.pk


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
    image = models.ImageField(
        upload_to="brands",
        blank=True,
        null=True,
        default="",
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
        blank=True, default="No description for this product",
    )
    image = models.ImageField(upload_to="products", blank=True, null=True, default="")
    brand = models.ForeignKey(
        Brand, on_delete=models.RESTRICT, blank=True, default=get_default_brand,
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
