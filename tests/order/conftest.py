from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Literal

import pytest
from django.contrib.auth.models import User
from django.test import Client as DjangoTestClient

from account.models import Client
from order.models import Order
from web.models import Category, Product

if TYPE_CHECKING:
    from django.contrib.sessions.backends.base import SessionBase


@pytest.fixture
def test_user(db: None) -> User:  # noqa: ARG001
    """Create a test user for order tests."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def authenticated_user(db: None) -> User:  # noqa: ARG001
    """Create an authenticated user for order tests."""
    return User.objects.create_user(
        username="authuser",
        email="auth@example.com",
        password="authpass123",
    )


@pytest.fixture
def category(db: None) -> Category:  # noqa: ARG001
    """Create a category for tests."""
    return Category.objects.create(name="Test Category")


@pytest.fixture
def product(category: Category) -> Product:
    """Create a test product."""
    return Product.objects.create(
        title="Test Product",
        price=Decimal("29.99"),
        category=category,
    )


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
def order(account_client: Client) -> Order:
    """Create a test order."""
    return Order.objects.create(
        client=account_client,
        total_price=Decimal("59.98"),
        status="0",  # Pending status
    )


@pytest.fixture
def account_client(authenticated_user: User) -> Client:
    """Create an account client for tests."""
    return Client.objects.create(
        user=authenticated_user,
        dni=12345678,
        phone="987654321",
        address="456 Test Avenue",
    )


@pytest.fixture
def authenticated_client(authenticated_user: User) -> DjangoTestClient:
    """Create an authenticated Django test client."""
    client = DjangoTestClient()
    client.force_login(authenticated_user)
    return client


@pytest.fixture
def authenticated_client_with_cart(
    client: DjangoTestClient,
    test_user: User,  # noqa: ARG001
    test_products: tuple[Product, Product],
) -> tuple[DjangoTestClient, SessionBase]:
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
    authenticated_client_with_cart: tuple[DjangoTestClient, SessionBase],
    test_user: User,
    test_client_model: Client,
    test_products: tuple[Product, Product],
) -> tuple[DjangoTestClient, User, Client, Product, Product, SessionBase]:
    """Complete setup data fixture for order tests."""
    client, session = authenticated_client_with_cart
    product_1, product_2 = test_products

    return client, test_user, test_client_model, product_1, product_2, session
