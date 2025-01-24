from django.test import TestCase
from django.urls import reverse

from tests.status import HTTP_200_OK
from web.models import Brand, Category, Product

# Create your tests here.


class WebAppTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.brand = Brand.objects.create(name="BrandA", fundator="FounderA")
        self.product = Product.objects.create(
            title="Product1",
            category=self.category,
            price=100.00,
            brand=self.brand,
        )

    def test_index_view(self):
        response = self.client.get(reverse("web:index"))

        assert response.status_code == HTTP_200_OK
        self.assertTemplateUsed(response, "index.html")
        self.assertContains(response, self.product.title)

    def test_filter_by_category_view(self):
        response = self.client.get(
            reverse("web:filter_by_category", args=[self.category.pk]),
        )

        assert response.status_code == HTTP_200_OK
        self.assertTemplateUsed(response, "index.html")
        self.assertContains(response, self.product.title)

    def test_filter_by_brand_view(self):
        response = self.client.get(
            reverse("web:filter_by_brand", args=[self.brand.pk]),
        )

        assert response.status_code == HTTP_200_OK
        self.assertTemplateUsed(response, "index.html")
        self.assertContains(response, self.product.title)

    def test_search_product_title_view(self):
        response = self.client.post(
            reverse("web:search_product_title"), {"title": "Product1"},
        )

        assert response.status_code == HTTP_200_OK
        self.assertTemplateUsed(response, "index.html")
        self.assertContains(response, self.product.title)

    def test_product_detail_view(self):
        response = self.client.get(
            reverse("web:product_detail", args=[self.product.pk]),
        )

        assert response.status_code == HTTP_200_OK
        self.assertTemplateUsed(response, "product.html")
        self.assertContains(response, self.product.title)
