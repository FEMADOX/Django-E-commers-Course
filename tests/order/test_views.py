"""
Unit tests for order views.

This module contains unit tests for individual order view components,
focusing on isolated functionality testing with mocked dependencies.
"""

from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpResponse
from django.test import RequestFactory
from django.test.client import Client as DjangoTestClient
from django.urls import reverse

from account.forms import ClientForm
from account.models import Client as AccountClient
from order.models import Order, OrderDetail
from order.views import ConfirmOrderView, CreateOrderView, OrderSummaryView
from tests.common.status import (
    HTTP_200_OK,
    HTTP_302_REDIRECT,
    HTTP_404_NOT_FOUND,
)
from web.models import Product


@pytest.mark.unit
@pytest.mark.django_db
class TestCreateOrderView:
    """Unit tests for CreateOrderView."""

    def test_requires_authentication(self) -> None:
        """Test that CreateOrderView requires authentication."""

        client = DjangoTestClient()
        response = client.get(reverse("order:create_order"))
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response["Location"]

    def test_redirects_if_cart_empty(
        self,
        authenticated_client: DjangoTestClient,
    ) -> None:
        """Test that view redirects to cart if cart is empty."""

        response = authenticated_client.get(reverse("order:create_order"))
        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("web:index")

    def test_get_context_data(
        self,
        authenticated_client_with_cart: tuple[DjangoTestClient, SessionBase],
    ) -> None:
        """Test that context contains client form."""

        client_with_cart = authenticated_client_with_cart[0]
        response = client_with_cart.get(reverse("order:create_order"))

        assert response.status_code == HTTP_200_OK
        assert "client_form" in response.context
        assert isinstance(response.context["client_form"], ClientForm)

    def test_template_used(
        self,
        authenticated_client_with_cart: tuple[DjangoTestClient, SessionBase],
    ) -> None:
        """Test that correct template is used."""

        client_with_cart = authenticated_client_with_cart[0]
        response = client_with_cart.get(reverse("order:create_order"))

        assert response.status_code == HTTP_200_OK
        template_names = [t.name for t in response.templates]
        assert "order/order.html" in template_names

    @patch("order.views.get_or_create_client_form")
    def test_get_context_data_calls_client_form_helper(
        self,
        mock_get_or_create_client_form: Mock,
        authenticated_client_with_cart: tuple[DjangoTestClient, SessionBase],
        user: User,
    ) -> None:
        """Test that get_context_data calls client form helper."""

        mock_form = Mock(spec=ClientForm)
        mock_get_or_create_client_form.return_value = mock_form

        factory = RequestFactory()
        request = factory.get(reverse("order:create_order"))
        request.user = user

        view = CreateOrderView()
        view.request = request
        context = view.get_context_data()

        assert context["client_form"] == mock_form
        mock_get_or_create_client_form.assert_called_once_with(user)


@pytest.mark.unit
@pytest.mark.django_db
class TestConfirmOrderView:
    """Unit tests for ConfirmOrderView."""

    def test_requires_authentication(self) -> None:
        """Test that ConfirmOrderView requires authentication."""

        client = DjangoTestClient()
        response = client.post(reverse("order:confirm_order"))
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response["Location"]

    def test_form_class_is_client_form(self) -> None:
        """Test that view uses ClientForm."""

        view = ConfirmOrderView()
        assert view.form_class == ClientForm

    @patch("order.views.ConfirmOrderView._create_order")
    @patch("order.views.ConfirmOrderView._get_or_create_client")
    def test_form_valid_updates_user_data(
        self,
        mock_get_or_create_client: Mock,
        mock_create_order: Mock,
        user: User,
    ) -> None:
        """Test that form_valid updates user data correctly."""

        # Setup mocks
        mock_client = Mock(spec=AccountClient)
        mock_order = Mock(spec=Order)
        mock_order.pk = 1
        mock_get_or_create_client.return_value = mock_client
        mock_create_order.return_value = mock_order

        # Create form data
        form_data = {
            "name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Test St",
        }
        form = ClientForm(data=form_data)
        assert form.is_valid()

        # Create request with session and cart
        factory = RequestFactory()
        request = factory.post(reverse("order:confirm_order"))
        request.user = user

        # Mock the session with proper support for item assignment
        session_mock = Mock()
        session_mock.__getitem__ = Mock(
            side_effect=lambda key: {
                "cart": {"1": {"product_id": 1, "quantity": 1, "subtotal": "10.00"}},
                "cart_total_price": "10.00",
            }[key],
        )
        session_mock.__setitem__ = Mock()
        session_mock.__contains__ = Mock(
            side_effect=lambda key: key in {"cart", "cart_total_price"},
        )
        request.session = session_mock

        view = ConfirmOrderView()
        view.request = request

        # Test form_valid
        response = view.form_valid(form)

        # Verify user was updated
        user.refresh_from_db()
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.email == "john@example.com"

        # Verify response is redirect
        assert isinstance(response, HttpResponse)
        assert response.status_code == HTTP_302_REDIRECT

    def test_form_valid_empty_cart_redirects_to_cart(
        self,
        user: User,
    ) -> None:
        """Test that empty cart redirects to cart page."""

        form_data = {
            "name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Test St",
        }
        form = ClientForm(data=form_data)
        assert form.is_valid()

        factory = RequestFactory()
        request = factory.post(reverse("order:confirm_order"))
        request.user = user

        # Mock the session
        client_data_mock = Mock()
        client_data_mock.pop = Mock(
            side_effect=lambda key, default="": {
                "phone": "1234567890",
                "address": "123 Test St",
            }.get(key, default),
        )
        client_data_mock.__getitem__ = Mock(
            side_effect=lambda key: {
                "phone": "1234567890",
                "address": "123 Test St",
            }[key],
        )

        session_mock = Mock()
        session_mock.__getitem__ = Mock(
            side_effect=lambda key: {
                "cart": None,
                "client_data": client_data_mock,
            }[key],
        )
        session_mock.__setitem__ = Mock()
        session_mock.__contains__ = Mock(return_value=True)
        session_mock.get = Mock(return_value=None)
        request.session = session_mock

        view = ConfirmOrderView()
        view.request = request

        response = view.form_valid(form)

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("cart:cart")

    def test_get_or_create_client_existing_client(
        self,
        user: User,
        account_client: AccountClient,
    ) -> None:
        """Test _get_or_create_client with existing client."""

        factory = RequestFactory()
        request = factory.post(reverse("order:confirm_order"))
        request.user = user

        # Mock the session
        client_data_mock = Mock()
        client_data_mock.pop = Mock(
            side_effect=lambda key, default="": {
                "phone": "987654321",
                "address": "456 Test Avenue",
            }.get(key, default),
        )

        session_mock = Mock()
        session_mock.__getitem__ = Mock(
            side_effect=lambda key: {
                "client_data": client_data_mock,
            }[key],
        )
        session_mock.__setitem__ = Mock()
        session_mock.__contains__ = Mock(return_value=True)
        request.session = session_mock

        view = ConfirmOrderView()
        view.request = request

        # Test the private method directly
        result_client = view._get_or_create_client(user)  # noqa: SLF001

        # Verify the returned client is the existing one
        assert result_client == account_client

        # Verify the existing client was updated
        account_client.refresh_from_db()
        assert account_client.phone == "987654321"
        assert account_client.address == "456 Test Avenue"

    def test_get_or_create_client_new_client(
        self,
        user: User,
    ) -> None:
        """Test _get_or_create_client creates new client."""

        factory = RequestFactory()
        request = factory.post(reverse("order:confirm_order"))
        request.user = user

        # Mock the session
        session_mock = Mock()
        session_mock.__getitem__ = Mock(
            side_effect=lambda key: {
                "client_data": {
                    "phone": "1111111111",
                    "address": "789 Brand New St",
                },
            }[key],
        )
        session_mock.__contains__ = Mock(return_value=True)
        request.session = session_mock

        view = ConfirmOrderView()
        view.request = request

        result_client = view._get_or_create_client(user)  # noqa: SLF001

        assert isinstance(result_client, AccountClient)
        assert result_client.user == user
        assert result_client.phone == "1111111111"
        assert result_client.address == "789 Brand New St"

    def test_create_order_success(
        self,
        account_client: AccountClient,
        product: Product,
    ) -> None:
        """Test _create_order creates order and details correctly."""

        quantity = 2
        expected_subtotal = product.price * quantity

        cart_data = {
            str(product.pk): {
                "product_id": product.pk,
                "quantity": quantity,
                "subtotal": str(expected_subtotal),
            },
        }

        factory = RequestFactory()
        request = factory.post(reverse("order:confirm_order"))
        # Create a mock session
        session_mock = Mock()
        session_mock.pop.return_value = str(expected_subtotal)
        request.session = session_mock

        view = ConfirmOrderView()
        view.request = request

        # Cast cart_data to the expected Cart type for the method
        order = view._create_order(account_client, cart_data)  # type: ignore[arg-type]  # noqa: SLF001

        assert isinstance(order, Order)
        assert order.client == account_client
        assert order.total_price == expected_subtotal
        assert order.order_num.startswith("Order #")

        # Check order detail
        order_detail = OrderDetail.objects.get(order=order)
        assert order_detail.product == product
        assert order_detail.quantity == quantity
        assert order_detail.subtotal == expected_subtotal


@pytest.mark.unit
@pytest.mark.django_db
class TestOrderSummaryView:
    """Unit tests for OrderSummaryView."""

    def test_requires_authentication(self) -> None:
        """Test that OrderSummaryView requires authentication."""

        client = DjangoTestClient()
        response = client.get(reverse("order:order_summary", args=[1]))
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response["Location"]

    def test_model_and_template(self) -> None:
        """Test that view uses correct model and template."""

        view = OrderSummaryView()
        assert view.model == Order
        assert view.template_name == "order/shipping.html"
        assert view.context_object_name == "order"
        assert view.pk_url_kwarg == "order_id"

    def test_get_context_data_stores_order_id_in_session(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
        order: Order,
    ) -> None:
        """Test that get_context_data stores order ID in session."""

        response = authenticated_client.get(
            reverse("order:order_summary", args=[order.pk]),
        )

        assert response.status_code == HTTP_200_OK
        assert authenticated_client.session["order_id"] == order.pk

    def test_context_object_name(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
        order: Order,
    ) -> None:
        """Test that order is available in context with correct name."""

        response = authenticated_client.get(
            reverse("order:order_summary", args=[order.pk]),
        )

        assert response.status_code == HTTP_200_OK
        assert "order" in response.context
        assert response.context["order"] == order

    def test_nonexistent_order_returns_404(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
    ) -> None:
        """Test that accessing nonexistent order returns 404."""

        response = authenticated_client.get(
            reverse("order:order_summary", args=[99999]),
        )
        assert response.status_code == HTTP_404_NOT_FOUND
