from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.common.status import HTTP_200_OK

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import Brand, Category, Product


@pytest.mark.unit
def test_index_view(
    client: Client,
    setup_data: tuple[Category, Brand, Product],
) -> None:
    _, _, product = setup_data
    response = client.get(reverse("web:index"))

    assert response.status_code == HTTP_200_OK
    assert "web/index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


@pytest.mark.unit
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


@pytest.mark.unit
def test_filter_by_brand_view(
    client: Client,
    setup_data: tuple[Category, Brand, Product],
) -> None:
    _, brand, product = setup_data
    response = client.get(reverse("web:filter_by_brand", args=[brand.pk]))

    assert response.status_code == HTTP_200_OK
    assert "web/index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


@pytest.mark.unit
def test_search_product_title_view(
    client: Client,
    setup_data: tuple[Category, Brand, Product],
) -> None:
    _, _, product = setup_data
    response = client.post(reverse("web:search_product_title"), {"title": "Product1"})

    assert response.status_code == HTTP_200_OK
    assert "web/index.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()


@pytest.mark.unit
def test_product_detail_view(
    client: Client,
    setup_data: tuple[Category, Brand, Product],
) -> None:
    _, _, product = setup_data
    response = client.get(reverse("web:product_detail", args=[product.pk]))

    assert response.status_code == HTTP_200_OK
    assert "web/product.html" in [t.name for t in response.templates]
    assert product.title in response.content.decode()
