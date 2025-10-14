from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.common.status import HTTP_200_OK, HTTP_404_NOT_FOUND

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import Brand, Category, Product


@pytest.mark.django_db
@pytest.mark.unit
class TestIndexView:
    """Unit tests for the index view."""

    def test_index_view_renders_correctly(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that index view renders with correct template and context."""
        _, _, product = setup_data

        response = client.get(reverse("web:index"))

        assert response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in response.templates]

        # Verify context data
        assert "products" in response.context
        assert "categories" in response.context
        assert "brands" in response.context

        # Verify content
        content = response.content.decode()
        assert product.title in content

    def test_index_view_with_no_products(
        self,
        client: Client,
    ) -> None:
        """Test index view when no products exist."""
        response = client.get(reverse("web:index"))

        assert response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in response.templates]
        assert len(response.context["products"]) == 0

    def test_index_view_context_contains_all_data(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that index view context contains all required data."""
        category, brand, product = setup_data

        response = client.get(reverse("web:index"))

        # Verify products
        products = response.context["products"]
        assert product in products

        # Verify categories
        categories = response.context["categories"]
        assert category in categories

        # Verify brands
        brands = response.context["brands"]
        assert brand in brands


@pytest.mark.django_db
@pytest.mark.unit
class TestFilterByCategoryView:
    """Unit tests for the filter by category view."""

    def test_filter_by_category_success(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test filtering products by category."""
        category, _, product = setup_data

        response = client.get(
            reverse("web:filter_by_category", args=[category.pk]),
        )

        assert response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in response.templates]

        # Verify filtered products
        products = response.context["products"]
        assert product in products
        assert all(p.category == category for p in products)

    def test_filter_by_category_context_data(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that filter by category view has correct context."""
        category, _, _ = setup_data

        response = client.get(
            reverse("web:filter_by_category", args=[category.pk]),
        )

        assert "products" in response.context
        assert "categories" in response.context
        assert "brands" in response.context

    def test_filter_by_category_content(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that filtered content appears in response."""
        category, _, product = setup_data

        response = client.get(
            reverse("web:filter_by_category", args=[category.pk]),
        )

        content = response.content.decode()
        assert product.title in content

    def test_filter_by_invalid_category(
        self,
        client: Client,
    ) -> None:
        """Test filtering by non-existent category ID."""
        response = client.get(
            reverse("web:filter_by_category", args=[999]),
        )

        assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
@pytest.mark.unit
class TestFilterByBrandView:
    """Unit tests for the filter by brand view."""

    def test_filter_by_brand_success(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test filtering products by brand."""
        _, brand, product = setup_data

        response = client.get(reverse("web:filter_by_brand", args=[brand.pk]))

        assert response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in response.templates]

        # Verify filtered products
        products = response.context["products"]
        assert product in products
        assert all(p.brand == brand for p in products)

    def test_filter_by_brand_context_data(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that filter by brand view has correct context."""
        _, brand, _ = setup_data

        response = client.get(reverse("web:filter_by_brand", args=[brand.pk]))

        assert "products" in response.context
        assert "categories" in response.context
        assert "brands" in response.context

    def test_filter_by_brand_content(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that filtered content appears in response."""
        _, brand, product = setup_data

        response = client.get(reverse("web:filter_by_brand", args=[brand.pk]))

        content = response.content.decode()
        assert product.title in content

    def test_filter_by_invalid_brand(
        self,
        client: Client,
    ) -> None:
        """Test filtering by non-existent brand ID."""
        response = client.get(
            reverse("web:filter_by_brand", args=[999]),
        )

        assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
@pytest.mark.unit
class TestSearchProductTitleView:
    """Unit tests for the search product title view."""

    def test_search_product_title_post_success(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test searching for products by title via POST."""
        _, _, product = setup_data

        response = client.post(
            reverse("web:search_product_title"),
            {"title": product.title},
        )

        assert response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in response.templates]

        # Verify search results
        products = response.context["products"]
        assert product in products

    def test_search_product_title_partial_match(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test searching with partial title match."""
        _, _, product = setup_data

        # Search with partial title
        search_term = product.title[:5]  # First 5 characters
        response = client.post(
            reverse("web:search_product_title"),
            {"title": search_term},
        )

        assert response.status_code == HTTP_200_OK
        products = response.context["products"]
        assert product in products

    def test_search_product_title_no_results(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test searching with no matching results."""
        _, _, _ = setup_data

        response = client.post(
            reverse("web:search_product_title"),
            {"title": "NonExistentProduct"},
        )

        assert response.status_code == HTTP_200_OK
        products = response.context["products"]
        assert len(products) == 0

    def test_search_product_title_get_request(
        self,
        client: Client,
    ) -> None:
        """Test GET request to search view returns index page."""
        response = client.get(reverse("web:search_product_title"))

        assert response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in response.templates]

    def test_search_product_title_context_data(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that search view has correct context data."""
        _, _, product = setup_data

        response = client.post(
            reverse("web:search_product_title"),
            {"title": product.title},
        )

        assert "products" in response.context
        assert "categories" in response.context

    def test_search_product_title_empty_search(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test searching with empty title."""
        _, _, product = setup_data

        response = client.post(
            reverse("web:search_product_title"),
            {"title": ""},
        )

        assert response.status_code == HTTP_200_OK
        # Empty search should return products containing empty string (all products)
        products = response.context["products"]
        assert product in products


@pytest.mark.django_db
@pytest.mark.unit
class TestProductDetailView:
    """Unit tests for the product detail view."""

    def test_product_detail_success(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test product detail view with valid product ID."""
        _, _, product = setup_data

        response = client.get(reverse("web:product_detail", args=[product.pk]))

        assert response.status_code == HTTP_200_OK
        assert "web/product.html" in [t.name for t in response.templates]

        # Verify context
        assert "product" in response.context
        assert response.context["product"] == product

    def test_product_detail_content(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that product details appear in response content."""
        _, _, product = setup_data

        response = client.get(reverse("web:product_detail", args=[product.pk]))

        content = response.content.decode()
        assert product.title in content

    def test_product_detail_invalid_id(
        self,
        client: Client,
    ) -> None:
        """Test product detail view with non-existent product ID."""
        response = client.get(reverse("web:product_detail", args=[999]))

        assert response.status_code == HTTP_404_NOT_FOUND

    def test_product_detail_context_structure(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that product detail context has correct structure."""
        _, _, product = setup_data

        response = client.get(reverse("web:product_detail", args=[product.pk]))

        # Verify context structure
        context_product = response.context["product"]
        assert context_product.title == product.title
        assert context_product.category == product.category
        assert context_product.brand == product.brand
