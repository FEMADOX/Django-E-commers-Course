from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from tests.common.status import HTTP_200_OK, HTTP_404_NOT_FOUND

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import Brand, Category, Product


@pytest.mark.django_db
@pytest.mark.integration
class TestWebWorkflowIntegration:
    """Integration tests for complete web workflow scenarios."""

    def test_complete_product_browsing_workflow(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test complete workflow: Index → Category Filter → Product Detail."""
        category, brand, product = setup_data

        # Step 1: User visits homepage
        index_response = client.get(reverse("web:index"))
        assert index_response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in index_response.templates]

        # Verify homepage shows all products, categories, and brands
        assert product in index_response.context["products"]
        assert category in index_response.context["categories"]
        assert brand in index_response.context["brands"]

        # Step 2: User filters by category
        category_response = client.get(
            reverse("web:filter_by_category", args=[category.pk]),
        )
        assert category_response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in category_response.templates]

        # Verify filtered results
        filtered_products = category_response.context["products"]
        assert product in filtered_products
        assert all(p.category == category for p in filtered_products)

        # Step 3: User views product detail
        detail_response = client.get(
            reverse("web:product_detail", args=[product.pk]),
        )
        assert detail_response.status_code == HTTP_200_OK
        assert "web/product.html" in [t.name for t in detail_response.templates]
        assert detail_response.context["product"] == product

        # Verify product detail content
        content = detail_response.content.decode()
        assert product.title in content

    def test_search_to_detail_workflow(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test workflow: Search → Results → Product Detail."""
        _, _, product = setup_data

        # Step 1: User searches for product
        search_response = client.post(
            reverse("web:search_product_title"),
            {"title": product.title[:5]},  # Partial search
        )
        assert search_response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in search_response.templates]

        # Verify search results
        search_results = search_response.context["products"]
        assert product in search_results

        # Step 2: User clicks on product from search results
        detail_response = client.get(
            reverse("web:product_detail", args=[product.pk]),
        )
        assert detail_response.status_code == HTTP_200_OK
        assert detail_response.context["product"] == product

        # Verify product information is complete
        detail_product = detail_response.context["product"]
        assert detail_product.title == product.title
        assert detail_product.category == product.category
        assert detail_product.brand == product.brand

    def test_brand_filtering_to_detail_workflow(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test workflow: Index → Brand Filter → Product Detail."""
        _, brand, product = setup_data

        # Step 1: User visits homepage
        index_response = client.get(reverse("web:index"))
        assert index_response.status_code == HTTP_200_OK

        # Step 2: User filters by brand
        brand_response = client.get(
            reverse("web:filter_by_brand", args=[brand.pk]),
        )
        assert brand_response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in brand_response.templates]

        # Verify brand filtering
        brand_products = brand_response.context["products"]
        assert product in brand_products
        assert all(p.brand == brand for p in brand_products)

        # Step 3: User views product detail
        detail_response = client.get(
            reverse("web:product_detail", args=[product.pk]),
        )
        assert detail_response.status_code == HTTP_200_OK
        assert detail_response.context["product"] == product

    def test_navigation_consistency_across_views(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that navigation data is consistent across all views."""
        category, brand, product = setup_data

        # Test index view
        index_response = client.get(reverse("web:index"))
        index_categories = set(index_response.context["categories"])
        index_brands = set(index_response.context["brands"])

        # Test category filter view
        category_response = client.get(
            reverse("web:filter_by_category", args=[category.pk]),
        )
        category_view_categories = set(category_response.context["categories"])
        category_view_brands = set(category_response.context["brands"])

        # Test brand filter view
        brand_response = client.get(
            reverse("web:filter_by_brand", args=[brand.pk]),
        )
        brand_view_categories = set(brand_response.context["categories"])
        brand_view_brands = set(brand_response.context["brands"])

        # Test search view
        search_response = client.post(
            reverse("web:search_product_title"),
            {"title": product.title},
        )
        search_categories = set(search_response.context["categories"])

        # Verify consistency - all views should show same navigation options
        assert index_categories == category_view_categories == brand_view_categories
        assert index_brands == category_view_brands == brand_view_brands
        assert index_categories == search_categories

    def test_empty_search_to_valid_search_workflow(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test workflow: Empty search → Valid search → Results."""
        _, _, product = setup_data

        # Step 1: User submits empty search
        empty_search_response = client.post(
            reverse("web:search_product_title"),
            {"title": ""},
        )
        assert empty_search_response.status_code == HTTP_200_OK
        # Empty search should return all products
        empty_search_products = empty_search_response.context["products"]
        assert product in empty_search_products

        # Step 2: User submits valid search
        valid_search_response = client.post(
            reverse("web:search_product_title"),
            {"title": product.title},
        )
        assert valid_search_response.status_code == HTTP_200_OK
        # Valid search should return specific products
        valid_search_products = valid_search_response.context["products"]
        assert product in valid_search_products

        # Step 3: User submits non-existent search
        no_results_response = client.post(
            reverse("web:search_product_title"),
            {"title": "NonExistentProduct"},
        )
        assert no_results_response.status_code == HTTP_200_OK
        # No results search should return empty queryset
        no_results_products = no_results_response.context["products"]
        assert len(no_results_products) == 0


@pytest.mark.django_db
@pytest.mark.integration
class TestWebErrorHandlingIntegration:
    """Integration tests for error handling scenarios."""

    def test_invalid_category_to_homepage_recovery(
        self,
        client: Client,
    ) -> None:
        """Test recovery workflow when accessing invalid category."""

        # Step 1: User tries to access invalid category
        invalid_category_response = client.get(
            reverse("web:filter_by_category", args=[999]),
        )
        assert invalid_category_response.status_code == HTTP_404_NOT_FOUND

        # Step 2: User recovers by going to homepage
        recovery_response = client.get(reverse("web:index"))
        assert recovery_response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in recovery_response.templates]

    def test_invalid_brand_to_homepage_recovery(
        self,
        client: Client,
    ) -> None:
        """Test recovery workflow when accessing invalid brand."""

        # Step 1: User tries to access invalid brand
        invalid_brand_response = client.get(
            reverse("web:filter_by_brand", args=[999]),
        )
        assert invalid_brand_response.status_code == HTTP_404_NOT_FOUND

        # Step 2: User recovers by going to homepage
        recovery_response = client.get(reverse("web:index"))
        assert recovery_response.status_code == HTTP_200_OK
        assert "web/index.html" in [t.name for t in recovery_response.templates]

    def test_invalid_product_to_search_recovery(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test recovery workflow when accessing invalid product."""
        _, _, product = setup_data

        # Step 1: User tries to access invalid product
        invalid_product_response = client.get(
            reverse("web:product_detail", args=[999]),
        )
        assert invalid_product_response.status_code == HTTP_404_NOT_FOUND

        # Step 2: User recovers by searching for products
        recovery_response = client.post(
            reverse("web:search_product_title"),
            {"title": product.title},
        )
        assert recovery_response.status_code == HTTP_200_OK
        assert product in recovery_response.context["products"]


@pytest.mark.django_db
@pytest.mark.integration
class TestWebDataConsistencyIntegration:
    """Integration tests for data consistency across views."""

    def test_product_data_consistency_across_views(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that product data is consistent across all views."""
        category, brand, product = setup_data

        # Get product data from each view
        products_from_views = self._get_products_from_all_views(
            client,
            category,
            brand,
            product,
        )

        # Verify all products have same data
        self._verify_product_consistency(products_from_views, product)

    def _get_products_from_all_views(
        self,
        client: Client,
        category: Category,
        brand: Brand,
        product: Product,
    ) -> list[Product]:
        """Helper method to get product from all views."""
        # Get product from index view
        index_response = client.get(reverse("web:index"))
        index_products = index_response.context["products"]
        index_product = next(p for p in index_products if p.pk == product.pk)

        # Get product from category filter
        category_response = client.get(
            reverse("web:filter_by_category", args=[category.pk]),
        )
        category_products = category_response.context["products"]
        category_product = next(p for p in category_products if p.pk == product.pk)

        # Get product from brand filter
        brand_response = client.get(
            reverse("web:filter_by_brand", args=[brand.pk]),
        )
        brand_products = brand_response.context["products"]
        brand_product = next(p for p in brand_products if p.pk == product.pk)

        # Get product from search
        search_response = client.post(
            reverse("web:search_product_title"),
            {"title": product.title},
        )
        search_products = search_response.context["products"]
        search_product = next(p for p in search_products if p.pk == product.pk)

        # Get product from detail view
        detail_response = client.get(
            reverse("web:product_detail", args=[product.pk]),
        )
        detail_product = detail_response.context["product"]

        return [
            index_product,
            category_product,
            brand_product,
            search_product,
            detail_product,
        ]

    def _verify_product_consistency(
        self,
        products_to_compare: list[Product],
        expected_product: Product,
    ) -> None:
        """Helper method to verify product data consistency."""
        for test_product in products_to_compare:
            assert test_product.pk == expected_product.pk
            assert test_product.title == expected_product.title
            assert test_product.category == expected_product.category
            assert test_product.brand == expected_product.brand

    def test_filtering_logic_consistency(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that filtering logic is consistent and correct."""
        category, brand, product = setup_data

        # Test category filtering
        category_response = client.get(
            reverse("web:filter_by_category", args=[category.pk]),
        )
        category_filtered_products = category_response.context["products"]

        # All products should belong to the specified category
        for filtered_product in category_filtered_products:
            assert filtered_product.category == category

        # Test brand filtering
        brand_response = client.get(
            reverse("web:filter_by_brand", args=[brand.pk]),
        )
        brand_filtered_products = brand_response.context["products"]

        # All products should belong to the specified brand
        for filtered_product in brand_filtered_products:
            assert filtered_product.brand == brand

        # Test search filtering
        search_response = client.post(
            reverse("web:search_product_title"),
            {"title": product.title[:3]},  # Partial match
        )
        search_filtered_products = search_response.context["products"]

        # All products should contain the search term
        search_term = product.title[:3]
        for filtered_product in search_filtered_products:
            assert search_term.lower() in filtered_product.title.lower()


@pytest.mark.django_db
@pytest.mark.integration
class TestWebTemplateIntegration:
    """Integration tests for template rendering consistency."""

    def test_template_inheritance_and_context(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that templates are properly inherited and context is passed."""
        category, brand, product = setup_data

        # Test all views that use web/index.html
        views_with_index_template = [
            (reverse("web:index"), {}),
            (reverse("web:filter_by_category", args=[category.pk]), {}),
            (reverse("web:filter_by_brand", args=[brand.pk]), {}),
            (reverse("web:search_product_title"), {"title": product.title}),
        ]

        for url, post_data in views_with_index_template:
            response = client.post(url, post_data) if post_data else client.get(url)

            assert response.status_code == HTTP_200_OK
            assert "web/index.html" in [t.name for t in response.templates]

            # Verify required context variables exist
            required_context_vars = ["products", "categories"]
            for var in required_context_vars:
                assert var in response.context

        # Test product detail template
        detail_response = client.get(
            reverse("web:product_detail", args=[product.pk]),
        )
        assert detail_response.status_code == HTTP_200_OK
        assert "web/product.html" in [t.name for t in detail_response.templates]
        assert "product" in detail_response.context

    def test_context_data_completeness(
        self,
        client: Client,
        setup_data: tuple[Category, Brand, Product],
    ) -> None:
        """Test that all views provide complete context data."""
        category, brand, product = setup_data

        # Test index view context
        index_response = client.get(reverse("web:index"))
        index_context = index_response.context
        assert "products" in index_context
        assert "categories" in index_context
        assert "brands" in index_context

        # Test category filter context
        category_response = client.get(
            reverse("web:filter_by_category", args=[category.pk]),
        )
        category_context = category_response.context
        assert "products" in category_context
        assert "categories" in category_context
        assert "brands" in category_context

        # Test brand filter context
        brand_response = client.get(
            reverse("web:filter_by_brand", args=[brand.pk]),
        )
        brand_context = brand_response.context
        assert "products" in brand_context
        assert "categories" in brand_context
        assert "brands" in brand_context

        # Test search context
        search_response = client.post(
            reverse("web:search_product_title"),
            {"title": product.title},
        )
        search_context = search_response.context
        assert "products" in search_context
        assert "categories" in search_context

        # Test product detail context
        detail_response = client.get(
            reverse("web:product_detail", args=[product.pk]),
        )
        detail_context = detail_response.context
        assert "product" in detail_context
