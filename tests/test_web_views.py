from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.test.client import Client
from django.urls import reverse

from tests.status import HTTP_200_OK
from web.models import Brand, Category, Product

if TYPE_CHECKING:
    from django.http import HttpResponse
    from django.test import Client


@pytest.fixture
def setup_data(db: None) -> tuple[Category, Brand, Product]:  # noqa: ARG001
    """Create test data for web app tests."""
    category = Category.objects.create(name="Electronics")
    brand = Brand.objects.create(name="BrandA", fundator="FounderA")
    product = Product.objects.create(
        title="Product1",
        category=category,
        price=100.00,
        brand=brand,
    )
    return category, brand, product


def test_index_view(
    client: Client,
    setup_data: tuple[Category, Brand, Product],
) -> None:
    _, _, product = setup_data
    response = client.get(reverse("web:index"))

    assert response.status_code == HTTP_200_OK
    assert "web/index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


def test_filter_by_category_view(
    client: Client,
    setup_data: tuple[Category, Brand, Product],
) -> None:
    category, _, product = setup_data
    response = client.get(
        reverse("web:filter_by_category", args=[category.pk]),
    )

    assert response.status_code == HTTP_200_OK
    assert "web/index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


def test_filter_by_brand_view(
    client: Client,
    setup_data: tuple[Category, Brand, Product],
) -> None:
    _, brand, product = setup_data
    response = client.get(reverse("web:filter_by_brand", args=[brand.pk]))

    assert response.status_code == HTTP_200_OK
    assert "web/index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


def test_search_product_title_view(
    client: Client,
    setup_data: tuple[Category, Brand, Product],
) -> None:
    _, _, product = setup_data
    response = client.post(reverse("web:search_product_title"), {"title": "Product1"})

    assert response.status_code == HTTP_200_OK
    assert "web/index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


def test_product_detail_view(
    client: Client,
    setup_data: tuple[Category, Brand, Product],
) -> None:
    _, _, product = setup_data
    response = client.get(reverse("web:product_detail", args=[product.pk]))

    assert response.status_code == HTTP_200_OK
    assert "web/product.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()
