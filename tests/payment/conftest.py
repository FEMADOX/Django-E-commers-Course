import pytest
from django.test import Client as DjangoTestClient

from account.models import Client as AccountClient
from account.models import User
from cart.cart import Decimal
from order.models import Order, OrderDetail
from web.models import Brand, Category, Product


@pytest.fixture
def user() -> User:
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def account_client(user: User) -> AccountClient:
    """Create a test client instance."""
    return AccountClient.objects.create(
        user=user,
        dni=12345678,
        address="Test Address",
        phone="123456789",
    )


@pytest.fixture
def category() -> Category:
    """Create a test category."""
    return Category.objects.create(name="Test Category")


@pytest.fixture
def brand() -> Brand:
    """Create a test brand."""
    return Brand.objects.create(name="Test Category")


@pytest.fixture
def product(category: Category, brand: Brand) -> Product:
    """Create a test product."""
    return Product.objects.create(
        title="Test Product",
        price=Decimal("29.99"),
        description="Test Description",
        brand=brand,
        category=category,
    )


@pytest.fixture
def order(account_client: AccountClient) -> Order:
    """Create a test order."""
    return Order.objects.create(
        client=account_client,
        total_price=Decimal("59.98"),
        status="0",  # Pending status
    )


@pytest.fixture
def order_detail(order: Order, product: Product) -> OrderDetail:
    """Create a test order detail."""
    return OrderDetail.objects.create(
        order=order,
        product=product,
        quantity=2,
        subtotal=Decimal("59.98"),
    )


@pytest.fixture
def authenticated_client(user: User) -> DjangoTestClient:
    """Create an authenticated Django test client."""
    client = DjangoTestClient()
    client.force_login(user)
    return client


@pytest.fixture
def authenticated_client_with_cart(
    authenticated_client: DjangoTestClient,
    product: Product,
    order_detail: OrderDetail,
) -> DjangoTestClient:
    """Create an authenticated Django test client with items in the cart."""

    # Initialize session and add cart data
    session = authenticated_client.session
    session["cart"] = {
        str(product.pk): {
            "quantity": order_detail.quantity,
            "price": str(product.price),
            "subtotal": str(order_detail.subtotal),
        }
    }
    session["cart_total_price"] = str(order_detail.subtotal * order_detail.quantity)
    session.save()

    return authenticated_client
