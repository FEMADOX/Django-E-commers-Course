from typing import cast
from unittest.mock import Mock, patch

import pytest
from django.core import mail
from django.test import Client as DjangoTestClient
from django.test import override_settings
from django.urls import reverse

from account.models import Client as AccountClient
from edshop.settings import EMAIL_BACKEND, EMAIL_HOST_USER
from order.models import Order, OrderDetail
from tests.common.status import HTTP_200_OK, HTTP_302_REDIRECT, HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPaymentViewsAuthentication:
    """Test authentication requirements for all payment views."""

    @pytest.mark.parametrize(
        "url_name",
        [
            "payment:payment_process",
            "payment:payment_completed",
            "payment:payment_canceled",
        ],
    )
    def test_all_views_require_authentication(self, url_name: str) -> None:
        """Test that all payment views require authentication."""

        client = DjangoTestClient()
        response = client.get(reverse(url_name))
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response["Location"]

    @pytest.mark.parametrize(
        "url_name",
        [
            "payment:payment_process",
            "payment:payment_completed",
            "payment:payment_canceled",
        ],
    )
    def test_all_views_accessible_when_authenticated(
        self,
        url_name: str,
        authenticated_client: DjangoTestClient,
    ) -> None:
        """Test that all payment views are accessible when authenticated."""

        response = authenticated_client.get(reverse(url_name))
        # Views should be accessible (may redirect based on business logic)
        assert response.status_code in {HTTP_200_OK, HTTP_302_REDIRECT}

        if response.status_code == HTTP_302_REDIRECT:
            assert response["Location"] == reverse("web:index")


@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentProcessView:
    """Test cases for PaymentProcessView."""

    def test_post_no_order_in_session(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
    ) -> None:
        """Test POST request with no order in session."""

        response = authenticated_client.post(reverse("payment:payment_process"))
        assert response.status_code == HTTP_400_BAD_REQUEST

    @patch("stripe.checkout.Session.create")
    def test_post_success_with_order(
        self,
        mock_stripe_session: Mock,
        authenticated_client: DjangoTestClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test successful POST request with order in session."""

        # Mock Stripe session creation
        mock_stripe_session.return_value = Mock(url="https://checkout.stripe.com/test")

        # Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        response = authenticated_client.post(reverse("payment:payment_process"))
        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == "https://checkout.stripe.com/test"

    @patch("stripe.checkout.Session.create")
    def test_post_stripe_error(
        self,
        mock_stripe_session: Mock,
        authenticated_client: DjangoTestClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test POST request with Stripe error."""

        # Mock Stripe error
        mock_stripe_session.side_effect = Exception("Stripe error")

        # Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        with patch("payment.views.logger") as mock_logger:
            response = authenticated_client.post(reverse("payment:payment_process"))

            # Should handle error gracefully by returning 400 Bad Request
            assert response.status_code == HTTP_400_BAD_REQUEST
            assert (
                response.content
                == b"An unexpected error occurred. Please try again later."
            )

            # Verify logger error call
            mock_logger.exception.assert_called_with(
                f"Unexpected error during checkout session creation: "
                f"{mock_stripe_session.side_effect}",
            )


@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentCompletedView:
    """Test cases for PaymentCompletedView."""

    def test_get_no_order_in_session(
        self,
        authenticated_client: DjangoTestClient,
    ) -> None:
        """Test GET request without order in session."""

        response = authenticated_client.get(reverse("payment:payment_completed"))
        # Should redirect to index when no order
        assert response.status_code in {HTTP_200_OK, HTTP_302_REDIRECT}

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_HOST_USER="test@example.com",
    )
    def test_get_with_order_in_session(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test GET request with order in session."""

        # Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        with patch("payment.views.logger") as mock_logger:
            response = authenticated_client.get(reverse("payment:payment_completed"))

            client = account_client
            order_details_products = [
                order_detail.product.title
                for order_detail in order.order_details.all()  # type: ignore
            ]

            # The view should complete successfully
            assert response.status_code == HTTP_200_OK
            assert len(mail.outbox) == 1

            # Verify email content
            assert "Thanks for your purchase" in mail.outbox[0].subject
            assert (
                f"Thanks for your purchase {client.user.first_name}\n"  # type: ignore
                f"Your order was completed successfully\n"
                f"Your order num is {order.order_num}\n"
                f"Order products: {', '.join(order_details_products)}\n"
                f"Total Price {order.total_price}\n"
            ) in mail.outbox[0].body

            # Verify logger info call
            mock_logger.info.assert_called_with(
                f"Confirmation email sent for order {order.order_num}",
            )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_HOST_USER="test@example.com",
    )
    def test_get_with_order_email_sending_fails(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test GET request with order and email sending fails."""

        # Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        # Mock send_mail to raise an exception
        with (
            patch("payment.views.send_mail") as mock_send_mail,
            patch("payment.views.logger") as mock_logger,
        ):
            mock_send_mail.side_effect = Exception("SMTP connection failed")

            response = authenticated_client.get(reverse("payment:payment_completed"))

            # View should still complete successfully (order is processed)
            assert response.status_code == HTTP_200_OK

            # Verify that send_mail was called (attempt was made)
            mock_send_mail.assert_called_once()

            # Verify order status was updated despite email failure
            order.refresh_from_db()
            assert order.status == "1"

            # Verify no email was actually sent (because it failed)
            assert len(mail.outbox) == 0

            # Verify the order page is still rendered correctly
            assert "order" in response.context
            assert response.context["order"] == order
            assert "payment/payment_completed.html" in [
                t.name for t in response.templates
            ]

            # Verify logger captured the error
            mock_logger.exception.assert_called_with(
                f"Failed to send confirmation email for order "
                f"{order.order_num}: {mock_send_mail.side_effect}",
            )


@pytest.mark.django_db
@pytest.mark.unit
class TestPaymentCanceledView:
    """Test cases for PaymentCanceledView."""

    def test_displays_cancellation_page(
        self,
        authenticated_client: DjangoTestClient,
    ) -> None:
        """Test that cancellation page is displayed."""

        response = authenticated_client.get(reverse("payment:payment_canceled"))
        # Accept either 200 OK or redirect behavior
        assert response.status_code in {HTTP_200_OK, HTTP_302_REDIRECT}

        # Only check templates if response is 200 OK
        if response.status_code == HTTP_200_OK:
            template_names = [t.name for t in response.templates]
            assert "payment/payment_canceled.html" in template_names
