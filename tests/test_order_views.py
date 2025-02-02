from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from account.models import Client
from order.models import Order, OrderDetail
from tests.status import HTTP_302_REDIRECT
from web.models import Category, Product


@pytest.fixture
def setup_data(db, client):  # noqa: ARG001
    # Create a user
    user = User.objects.create_user(username="testuser", password="testpass")
    client.login(username="testuser", password="testpass")

    # Create category
    category = Category.objects.create(name="TEST CATEGORY")

    # Create products
    product_1 = Product.objects.create(
        title="Product 1", category=category, price=Decimal(10),
    )
    product_2 = Product.objects.create(
        title="Product 2", category=category, price=Decimal(20),
    )

    # Create a client
    client_model = Client.objects.create(
        user=user, phone="1234567890", address="123 Test St",
    )

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

    def get_total_price(cart: dict):
        total = 0
        for value in cart.values():
            total += Decimal(value["subtotal"])
        return total

    session["cart_total_price"] = str(get_total_price(session["cart"]))
    session.save()

    return client, user, client_model, product_1, product_2, session


def test_confirm_order_success(setup_data):
    client, _, client_model, product_1, product_2, _ = setup_data

    response = client.post(
        reverse("order:confirm_order"),
        {
            "name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "1234567890",
            "address": "123 Test St",
        },
    )
    order = Order.objects.get(client=client_model)

    assert response.status_code == HTTP_302_REDIRECT
    assert response.url == reverse("order:order_summary", args=[order.pk])

    # Check that the order was created
    assert Order.objects.count() == 1
    assert order.client == client_model
    assert order.total_price == Decimal(50)

    # Check that the order details were created
    order_detail_total = 2
    assert OrderDetail.objects.count() == order_detail_total
    order_detail_1 = OrderDetail.objects.get(product=product_1)
    assert order_detail_1.quantity == 1
    assert order_detail_1.subtotal == Decimal(10)

    order_detail_2 = OrderDetail.objects.get(product=product_2)
    assert order_detail_2.quantity == order_detail_total
    assert order_detail_2.subtotal == Decimal(40)


def test_confirm_order_empty_cart(setup_data):
    client, _, _, _, _, session = setup_data

    # Clear the cart
    session["cart"] = {}
    session.save()

    response = client.post(
        reverse("order:confirm_order"),
        {
            "name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "1234567890",
            "address": "123 Test St",
        },
    )

    assert response.status_code == HTTP_302_REDIRECT
    assert response.url == reverse("cart:cart")

    # Check that no order was created
    assert Order.objects.count() == 0


def test_confirm_order_with_pending_orders(setup_data):
    client, _, client_model, product_1, _, _ = setup_data

    # Create a pending order
    pending_order = Order.objects.create(client=client_model, status="0")
    OrderDetail.objects.create(
        order=pending_order, product=product_1, quantity=1,
        subtotal=Decimal(10),
    )

    response = client.post(
        reverse("order:confirm_order"),
        {
            "name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "1234567890",
            "address": "123 Test St",
        },
    )
    new_order = Order.objects.filter(client=client_model).first()

    assert response.status_code == HTTP_302_REDIRECT
    assert response.url == reverse(
        "order:order_summary",
        args=[new_order.pk],  # type: ignore[attr-defined]
    )

    # Check that the new order was created
    order_total = 2
    assert Order.objects.count() == order_total
    assert new_order.client == client_model  # type: ignore[attr-defined]
    assert new_order.total_price == Decimal(50)  # type: ignore[attr-defined]

    # Check that the pending order details were moved to the new order
    assert OrderDetail.objects.count() == 3  # noqa: PLR2004
    assert OrderDetail.objects.filter(order=new_order).count() == 2  # noqa: PLR2004
