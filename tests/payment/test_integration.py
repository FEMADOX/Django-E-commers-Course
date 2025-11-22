from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core import mail
from django.test import Client as DjangoTestClient
from django.urls import reverse

from account.models import Client as AccountClient
from order.models import Order, OrderDetail
from tests.common.status import HTTP_200_OK, HTTP_302_REDIRECT, HTTP_400_BAD_REQUEST
from web.models import Category, Product


@pytest.mark.django_db
@pytest.mark.integration
class TestPaymentWorkflowIntegration:
    """Integration tests for complete payment workflows."""

    @patch("stripe.checkout.Session.create")
    def test_complete_payment_process_workflow(
        self,
        mock_stripe_session: Mock,
        authenticated_client: DjangoTestClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test complete payment workflow from process to completion."""

        # Mock Stripe session creation
        mock_stripe_session.return_value = Mock(
            url="https://checkout.stripe.com/test",
        )

        # Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        # Step 1: Process payment (POST to create Stripe session)
        response = authenticated_client.post(reverse("payment:payment_process"))
        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == "https://checkout.stripe.com/test"

        # Step 2: Simulate successful payment completion
        response = authenticated_client.get(reverse("payment:payment_completed"))
        assert response.status_code == HTTP_200_OK

        # Step 3: Verify email was sent
        client = AccountClient.objects.get(pk=order.client.pk)  # type: ignore
        order_details_products = [
            od.product.title for od in OrderDetail.objects.filter(order=order)
        ]
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "Thanks for your purchase" in email.subject
        assert (
            f"Thanks for your purchase {client.user.first_name}\n"  # type: ignore
            f"Your order was completed successfully\n"
            f"Your order num is {order.order_num}\n"
            f"Order products: {', '.join(order_details_products)}\n"
            f"Total Price {order.total_price}\n"
        ) in mail.outbox[0].body
        assert order.client.user.email in email.to  # type: ignore

        # Step 4: Verify order status updated to PAID
        order.refresh_from_db()
        assert order.status == "1"  # PAID status

        # Step 5: Verify cart is cleared from session
        session = authenticated_client.session
        assert "cart" not in session
        assert "order_id" not in session

    def test_payment_cancellation_workflow(
        self,
        authenticated_client_with_cart: DjangoTestClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test payment cancellation workflow."""

        # Step 1: Add order to session
        session = authenticated_client_with_cart.session
        session["order_id"] = order.pk
        session.save()

        # Step 2: Simulate payment cancellation
        response = authenticated_client_with_cart.get(
            reverse("payment:payment_canceled")
        )

        messages = list(get_messages(response.wsgi_request))
        assert any("Payment was canceled." in str(message) for message in messages)
        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("order:create_order")

        # Step 3: Verify order status remains Pending
        order.refresh_from_db()
        assert order.status == "0"  # Still Pending

        # Step 4: Verify cart is intact but order_id was removed
        session = authenticated_client_with_cart.session
        assert session.get("cart") is not None
        # order_id is popped by PaymentCanceledView
        assert "order_id" not in session

    @patch("stripe.checkout.Session.create")
    def test_stripe_integration_with_line_items(
        self,
        mock_stripe_session: Mock,
        authenticated_client: DjangoTestClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test Stripe integration with proper line items configuration."""

        # Step 1: Mock Stripe session creation
        mock_stripe_session.return_value = Mock(
            url="https://checkout.stripe.com/test",
        )

        # Step 2: Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        # Step 3: Make POST request to process payment
        response = authenticated_client.post(reverse("payment:payment_process"))

        # Step 4: Verify Stripe session was called with correct parameters
        mock_stripe_session.assert_called_once()
        call_args = mock_stripe_session.call_args[1]

        # Step 5: Verify session data structure
        assert call_args["mode"] == "payment"
        assert call_args["client_reference_id"] == order.order_num
        if hasattr(order.client, "user") and hasattr(order.client.user, "email"):
            assert call_args["customer_email"] == order.client.user.email
        assert "line_items" in call_args
        assert len(call_args["line_items"]) == 1

        # Step 6: Verify line item details
        line_item = call_args["line_items"][0]
        assert line_item["quantity"] == order_detail.quantity
        assert line_item["price_data"]["currency"] == "usd"

        # Check unit amount calculation
        if hasattr(order_detail.product, "price") and isinstance(
            order_detail.product.price,
            int,
        ):
            assert line_item["price_data"]["unit_amount"] == int(
                order_detail.product.price * 100,
            )

    def test_order_without_details_handling(
        self,
        authenticated_client: DjangoTestClient,
        order: Order,
        account_client: AccountClient,
    ) -> None:
        """Test handling of order without order details."""

        # Step 1: Add order to session (but no order details)
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        # Step 2: Attempt to process payment
        response = authenticated_client.post(reverse("payment:payment_process"))

        # Should handle gracefully with empty order details - returns 400 error
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_session_handling_across_requests(
        self,
        authenticated_client: DjangoTestClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test session handling across multiple requests."""

        # Step 1: Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        # Session should still contain order_id
        session = authenticated_client.session
        assert session.get("order_id") == order.pk

        # Step 2: Complete payment (this should remove order_id from session)
        response = authenticated_client.get(reverse("payment:payment_completed"))
        assert response.status_code == HTTP_200_OK

        assert "order_id" not in authenticated_client.session

    def test_multiple_order_details_processing(
        self,
        authenticated_client: DjangoTestClient,
        order: Order,
        product: Product,
        category: Category,
    ) -> None:
        """Test processing order with multiple order details."""

        # Step 1: Create additional product and order detail
        product2 = Product.objects.create(
            title="Test Product 2",
            price=Decimal("19.99"),
            description="Test Description 2",
            category=category,
        )

        OrderDetail.objects.create(
            order=order,
            product=product,
            quantity=2,
            subtotal=Decimal("59.98"),
        )

        OrderDetail.objects.create(
            order=order,
            product=product2,
            quantity=1,
            subtotal=Decimal("19.99"),
        )

        # Step 2: Update order total
        order.total_price = Decimal("79.97")
        order.save()

        # Step 3: Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        # Step 4: Process payment
        with patch("stripe.checkout.Session.create") as mock_stripe:
            mock_stripe.return_value = Mock(url="https://checkout.stripe.com/test")

            response = authenticated_client.post(reverse("payment:payment_process"))

            # Verify multiple line items were created
            expected_line_items = 2
            call_args = mock_stripe.call_args[1]
            assert len(call_args["line_items"]) == expected_line_items

        # Step 5: Complete payment
        response = authenticated_client.get(reverse("payment:payment_completed"))
        assert response.status_code == HTTP_200_OK

        # Step 6: Verify order status updated to PAID
        order.refresh_from_db()
        assert order.status == "1"


@pytest.mark.django_db
@pytest.mark.integration
class TestPaymentErrorHandlingIntegration:
    """Integration tests for error handling scenarios."""

    def test_invalid_order_id_in_session(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
    ) -> None:
        """Test handling of invalid order ID in session."""

        # Step 1: Add invalid order ID to session
        session = authenticated_client.session
        session["order_id"] = 99999  # Non-existent order
        session.save()

        # Step 2: Attempt to process payment
        response = authenticated_client.post(reverse("payment:payment_process"))

        # Should handle error gracefully - returns 400 for invalid order
        assert response.status_code == HTTP_400_BAD_REQUEST

    @patch("stripe.checkout.Session.create")
    def test_stripe_api_failure_handling(
        self,
        mock_stripe_session: Mock,
        authenticated_client: DjangoTestClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test handling of Stripe API failures."""

        # Step 1: Mock Stripe API failure
        mock_stripe_session.side_effect = Exception("Stripe API Error")

        # Step 2: Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        with patch("payment.views.logger") as mock_logger_error:
            # Step 3: Attempt to process payment
            response = authenticated_client.post(reverse("payment:payment_process"))

            # Should handle error gracefully by returning 400 Bad Request
            assert response.status_code == HTTP_400_BAD_REQUEST
            assert (
                response.content
                == b"An unexpected error occurred. Please try again later."
            )

            # Verify logger error call
            mock_logger_error.exception.assert_called_with(
                f"Unexpected error during checkout session creation: "
                f"{mock_stripe_session.side_effect}",
            )

            # Step 4: Order status should remain unchanged
            order.refresh_from_db()
            assert order.status == "0"  # Still Pending

    @patch("payment.views.send_mail")
    def test_email_sending_failure_handling(
        self,
        mock_send_mail: Mock,
        authenticated_client: DjangoTestClient,
        order: Order,
        order_detail: OrderDetail,
    ) -> None:
        """Test handling of email sending failures."""

        # Step 1: Mock email sending failure
        mock_send_mail.side_effect = Exception("Email sending failed")

        # Step 2: Add order to session
        session = authenticated_client.session
        session["order_id"] = order.pk
        session.save()

        # Step 3: Complete payment
        response = authenticated_client.get(reverse("payment:payment_completed"))

        # Should still complete successfully despite email failure
        assert response.status_code == HTTP_200_OK

        # Step 4: Verify order status updated to PAID
        order.refresh_from_db()
        assert order.status == "1"

        # Step 5: Verify email sending was attempted
        mock_send_mail.assert_called_once()
