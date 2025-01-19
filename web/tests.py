# from django.http import HttpRequest, HttpResponse
from django.test import TestCase
from django.urls import reverse

from web.models import Brand, Category, Product

# from web.views import (filter_by_brand, filter_by_category, index,
#                        product_detail, search_product_title)

# Create your tests here.


class WebAppTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.brand = Brand.objects.create(name="BrandA", fundator="FounderA")
        self.product = Product.objects.create(
            title="Product1",
            category=self.category,
            price=100.00,
            brand=self.brand
        )

    def test_index_view(self):
        response = self.client.get(reverse('web:index'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, self.product.title)

    def test_filter_by_category_view(self):
        response = self.client.get(
            reverse('web:filter_by_category', args=[self.category.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, self.product.title)

    def test_filter_by_brand_view(self):
        response = self.client.get(
            reverse('web:filter_by_brand', args=[self.brand.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, self.product.title)

    def test_search_product_title_view(self):
        response = self.client.post(
            reverse('web:search_product_title'), {'title': 'Product1'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, self.product.title)

    def test_product_detail_view(self):
        response = self.client.get(
            reverse('web:product_detail', args=[self.product.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product.html')
        self.assertContains(response, self.product.title)
