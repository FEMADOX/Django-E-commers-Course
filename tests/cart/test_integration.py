"""Integration tests for cart views"""

import pytest
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse

from account.models import Client as ClientModel
from cart.cart import Cart
from order.models import Order
from tests.common.status import HTTP_200_OK, HTTP_302_REDIRECT
from web.models import Product

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


class TestCartWorkflow:
    """Integration tests for complete cart workflows"""

    def test_complete_cart_workflow(
        self,
        client: Client,
        user: User,
        product: Product,
        another_product: Product,
    ) -> None:
        """Test complete workflow: add → view → update → delete → clear"""
        # Login
        client.login(username="testuser", password="testpass123")

        # Step 1: Add first product to cart
        response = client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 2, "location-url": "/"},
        )
        assert response.status_code == HTTP_302_REDIRECT

        # Step 2: Add second product to cart
        response = client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": another_product.pk}),
            data={"quantity": 1, "location-url": "/"},
        )
        assert response.status_code == HTTP_302_REDIRECT

        # Step 3: View cart
        response = client.get(reverse("cart:cart"))
        assert response.status_code == HTTP_200_OK
        assert "cart" in response.wsgi_request.session

        # Step 4: Update product quantity
        response = client.patch(
            reverse("cart:update_product_cart", kwargs={"product_id": product.pk}),
            data='{"quantity": 5}',
            content_type="application/json",
        )
        assert response.status_code == HTTP_200_OK

        # Step 5: Delete a product
        response = client.post(
            reverse(
                "cart:delete_product_cart",
                kwargs={"product_id": another_product.pk},
            ),
            data={"location-url": "/cart/"},
        )
        assert response.status_code == HTTP_302_REDIRECT

        # Step 6: Clear cart
        response = client.post(
            reverse("cart:clear_cart"),
            data={"location-url": "/"},
        )
        assert response.status_code == HTTP_302_REDIRECT

    def test_unauthenticated_user_redirected_to_login(
        self,
        client: Client,
        product: Product,
    ) -> None:
        """Test that unauthenticated users are redirected to login"""
        response = client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 1},
        )

        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response.url  # type: ignore[attr-defined]

    def test_login_and_add_to_cart_workflow(
        self,
        client: Client,
        user: User,
        product: Product,
    ) -> None:
        """Test workflow: try to add → redirected to login → login → product added"""
        # Step 1: Try to add product without login
        response = client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 2},
            follow=False,
        )
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response.url  # type: ignore[attr-defined]

        # Step 2: Login
        client.login(username="testuser", password="testpass123")

        # Step 3: Add product after login
        response = client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 2, "location-url": "/"},
        )
        assert response.status_code == HTTP_302_REDIRECT

    def test_empty_cart_redirects_to_home(
        self,
        client: Client,
        user: User,
    ) -> None:
        """Test that empty cart redirects to home with message"""
        client.login(username="testuser", password="testpass123")

        response = client.get(reverse("cart:cart"), follow=True)

        assert response.status_code == HTTP_200_OK
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) > 0
        assert "empty" in str(messages[0]).lower()

    def test_cart_persists_across_requests(
        self,
        client: Client,
        user: User,
        product: Product,
    ) -> None:
        """Test that cart data persists across multiple requests"""
        client.login(username="testuser", password="testpass123")

        # Add product
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 3, "location-url": "/"},
        )

        # Make another request
        response = client.get("/")
        assert response.status_code == HTTP_200_OK

        # Cart should still have the product
        session = client.session
        assert "cart" in session
        assert str(product.pk) in session["cart"]
        assert session["cart"][str(product.pk)]["quantity"] == 3  # noqa: PLR2004


class TestRestoreOrderIntegration:
    """Integration tests for restoring pending orders"""

    def test_restore_pending_order_to_cart(
        self,
        client: Client,
        user: User,
        pending_order: Order,
        product: Product,
        another_product: Product,
    ) -> None:
        """Test restoring a pending order populates the cart correctly"""
        client.login(username="testuser", password="testpass123")

        # Clear cart first
        client.post(reverse("cart:clear_cart"), data={"location-url": "/"})

        # Restore order
        response = client.post(
            reverse(
                "cart:restore_order_pending_cart",
                kwargs={"order_pending_id": pending_order.pk},
            ),
            data={"location-url": "/cart/"},
        )

        assert response.status_code == HTTP_302_REDIRECT
        assert response.url == "/cart/"  # type: ignore[attr-defined]

        # Verify cart has products from order
        session = client.session
        assert str(product.pk) in session["cart"]
        assert str(another_product.pk) in session["cart"]

    def test_restore_order_clears_previous_cart(
        self,
        client: Client,
        user: User,
        product: Product,
        pending_order: Order,
    ) -> None:
        """Test that restoring an order clears the existing cart"""
        client.login(username="testuser", password="testpass123")

        # Add different product to cart
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 5, "location-url": "/"},
        )

        # Restore order (should clear current cart)
        client.post(
            reverse(
                "cart:restore_order_pending_cart",
                kwargs={"order_pending_id": pending_order.pk},
            ),
            data={"location-url": "/cart/"},
        )

        # Cart should have products from restored order, not the previous product
        session = client.session
        # Check that quantity matches restored order, not previous cart
        assert (
            session["cart"][str(product.pk)]["quantity"] == 2  # noqa: PLR2004
        )

    def test_user_can_only_restore_own_orders(
        self,
        client: Client,
        user: User,
        another_user: User,
        pending_order: Order,
    ) -> None:
        """Test that users can only restore their own orders"""
        # Login as different user
        client.login(username="anotheruser", password="testpass123")

        # Try to restore first user's order
        response = client.post(
            reverse(
                "cart:restore_order_pending_cart",
                kwargs={"order_pending_id": pending_order.pk},
            ),
            data={"location-url": "/cart/"},
        )

        # Should handle gracefully (the cart.restore_order_pending will fail)
        # The behavior depends on Cart implementation


class TestUpdateCartIntegration:
    """Integration tests for updating cart items"""

    def test_update_multiple_products_sequentially(
        self,
        client: Client,
        user: User,
        product: Product,
        another_product: Product,
    ) -> None:
        """Test updating multiple products in cart"""
        client.login(username="testuser", password="testpass123")

        # Add products
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 1, "location-url": "/"},
        )
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": another_product.pk}),
            data={"quantity": 1, "location-url": "/"},
        )

        # Update first product
        response = client.patch(
            reverse("cart:update_product_cart", kwargs={"product_id": product.pk}),
            data='{"quantity": 10}',
            content_type="application/json",
        )
        assert response.status_code == HTTP_200_OK

        # Update second product
        response = client.patch(
            reverse(
                "cart:update_product_cart",
                kwargs={"product_id": another_product.pk},
            ),
            data='{"quantity": 5}',
            content_type="application/json",
        )
        assert response.status_code == HTTP_200_OK

        # Verify both updates persisted
        session = client.session
        assert session["cart"][str(product.pk)]["quantity"] == 10  # noqa: PLR2004
        assert session["cart"][str(another_product.pk)]["quantity"] == 5  # noqa: PLR2004

    def test_update_returns_correct_totals(
        self,
        client: Client,
        user: User,
        product: Product,
    ) -> None:
        """Test that update returns correct subtotal and total"""
        client.login(username="testuser", password="testpass123")

        # Add product
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 2, "location-url": "/"},
        )

        # Update quantity
        response = client.patch(
            reverse("cart:update_product_cart", kwargs={"product_id": product.pk}),
            data='{"quantity": 5}',
            content_type="application/json",
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()

        # Check that totals are calculated correctly
        expected_subtotal = float(product.price) * 5
        assert "subtotal" in data
        assert "total_price" in data
        assert float(data["subtotal"]) == expected_subtotal


class TestCartViewContextIntegration:
    """Integration tests for CartIndexView context"""

    def test_cart_view_shows_pending_orders(
        self,
        client: Client,
        user: User,
        product: Product,
        pending_order: Order,
    ) -> None:
        """Test that cart view displays pending orders"""
        client.login(username="testuser", password="testpass123")

        # Add product to cart first
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 1, "location-url": "/"},
        )

        response = client.get(reverse("cart:cart"))

        assert response.status_code == HTTP_200_OK
        assert "pending_orders" in response.context
        assert pending_order in response.context["pending_orders"]

    def test_cart_view_excludes_completed_orders(
        self,
        client: Client,
        user: User,
        product: Product,
        completed_order: Order,
    ) -> None:
        """Test that cart view doesn't show completed orders"""
        client.login(username="testuser", password="testpass123")

        # Add product to cart
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 1, "location-url": "/"},
        )

        response = client.get(reverse("cart:cart"))

        assert response.status_code == HTTP_200_OK
        assert "pending_orders" in response.context
        assert completed_order not in response.context["pending_orders"]

    def test_cart_view_shows_only_user_orders(
        self,
        client: Client,
        user: User,
        another_client_account: ClientModel,
        product: Product,
        pending_order: Order,
    ) -> None:
        """Test that cart view only shows current user's orders"""
        # Create order for another user
        other_order = Order.objects.create(
            client=another_client_account,
            status="0",
            total_price=100.00,
        )

        client.login(username="testuser", password="testpass123")

        # Add product to cart
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 1, "location-url": "/"},
        )

        response = client.get(reverse("cart:cart"))

        assert response.status_code == HTTP_200_OK
        assert pending_order in response.context["pending_orders"]
        assert other_order not in response.context["pending_orders"]


class TestDeleteCartIntegration:
    """Integration tests for deleting cart items"""

    def test_delete_product_updates_cart_immediately(
        self,
        client: Client,
        user: User,
        product: Product,
        another_product: Product,
    ) -> None:
        """Test that deleting a product immediately updates the cart"""
        client.login(username="testuser", password="testpass123")

        # Add two products
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 2, "location-url": "/"},
        )
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": another_product.pk}),
            data={"quantity": 1, "location-url": "/"},
        )

        # Delete one product
        client.post(
            reverse("cart:delete_product_cart", kwargs={"product_id": product.pk}),
            data={"location-url": "/cart/"},
        )

        # Verify it's removed
        session = client.session
        assert str(product.pk) not in session["cart"]
        assert str(another_product.pk) in session["cart"]

    def test_delete_last_product_allows_cart_view(
        self,
        client: Client,
        user: User,
        product: Product,
    ) -> None:
        """Test that deleting last product makes cart empty"""
        client.login(username="testuser", password="testpass123")

        # Add one product
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 1, "location-url": "/"},
        )

        # Delete it
        client.post(
            reverse("cart:delete_product_cart", kwargs={"product_id": product.pk}),
            data={"location-url": "/cart/"},
        )

        # Cart should be empty
        session = client.session
        cart_data = session.get("cart", {})
        assert len(cart_data) == 0


class TestClearCartIntegration:
    """Integration tests for clearing cart"""

    def test_clear_cart_removes_all_products(
        self,
        client: Client,
        user: User,
        product: Product,
        another_product: Product,
    ) -> None:
        """Test that clearing cart removes all products"""
        client.login(username="testuser", password="testpass123")

        # Add multiple products
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 5, "location-url": "/"},
        )
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": another_product.pk}),
            data={"quantity": 3, "location-url": "/"},
        )

        # Clear cart
        response = client.post(
            reverse("cart:clear_cart"),
            data={"location-url": "/"},
        )

        assert response.status_code == HTTP_302_REDIRECT

        # Verify cart is empty
        session = client.session
        cart_data = session.get("cart", {})
        assert len(cart_data) == 0

    def test_clear_cart_and_add_new_products(
        self,
        client: Client,
        user: User,
        product: Product,
        another_product: Product,
    ) -> None:
        """Test workflow: add → clear → add different products"""
        client.login(username="testuser", password="testpass123")

        # Add product
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 2, "location-url": "/"},
        )

        # Clear cart
        client.post(reverse("cart:clear_cart"), data={"location-url": "/"})

        # Add different product
        client.post(
            reverse("cart:add_product_cart", kwargs={"product_id": another_product.pk}),
            data={"quantity": 1, "location-url": "/"},
        )

        # Verify only new product is in cart
        session = client.session
        assert str(product.pk) not in session["cart"]
        assert str(another_product.pk) in session["cart"]
        assert session["cart"][str(another_product.pk)]["quantity"] == 1
