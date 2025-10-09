from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Literal

import pytest
from django.contrib.auth.models import User

from account.models import Client
from web.models import Category, Product

if TYPE_CHECKING:
    from django.contrib.sessions.backends.base import SessionBase
    from django.test.client import Client as DjangoClient


@pytest.fixture
def test_user(db: None) -> User:  # noqa: ARG001
    """Create a test user for order tests."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def test_category(db: None) -> Category:  # noqa: ARG001
    """Create a test category for order tests."""
    return Category.objects.create(name="TEST CATEGORY")


@pytest.fixture
def test_products(test_category: Category) -> tuple[Product, Product]:
    """Create test products for order tests."""
    product_1 = Product.objects.create(
        title="Product 1",
        category=test_category,
        price=Decimal("10.00"),
    )
    product_2 = Product.objects.create(
        title="Product 2",
        category=test_category,
        price=Decimal("20.00"),
    )
    return product_1, product_2


@pytest.fixture
def test_client_model(test_user: User) -> Client:
    """Create a test client model for order tests."""
    return Client.objects.create(
        user=test_user,
        phone="1234567890",
        address="123 Test St",
    )


@pytest.fixture
def authenticated_client_with_cart(
    client: DjangoClient,
    test_user: User,  # noqa: ARG001
    test_products: tuple[Product, Product],
) -> tuple[DjangoClient, SessionBase]:
    """Create an authenticated client with cart data."""
    product_1, product_2 = test_products

    # Login the user
    client.login(username="testuser", password="testpass")

    # Set up cart in session
    session = client.session
    session["cart"] = {
        str(product_1.pk): {
            "product_id": product_1.pk,
            "quantity": 1,
            "subtotal": str(Decimal(product_1.price) * 1),
        },
        str(product_2.pk): {
            "product_id": product_2.pk,
            "quantity": 2,
            "subtotal": str(Decimal(product_2.price) * 2),
        },
    }

    def get_total_price(cart: dict) -> Decimal | Literal[0]:
        total = 0
        for value in cart.values():
            total += Decimal(value["subtotal"])
        return total

    session["cart_total_price"] = str(get_total_price(session["cart"]))
    session.save()

    return client, session


@pytest.fixture
def setup_data(
    authenticated_client_with_cart: tuple[DjangoClient, SessionBase],
    test_user: User,
    test_client_model: Client,
    test_products: tuple[Product, Product],
) -> tuple[DjangoClient, User, Client, Product, Product, SessionBase]:
    """Complete setup data fixture for order tests."""
    client, session = authenticated_client_with_cart
    product_1, product_2 = test_products

    return client, test_user, test_client_model, product_1, product_2, session
