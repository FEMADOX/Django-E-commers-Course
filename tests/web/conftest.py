from __future__ import annotations

import pytest

from web.models import Brand, Category, Product


@pytest.fixture
def test_category(db: None) -> Category:  # noqa: ARG001
    """Create a test category for web tests."""
    return Category.objects.create(name="Electronics")


@pytest.fixture
def test_brand(db: None) -> Brand:  # noqa: ARG001
    """Create a test brand for web tests."""
    return Brand.objects.create(name="BrandA", fundator="FounderA")


@pytest.fixture
def test_product(test_category: Category, test_brand: Brand) -> Product:
    """Create a test product for web tests."""
    return Product.objects.create(
        title="Product1",
        category=test_category,
        price=100.00,
        brand=test_brand,
    )


@pytest.fixture
def setup_data(
    test_category: Category,
    test_brand: Brand,
    test_product: Product,
) -> tuple[Category, Brand, Product]:
    """Create test data for web app tests."""
    return test_category, test_brand, test_product
