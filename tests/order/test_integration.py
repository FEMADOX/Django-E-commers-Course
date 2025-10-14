"""
Integration tests for order views.

This module contains integration tests that test the complete workflow
of order creation, confirmation, and summary display with real database
interactions and full request/response cycles.
"""

from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.test import Client as DjangoTestClient
from django.test import override_settings
from django.urls import reverse

from account.models import Client as AccountClient
from order.models import Order, OrderDetail
from tests.common.status import HTTP_200_OK, HTTP_302_REDIRECT, HTTP_404_NOT_FOUND
from web.models import Category, Product


@pytest.mark.integration
@pytest.mark.django_db
class TestOrderWorkflowIntegration:
    """Integration tests for complete order workflow."""

    def test_complete_order_creation_workflow(
        self,
        authenticated_client: DjangoTestClient,
        authenticated_user: User,
        product: Product,
        category: Category,
    ) -> None:
        """Test complete order creation workflow from start to finish."""
        # Step 1: Set up cart in session using the Cart class
        # First make a request to get proper session handling
        authenticated_client.get("/")  # Any view to initialize session

        # Set up cart data with proper structure expected by template
        session = authenticated_client.session
        session["cart"] = {
            str(product.pk): {
                "product_id": product.pk,
                "title": product.title,
                "price": str(product.price),
                "quantity": 2,
                "subtotal": str(Decimal(product.price) * 2),
                "description": product.description,
                "image": "",  # Empty image for test
                "weight": "",
                "dimension": "",
                "color": "",
                "category": {
                    "id": category.pk,
                    "name": category.name,
                },
                "brand": {
                    "id": 1,  # Default brand ID for test
                    "name": "Test Brand",
                },
            },
        }
        session["cart_total_price"] = str(Decimal(product.price) * 2)
        session.save()

        # Step 2: Access create order page
        response = authenticated_client.get(reverse("order:create_order"))
        assert response.status_code == HTTP_200_OK
        assert "client_form" in response.context

        # Step 3: Submit order confirmation
        order_data = {
            "name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Test Street",
        }
        response = authenticated_client.post(
            reverse("order:confirm_order"),
            data=order_data,
        )

        # Step 4: Verify order creation and redirect
        assert response.status_code == HTTP_302_REDIRECT

        # Verify order was created
        order = Order.objects.get(client__user=authenticated_user)
        assert order.total_price == Decimal(product.price) * 2
        assert order.order_num.startswith("Order #")

        # Verify order detail was created
        order_detail = OrderDetail.objects.get(order=order)
        assert order_detail.product == product
        order_detail_quantity_expected = 2
        assert order_detail.quantity == order_detail_quantity_expected
        assert order_detail.subtotal == Decimal(product.price) * 2

        # Step 5: Access order summary
        response = authenticated_client.get(
            reverse("order:order_summary", args=[order.pk]),
        )
        assert response.status_code == HTTP_200_OK
        assert response.context["order"] == order
        assert authenticated_client.session["order_id"] == order.pk

        # Step 6: Verify user data was updated
        authenticated_user.refresh_from_db()
        assert authenticated_user.first_name == "John"
        assert authenticated_user.last_name == "Doe"
        assert authenticated_user.email == "john@example.com"

        # Step 7: Verify client was created/updated
        client = AccountClient.objects.get(user=authenticated_user)
        assert client.phone == "1234567890"
        assert client.address == "123 Test Street"

    def test_order_workflow_with_existing_client(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
        product: Product,
    ) -> None:
        """Test order workflow when user already has a client profile."""
        # Set up cart
        session = authenticated_client.session
        session["cart"] = {
            str(product.pk): {
                "product_id": product.pk,
                "quantity": 1,
                "subtotal": str(product.price),
            },
        }
        session["cart_total_price"] = str(product.price)
        session.save()

        # Submit order with different data
        order_data = {
            "name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "phone": "9876543210",
            "address": "456 New Avenue",
        }
        response = authenticated_client.post(
            reverse("order:confirm_order"),
            data=order_data,
        )

        assert response.status_code == HTTP_302_REDIRECT

        # Verify existing client was updated
        account_client.refresh_from_db()
        assert account_client.phone == "9876543210"
        assert account_client.address == "456 New Avenue"

        # Verify order was created with existing client
        order = Order.objects.get(client=account_client)
        assert order.total_price == product.price

    def test_multiple_products_order_workflow(
        self,
        authenticated_client: DjangoTestClient,
        authenticated_user: User,
        category: Category,
    ) -> None:
        """Test order workflow with multiple products."""
        # Create multiple products
        product1 = Product.objects.create(
            title="Product 1",
            price=Decimal("15.00"),
            category=category,
        )
        product2 = Product.objects.create(
            title="Product 2",
            price=Decimal("25.00"),
            category=category,
        )
        product3 = Product.objects.create(
            title="Product 3",
            price=Decimal("35.00"),
            category=category,
        )

        # Set up cart with multiple products
        total_price = Decimal("0.00")
        cart_data = {}

        for i, product in enumerate([product1, product2, product3], 1):
            quantity = i  # 1, 2, 3
            subtotal = product.price * quantity
            total_price += subtotal

            cart_data[str(product.pk)] = {
                "product_id": product.pk,
                "quantity": quantity,
                "subtotal": str(subtotal),
            }

        session = authenticated_client.session
        session["cart"] = cart_data
        session["cart_total_price"] = str(total_price)
        session.save()

        # Submit order
        order_data = {
            "name": "Multi",
            "last_name": "Product",
            "email": "multi@example.com",
            "phone": "5555555555",
            "address": "789 Multi Street",
        }
        response = authenticated_client.post(
            reverse("order:confirm_order"),
            data=order_data,
        )

        assert response.status_code == HTTP_302_REDIRECT

        # Verify order and details
        order = Order.objects.get(client__user=authenticated_user)
        assert order.total_price == total_price

        order_details = OrderDetail.objects.filter(order=order).order_by("product__pk")
        order_detail_count_expected = 3
        assert order_details.count() == order_detail_count_expected

        expected_quantities = [1, 2, 3]
        for detail, expected_qty in zip(
            order_details,
            expected_quantities,
            strict=False,
        ):
            assert detail.quantity == expected_qty
            assert detail.subtotal == detail.product.price * expected_qty

    def test_order_workflow_empty_cart_handling(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
    ) -> None:
        """Test order workflow when cart is empty."""
        # Ensure no cart in session
        session = authenticated_client.session
        if "cart" in session:
            del session["cart"]
        session.save()

        # Try to submit order
        order_data = {
            "name": "Empty",
            "last_name": "Cart",
            "email": "empty@example.com",
            "phone": "0000000000",
            "address": "000 Empty Street",
        }
        response = authenticated_client.post(
            reverse("order:confirm_order"),
            data=order_data,
        )

        # Should redirect to cart page
        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("cart:cart")

        # No order should be created
        assert Order.objects.count() == 0

    def test_order_summary_workflow_invalid_order(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
    ) -> None:
        """Test order summary with invalid order ID."""
        response = authenticated_client.get(
            reverse("order:order_summary", args=[99999]),
        )
        assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.integration
@pytest.mark.django_db
class TestOrderSecurityIntegration:
    """Integration tests for order security."""

    def test_unauthenticated_access_prevention(self) -> None:
        """Test that all order views require authentication."""
        client = DjangoTestClient()

        urls_to_test = [
            reverse("order:create_order"),
            reverse("order:confirm_order"),
            reverse("order:order_summary", args=[1]),
        ]

        for url in urls_to_test:
            response = client.get(url)
            assert response.status_code == HTTP_302_REDIRECT
            assert "/account/login/" in response["Location"]

    def test_cross_user_order_access_prevention(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
        order: Order,
    ) -> None:
        """Test that users cannot access other users' orders."""
        # Create another user and client
        other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="otherpass123",
        )
        other_client = AccountClient.objects.create(
            user=other_user,
            dni=87654321,
            phone="9999999999",
            address="999 Other Street",
        )

        # Create order for other user
        other_order = Order.objects.create(
            client=other_client,
            total_price=Decimal("100.00"),
        )

        # Try to access other user's order
        response = authenticated_client.get(
            reverse("order:order_summary", args=[other_order.pk]),
        )

        # Should return 404 (order not found for this user)
        assert response.status_code == HTTP_404_NOT_FOUND

    def test_order_data_integrity(
        self,
        authenticated_client: DjangoTestClient,
        authenticated_user: User,
        product: Product,
    ) -> None:
        """Test that order data integrity is maintained throughout workflow."""
        original_product_price = product.price

        # Set up cart
        quantity = 3
        session = authenticated_client.session
        session["cart"] = {
            str(product.pk): {
                "product_id": product.pk,
                "quantity": quantity,
                "subtotal": str(original_product_price * quantity),
            },
        }
        session["cart_total_price"] = str(original_product_price * quantity)
        session.save()

        # Submit order
        order_data = {
            "name": "Integrity",
            "last_name": "Test",
            "email": "integrity@example.com",
            "phone": "1111111111",
            "address": "111 Integrity Street",
        }
        response = authenticated_client.post(
            reverse("order:confirm_order"),
            data=order_data,
        )

        assert response.status_code == HTTP_302_REDIRECT

        # Verify order data integrity
        order = Order.objects.get(client__user=authenticated_user)
        order_detail = OrderDetail.objects.get(order=order)

        # Check that order preserves original cart data
        expected_total = original_product_price * quantity
        assert order.total_price == expected_total
        assert order_detail.quantity == quantity
        assert order_detail.subtotal == expected_total
        assert order_detail.product == product

        # Verify cart was cleared
        assert authenticated_client.session.get("cart") == {}


@pytest.mark.integration
@pytest.mark.django_db
class TestOrderErrorHandlingIntegration:
    """Integration tests for order error handling."""

    def test_invalid_form_data_handling(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
    ) -> None:
        """Test handling of invalid form data."""
        # Set up cart
        session = authenticated_client.session
        session["cart"] = {"1": {"product_id": 1, "quantity": 1, "subtotal": "10.00"}}
        session.save()

        # Submit invalid form data (missing required fields)
        invalid_data = {
            "name": "",  # Required field is empty
            "email": "invalid-email",  # Invalid email format
        }
        response = authenticated_client.post(
            reverse("order:confirm_order"),
            data=invalid_data,
        )

        # Should re-render form with errors (not redirect)
        assert response.status_code == HTTP_200_OK

        # No order should be created
        assert Order.objects.count() == 0

    def test_nonexistent_product_in_cart_handling(
        self,
        authenticated_client: DjangoTestClient,
        account_client: AccountClient,
    ) -> None:
        """Test handling when cart contains nonexistent product."""
        # Set up cart with nonexistent product
        session = authenticated_client.session
        session["cart"] = {
            "99999": {  # Nonexistent product ID
                "product_id": 99999,
                "quantity": 1,
                "subtotal": "10.00",
            },
        }
        session["cart_total_price"] = "10.00"
        session.save()

        # Submit valid form data
        order_data = {
            "name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "1234567890",
            "address": "123 Test Street",
        }

        # This should handle the error gracefully
        response = authenticated_client.post(
            reverse("order:confirm_order"),
            data=order_data,
        )

        # The view should handle the DoesNotExist exception
        # (exact behavior depends on implementation)
        assert response.status_code in {HTTP_200_OK, HTTP_302_REDIRECT}

    def test_concurrent_order_creation_handling(
        self,
        authenticated_user: User,
        product: Product,
    ) -> None:
        """Test handling of concurrent order creation attempts."""
        # Create two clients for the same user
        client1 = DjangoTestClient()
        client2 = DjangoTestClient()

        client1.force_login(authenticated_user)
        client2.force_login(authenticated_user)

        # Set up identical carts in both clients
        cart_data = {
            str(product.pk): {
                "product_id": product.pk,
                "quantity": 1,
                "subtotal": str(product.price),
            },
        }

        for client in [client1, client2]:
            session = client.session
            session["cart"] = cart_data
            session["cart_total_price"] = str(product.price)
            session.save()

        # Submit orders concurrently
        order_data = {
            "name": "Concurrent",
            "last_name": "Test",
            "email": "concurrent@example.com",
            "phone": "2222222222",
            "address": "222 Concurrent Street",
        }

        response1 = client1.post(reverse("order:confirm_order"), data=order_data)
        response2 = client2.post(reverse("order:confirm_order"), data=order_data)

        # Both should handle gracefully
        assert response1.status_code in {HTTP_200_OK, HTTP_302_REDIRECT}
        assert response2.status_code in {HTTP_200_OK, HTTP_302_REDIRECT}

        # At least one order should be created
        assert Order.objects.filter(client__user=authenticated_user).count() >= 1
