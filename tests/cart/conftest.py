"""Fixtures for cart tests"""

from typing import Any

import pytest
from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.test import RequestFactory

from account.models import Client
from cart.cart import Cart
from order.models import Order, OrderDetail
from web.models import Brand, Category, Product


@pytest.fixture
def user() -> User:
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="testpass123",
    )


@pytest.fixture
def another_user() -> User:
    """Create another test user for isolation tests"""
    return User.objects.create_user(
        username="anotheruser",
        email="another@example.com",
        password="testpass123",
    )


@pytest.fixture
def another_client_account(another_user: User) -> Client:
    """Create a Client instance linked to another_user."""
    return Client.objects.create(
        user=another_user,
        dni=87654321,
        phone="987654321",
        address="456 Another Street",
    )


@pytest.fixture
def client_account(user: User) -> Client:
    """Create a Client instance linked to the test user."""
    return Client.objects.create(
        user=user,
        dni=12345678,
        phone="123456789",
        address="123 Test Street",
    )


@pytest.fixture
def category() -> Category:
    """Create a test category"""
    return Category.objects.create(
        name="Test Category",
    )


@pytest.fixture
def brand() -> Brand:
    """Create a test brand"""
    return Brand.objects.create(
        name="Test Brand",
        fundator="Test Fundator",
    )


@pytest.fixture
def product(category: Category, brand: Brand) -> Product:
    """Create a test product"""
    return Product.objects.create(
        title="Test Product",
        description="Test product description",
        price=99.99,
        category=category,
        brand=brand,
    )


@pytest.fixture
def another_product(category: Category, brand: Brand) -> Product:
    """Create another test product"""
    return Product.objects.create(
        title="Another Product",
        description="Another product description",
        price=49.99,
        category=category,
        brand=brand,
    )


@pytest.fixture
def out_of_stock_product(category: Category, brand: Brand) -> Product:
    """Create a product that simulates out of stock scenario"""
    return Product.objects.create(
        title="Out of Stock Product",
        description="Product that can be used for testing out of stock scenarios",
        price=29.99,
        category=category,
        brand=brand,
    )


@pytest.fixture
def request_factory() -> RequestFactory:
    """Return Django RequestFactory instance"""
    return RequestFactory()


@pytest.fixture
def request_with_session(request_factory: RequestFactory) -> WSGIRequest:
    """Create a request with session and message middleware"""
    request = request_factory.get("/")

    # Add session middleware
    session_middleware = SessionMiddleware(lambda _: HttpResponse())
    session_middleware.process_request(request)
    request.session.save()

    # Add message middleware
    message_middleware = MessageMiddleware(lambda _: HttpResponse())
    message_middleware.process_request(request)

    return request


@pytest.fixture
def authenticated_request(
    request_with_session: WSGIRequest,
    user: User,
) -> WSGIRequest:
    """Create an authenticated request with session and messages"""
    request_with_session.user = user
    return request_with_session


@pytest.fixture
def cart(request_with_session: WSGIRequest) -> Cart:
    """Create a Cart instance with session"""
    return Cart(request_with_session)


@pytest.fixture
def cart_with_products(cart: Cart, product: Product, another_product: Product) -> Cart:
    """Create a cart with multiple products"""
    cart.add(product, 2)
    cart.add(another_product, 1)
    return cart


@pytest.fixture
def pending_order(
    client_account: Client,
    product: Product,
    another_product: Product,
) -> Order:
    """Create a pending order with multiple products"""
    order = Order.objects.create(
        client=client_account,
        status="0",  # Pending
        total_price=249.97,
    )

    OrderDetail.objects.create(
        order=order,
        product=product,
        quantity=2,
    )

    OrderDetail.objects.create(
        order=order,
        product=another_product,
        quantity=1,
    )

    return order


@pytest.fixture
def completed_order(client_account: Client, product: Product) -> Order:
    """Create a completed order"""
    order = Order.objects.create(
        client=client_account,
        status="1",  # Completed
        total_price=99.99,
    )

    OrderDetail.objects.create(
        order=order,
        product=product,
        quantity=1,
    )

    return order


@pytest.fixture
def cart_session_data(
    product: Product,
    another_product: Product,
) -> dict[str, dict[str, Any]]:
    """Sample cart session data structure"""
    return {
        str(product.pk): {
            "product_id": product.pk,
            "title": product.title,
            "quantity": 2,
            "price": str(product.price),
            "image": "",
        },
        str(another_product.pk): {
            "product_id": another_product.pk,
            "title": another_product.title,
            "quantity": 1,
            "price": str(another_product.price),
            "image": "",
        },
    }
