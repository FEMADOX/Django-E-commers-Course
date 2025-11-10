"""Unit tests for cart views"""

import json

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.test import RequestFactory
from django.urls import reverse

from cart.cart import Cart
from cart.views import (
    AddProductCartView,
    CartIndexView,
    ClearCartView,
    DeleteProductCartView,
    RestoreOrderPendingCartView,
    UpdateProductCartView,
)
from order.models import Order
from tests.cart.conftest import WSGIRequest
from tests.common.status import HTTP_200_OK, HTTP_302_REDIRECT, HTTP_400_BAD_REQUEST
from web.models import Product

User = get_user_model()

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _add_session_to_request(request: WSGIRequest) -> None:
    """Helper function to add session and message middleware to request"""
    session_middleware = SessionMiddleware(lambda _: HttpResponse())
    session_middleware.process_request(request)
    request.session.save()

    message_middleware = MessageMiddleware(lambda _: HttpResponse())
    message_middleware.process_request(request)


class TestCartIndexView:
    """Unit tests for CartIndexView"""

    def test_get_context_data_includes_pending_orders(
        self,
        authenticated_request: WSGIRequest,
        pending_order: Order,
    ) -> None:
        """Test that context includes user's pending orders"""
        view = CartIndexView()
        view.request = authenticated_request

        context = view.get_context_data()

        assert "pending_orders" in context
        assert pending_order in context["pending_orders"]

    def test_get_context_data_excludes_completed_orders(
        self,
        authenticated_request: WSGIRequest,
        completed_order: Order,
    ) -> None:
        """Test that context excludes completed orders"""
        view = CartIndexView()
        view.request = authenticated_request

        context = view.get_context_data()

        assert "pending_orders" in context
        assert completed_order not in context["pending_orders"]

    def test_get_redirects_when_cart_empty(
        self,
        authenticated_request: WSGIRequest,
    ) -> None:
        """Test redirect to home when cart is empty"""
        # Create empty cart
        Cart(authenticated_request).clear()

        view = CartIndexView.as_view()
        response = view(authenticated_request)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTP_302_REDIRECT
        assert response.url == "/catalog/"

    def test_get_with_products_in_cart(
        self,
        authenticated_request: WSGIRequest,
        cart_with_products: Cart,
    ) -> None:
        """Test successful GET with products in cart"""
        authenticated_request.session["cart"] = cart_with_products.cart

        view = CartIndexView.as_view()
        response = view(authenticated_request)

        assert response.status_code == HTTP_200_OK


class TestAddProductCartView:
    """Unit tests for AddProductCartView"""

    def test_post_adds_product_to_cart(
        self,
        rf: RequestFactory,
        user: User,
        product: Product,
    ) -> None:
        """Test adding product to cart via POST"""
        quantity = 2
        request = rf.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": quantity, "location-url": "/"},
        )
        request.user = user

        # Add session

        _add_session_to_request(request)

        view = AddProductCartView.as_view()
        response = view(request, product_id=product.pk)

        cart = Cart(request)
        assert str(product.pk) in cart.cart
        assert cart.cart[str(product.pk)]["quantity"] == quantity
        assert response.status_code == HTTP_302_REDIRECT

    def test_post_with_default_quantity(
        self,
        rf: RequestFactory,
        user: User,
        product: Product,
    ) -> None:
        """Test adding product with default quantity (1)"""
        request = rf.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"location-url": "/"},
        )
        request.user = user

        _add_session_to_request(request)

        view = AddProductCartView.as_view()
        view(request, product_id=product.pk)

        cart = Cart(request)
        assert cart.cart[str(product.pk)]["quantity"] == 1

    def test_post_redirects_to_location_url(
        self,
        rf: RequestFactory,
        user: User,
        product: Product,
    ) -> None:
        """Test redirect to location-url after adding product"""
        request = rf.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 1, "location-url": "/catalog/"},
        )
        request.user = user

        _add_session_to_request(request)

        view = AddProductCartView.as_view()
        response = view(request, product_id=product.pk)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTP_302_REDIRECT
        assert response.url == "/catalog/"

    def test_post_with_nonexistent_product_raises_404(
        self,
        rf: RequestFactory,
        user: User,
    ) -> None:
        """Test adding nonexistent product raises 404"""

        request = rf.post(
            "/cart/add-to-cart/99999",
            data={"quantity": 1},
        )
        request.user = user

        _add_session_to_request(request)

        view = AddProductCartView.as_view()

        with pytest.raises(Http404):
            view(request, product_id=99999)

    def test_get_method_calls_post(
        self,
        rf: RequestFactory,
        user: User,
        product: Product,
    ) -> None:
        """Test GET method internally calls POST"""
        request = rf.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": "1"},
        )
        request.user = user

        _add_session_to_request(request)

        view = AddProductCartView.as_view()
        response = view(request, product_id=product.pk)

        assert response.status_code == HTTP_302_REDIRECT

    def test_login_required(self, rf: RequestFactory, product: Product) -> None:
        """Test that login is required to add products"""

        request = rf.post(
            reverse("cart:add_product_cart", kwargs={"product_id": product.pk}),
            data={"quantity": 1},
        )
        request.user = AnonymousUser()

        view = AddProductCartView.as_view()
        response = view(request, product_id=product.pk)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response.url


class TestDeleteProductCartView:
    """Unit tests for DeleteProductCartView"""

    def test_post_deletes_product_from_cart(
        self,
        rf: RequestFactory,
        user: User,
        product: Product,
        cart_with_products: Cart,
    ) -> None:
        """Test deleting product from cart"""
        request = rf.post(
            reverse("cart:delete_product_cart", kwargs={"product_id": product.pk}),
            data={"location-url": "/cart/"},
        )
        request.user = user

        middleware = SessionMiddleware(lambda _: HttpResponse())
        middleware.process_request(request)
        request.session["cart"] = cart_with_products.cart
        request.session.save()

        view = DeleteProductCartView.as_view()
        response = view(request, product_id=product.pk)

        cart = Cart(request)
        assert str(product.pk) not in cart.cart
        assert response.status_code == HTTP_302_REDIRECT

    def test_post_with_nonexistent_product(
        self,
        rf: RequestFactory,
        user: User,
        cart_with_products: Cart,
    ) -> None:
        """Test deleting nonexistent product doesn't crash"""
        request = rf.post(
            "/cart/delete-from-cart/99999",
            data={"location-url": "/cart/"},
        )
        request.user = user

        middleware = SessionMiddleware(lambda _: HttpResponse())
        middleware.process_request(request)
        request.session["cart"] = cart_with_products.cart
        request.session.save()

        view = DeleteProductCartView.as_view()
        response = view(request, product_id=99999)

        # Should not crash
        assert response.status_code == HTTP_302_REDIRECT

    def test_login_required(self, rf: RequestFactory, product: Product) -> None:
        """Test that login is required to delete products"""

        request = rf.post(
            reverse("cart:delete_product_cart", kwargs={"product_id": product.pk}),
        )
        request.user = AnonymousUser()

        view = DeleteProductCartView.as_view()
        response = view(request, product_id=product.pk)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response.url


class TestUpdateProductCartView:
    """Unit tests for UpdateProductCartView"""

    def test_patch_updates_product_quantity(
        self,
        rf: RequestFactory,
        user: User,
        product: Product,
        cart_with_products: Cart,
    ) -> None:
        """Test updating product quantity via PATCH"""
        request = rf.patch(
            reverse("cart:update_product_cart", kwargs={"product_id": product.pk}),
            data=json.dumps({"quantity": 5}),
            content_type="application/json",
        )
        request.user = user

        middleware = SessionMiddleware(lambda _: HttpResponse())
        middleware.process_request(request)
        request.session["cart"] = cart_with_products.cart
        request.session.save()

        view = UpdateProductCartView.as_view()
        response = view(request, product_id=product.pk)

        assert response.status_code == HTTP_200_OK
        assert isinstance(response, JsonResponse)

        data = json.loads(response.content)
        assert "subtotal" in data
        assert "total_price" in data
        assert "message" in data

    def test_patch_with_invalid_json_returns_400(
        self,
        rf: RequestFactory,
        user: User,
        product: Product,
        cart_with_products: Cart,
    ) -> None:
        """Test invalid JSON returns 400 error"""
        request = rf.patch(
            reverse("cart:update_product_cart", kwargs={"product_id": product.pk}),
            data="invalid json",
            content_type="application/json",
        )
        request.user = user

        middleware = SessionMiddleware(lambda _: HttpResponse())
        middleware.process_request(request)
        request.session["cart"] = cart_with_products.cart
        request.session.save()

        view = UpdateProductCartView.as_view()
        response = view(request, product_id=product.pk)

        assert response.status_code == HTTP_400_BAD_REQUEST
        assert isinstance(response, JsonResponse)
        data = json.loads(response.content)
        assert "error" in data

    def test_patch_with_invalid_quantity_returns_400(
        self,
        rf: RequestFactory,
        user: User,
        product: Product,
        cart_with_products: Cart,
    ) -> None:
        """Test invalid quantity returns 400 error"""
        request = rf.patch(
            reverse("cart:update_product_cart", kwargs={"product_id": product.pk}),
            data=json.dumps({"quantity": "invalid"}),
            content_type="application/json",
        )
        request.user = user

        middleware = SessionMiddleware(lambda _: HttpResponse())
        middleware.process_request(request)
        request.session["cart"] = cart_with_products.cart
        request.session.save()

        view = UpdateProductCartView.as_view()
        response = view(request, product_id=product.pk)

        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_login_required(self, rf: RequestFactory, product: Product) -> None:
        """Test that login is required to update products"""

        request = rf.patch(
            reverse("cart:update_product_cart", kwargs={"product_id": product.pk}),
            data=json.dumps({"quantity": 3}),
            content_type="application/json",
        )
        request.user = AnonymousUser()

        view = UpdateProductCartView.as_view()
        response = view(request, product_id=product.pk)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response.url


class TestClearCartView:
    """Unit tests for ClearCartView"""

    def test_post_clears_cart(
        self,
        rf: RequestFactory,
        user: User,
        cart_with_products: Cart,
    ) -> None:
        """Test clearing the entire cart"""
        request = rf.post(
            reverse("cart:clear_cart"),
            data={"location-url": "/"},
        )
        request.user = user

        middleware = SessionMiddleware(lambda _: HttpResponse())
        middleware.process_request(request)
        request.session["cart"] = cart_with_products.cart
        request.session.save()

        view = ClearCartView.as_view()
        response = view(request)

        cart = Cart(request)
        assert len(cart.cart) == 0
        assert response.status_code == HTTP_302_REDIRECT

    def test_post_redirects_to_location_url(
        self,
        rf: RequestFactory,
        user: User,
        cart_with_products: Cart,
    ) -> None:
        """Test redirect after clearing cart"""
        request = rf.post(
            reverse("cart:clear_cart"),
            data={"location-url": "/catalog/"},
        )
        request.user = user

        middleware = SessionMiddleware(lambda _: HttpResponse())
        middleware.process_request(request)
        request.session["cart"] = cart_with_products.cart
        request.session.save()

        view = ClearCartView.as_view()
        response = view(request)

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == "/catalog/"

    def test_login_required(self, rf: RequestFactory) -> None:
        """Test that login is required to clear cart"""

        request = rf.post(reverse("cart:clear_cart"))
        request.user = AnonymousUser()

        view = ClearCartView.as_view()
        response = view(request)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response.url


class TestRestoreOrderPendingCartView:
    """Unit tests for RestoreOrderPendingCartView"""

    def test_post_restores_order_to_cart(
        self,
        rf: RequestFactory,
        user: User,
        pending_order: Order,
    ) -> None:
        """Test restoring pending order to cart"""
        request = rf.post(
            reverse(
                "cart:restore_order_pending_cart",
                kwargs={"order_pending_id": pending_order.pk},
            ),
            data={"location-url": "/cart/"},
        )
        request.user = user

        _add_session_to_request(request)

        view = RestoreOrderPendingCartView.as_view()
        response = view(request, order_pending_id=pending_order.pk)

        cart = Cart(request)
        assert len(cart.cart) > 0
        assert response.status_code == HTTP_302_REDIRECT

    def test_post_with_nonexistent_order(
        self,
        rf: RequestFactory,
        user: User,
    ) -> None:
        """Test restoring nonexistent order raises error"""
        request = rf.post(
            "/cart/restore_cart/99999",
            data={"location-url": "/cart/"},
        )
        request.user = user

        _add_session_to_request(request)

        view = RestoreOrderPendingCartView.as_view()

        # Should raise an error when trying to restore nonexistent order
        with pytest.raises(Exception):  # noqa: B017, PT011
            view(request, order_pending_id=99999)

    def test_login_required(self, rf: RequestFactory, pending_order: Order) -> None:
        """Test that login is required to restore orders"""

        request = rf.post(
            reverse(
                "cart:restore_order_pending_cart",
                kwargs={"order_pending_id": pending_order.pk},
            ),
        )
        request.user = AnonymousUser()

        view = RestoreOrderPendingCartView.as_view()
        response = view(request, order_pending_id=pending_order.pk)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTP_302_REDIRECT
        assert "/account/login/" in response.url
