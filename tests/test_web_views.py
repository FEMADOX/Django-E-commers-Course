import pytest
from django.urls import reverse

from web.models import Brand, Category, Product


@pytest.fixture
def setup_data(db):
    category = Category.objects.create(name="Electronics")
    brand = Brand.objects.create(name="BrandA", fundator="FounderA")
    product = Product.objects.create(
        title="Product1", category=category, price=100.00, brand=brand
    )
    return category, brand, product


def test_index_view(client, setup_data):
    category, brand, product = setup_data
    response = client.get(reverse("web:index"))

    assert response.status_code == 200
    assert "index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


def test_filter_by_category_view(client, setup_data):
    category, brand, product = setup_data
    response = client.get(
        reverse("web:filter_by_category", args=[category.pk])
    )

    assert response.status_code == 200
    assert "index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


def test_filter_by_brand_view(client, setup_data):
    category, brand, product = setup_data
    response = client.get(reverse("web:filter_by_brand", args=[brand.pk]))

    assert response.status_code == 200
    assert "index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


def test_search_product_title_view(client, setup_data):
    category, brand, product = setup_data
    response = client.post(reverse("web:search_product_title"),
                           {"title": "Product1"})

    assert response.status_code == 200
    assert "index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


def test_product_detail_view(client, setup_data):
    category, brand, product = setup_data
    response = client.get(reverse("web:product_detail", args=[product.pk]))

    assert response.status_code == 200
    assert "product.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()
