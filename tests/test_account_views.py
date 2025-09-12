from __future__ import annotations

import hashlib
import time
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from account.models import Client
from tests.status import HTTP_200_OK, HTTP_302_REDIRECT, HTTP_404_NOT_FOUND

if TYPE_CHECKING:
    from collections.abc import Mapping

    from django.forms import Form
    from django.test.client import Client as DjangoClient
    from django.test.client import _MonkeyPatchedWSGIResponse


@pytest.fixture
def user_data() -> dict[str, str]:
    """Sample user data for testing."""
    email = "testuser@example.com"
    return {
        "username": email.split("@", maxsplit=1)[0],
        "email": email,
        "password": "TestPassword123!",
    }


@pytest.fixture
def client_data(user_data: dict[str, str]) -> dict[str, str]:
    """Sample client data for testing."""
    return {
        "name": user_data["username"],
        "last_name": "User",
        "email": user_data["email"],
        "dni": "12345678",
        "sex": "M",
        "phone": "123456789",
        "birth": "1990-01-01",
        "address": "123 Test Street",
    }


@pytest.fixture
def authenticated_user(db: None, user_data: dict[str, str]) -> User:  # noqa: ARG001
    """Create and return an authenticated user."""
    return User.objects.create_user(
        username=user_data["username"],
        email=user_data["email"],
        password=user_data["password"],
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name", ""),
    )


@pytest.fixture
def authenticated_client(
    authenticated_user: User,
    client: DjangoClient,
) -> DjangoClient:
    """Return a client with authenticated user."""
    client.force_login(authenticated_user)
    return client


@pytest.fixture
def client_profile(authenticated_user: User) -> Client:
    """Create and return a client profile."""
    return Client.objects.create(
        user=authenticated_user,
        dni="12345678",
        sex="M",
        phone="123456789",
        address="123 Test Street",
    )


class TestUserAccountView:
    """Tests for UserAccountView."""

    @staticmethod
    def authenticated_client_form_data(
        authenticated_client: DjangoClient,
    ) -> Mapping[str, Any]:
        response = authenticated_client.get(reverse("account:user_account"))

        assert response.status_code == HTTP_200_OK
        assert "account/account.html" in [t.name for t in response.templates]
        assert response.context["form"]

        # Check that form has complete user and client data
        form: Form = response.context["form"]
        assert form.is_bound  # Form is bound with data
        return form.data

    def test_account_view_requires_login(self, client: DjangoClient) -> None:
        """Test that account view requires authentication."""
        response = client.get(reverse("account:user_account"))

        assert response.status_code == HTTP_302_REDIRECT
        assert "login" in response["Location"]

    def test_account_view_with_authenticated_user_no_profile(
        self,
        authenticated_client: DjangoClient,
        authenticated_user: User,
    ) -> None:
        """Test account view with authenticated user but no client profile."""
        form_data = self.authenticated_client_form_data(authenticated_client)

        assert form_data["name"] == authenticated_user.username
        assert form_data["email"] == authenticated_user.email

    def test_account_view_with_authenticated_user_and_profile(
        self,
        authenticated_client: DjangoClient,
        authenticated_user: User,
        client_profile: Client,
    ) -> None:
        """Test account view with authenticated user and client profile."""
        form_data = self.authenticated_client_form_data(authenticated_client)

        assert form_data["name"] == authenticated_user.username
        assert form_data["last_name"] == authenticated_user.last_name
        assert form_data["email"] == authenticated_user.email
        assert form_data["dni"] == client_profile.dni
        assert form_data["sex"] == client_profile.sex
        assert form_data["phone"] == client_profile.phone
        assert form_data["address"] == client_profile.address


@pytest.mark.django_db
class TestUserUpdateView:
    """Tests for UserUpdateView."""

    def test_update_view_requires_login(self, client: DjangoClient) -> None:
        """Test that update view requires authentication."""
        response = client.get(reverse("account:update_account"))

        assert response.status_code == HTTP_302_REDIRECT
        assert "login" in response["Location"]

    def test_update_view_without_client_profile_404(
        self,
        authenticated_client: DjangoClient,
    ) -> None:
        """Test update view returns 404 when no client profile exists."""
        response = authenticated_client.get(reverse("account:update_account"))

        assert response.status_code == HTTP_404_NOT_FOUND

    def test_update_view_get_with_client_profile(
        self,
        authenticated_client: DjangoClient,
        client_profile: Client,
    ) -> None:
        """Test GET request to update view with existing client profile."""
        response = authenticated_client.get(reverse("account:update_account"))

        assert response.status_code == HTTP_200_OK
        assert "account/account.html" in [t.name for t in response.templates]

    def test_update_view_post_valid_data(
        self,
        authenticated_client: DjangoClient,
        authenticated_user: User,
        client_profile: Client,
        client_data: dict[str, str],
    ) -> None:
        """Test POST request with valid data updates user and client."""
        updated_data = client_data.copy()
        updated_data.update(
            {
                "name": "Updated",
                "last_name": "Name",
                "email": "updated@example.com",
                "phone": "987654321",
            },
        )

        response = authenticated_client.post(
            reverse("account:update_account"),
            updated_data,
        )

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == "/account/"

        # Verify user was updated
        authenticated_user.refresh_from_db()
        assert authenticated_user.username == "Updated"
        assert authenticated_user.last_name == "Name"
        assert authenticated_user.email == "updated@example.com"

        # Verify client was updated
        client_profile.refresh_from_db()
        assert client_profile.phone == "987654321"

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any("data has been updated" in str(m) for m in messages)

    def test_update_view_post_invalid_data(
        self,
        authenticated_client: DjangoClient,
        client_profile: Client,
    ) -> None:
        """Test POST request with invalid data shows error."""
        invalid_data = {
            "name": "",  # Required field empty
            "email": "invalid-email",  # Invalid email format
        }

        response = authenticated_client.post(
            reverse("account:update_account"),
            invalid_data,
        )

        assert response.status_code == HTTP_200_OK

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("Update failed" in str(m) for m in messages)


@pytest.mark.django_db
class TestUserSignupView:
    """Tests for UserSignupView."""

    def test_signup_view_get(self, client: DjangoClient) -> None:
        """Test GET request to signup view."""
        response = client.get(reverse("account:signup"))

        assert response.status_code == HTTP_200_OK
        assert "account/signup.html" in [t.name for t in response.templates]
        assert response.context["form"]

    def test_signup_view_authenticated_user_redirected(
        self,
        authenticated_client: DjangoClient,
    ) -> None:
        """Test that authenticated users are redirected from signup."""
        response = authenticated_client.get(reverse("account:signup"))

        assert response.status_code == HTTP_302_REDIRECT

    @patch("account.views.send_account_activation_email")
    def test_signup_view_post_valid_data(
        self,
        mock_send_email: MagicMock,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test POST request with valid signup data."""
        signup_data = {
            "email": user_data["email"],
            "password": user_data["password"],
            "password_confirm": user_data["password"],
        }

        response = client.post(reverse("account:signup"), signup_data)

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("account:email_validation")

        # Check that email sending was called
        mock_send_email.assert_called_once_with(
            response.wsgi_request,
            user_data["email"],
        )

        # Check session data
        session = client.session
        assert "pending_registration" in session
        pending = session["pending_registration"]
        assert pending["email"] == user_data["email"]
        assert pending["password"] == user_data["password"]
        assert "timestamp" in pending

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any("sent an email" in str(m) for m in messages)

    def test_signup_view_post_invalid_data(
        self,
        client: DjangoClient,
    ) -> None:
        """Test POST request with invalid signup data."""
        invalid_data = {
            "email": "invalid-email",
            "password": "weak",
            "password_confirm": "different",
        }

        response = client.post(reverse("account:signup"), invalid_data)

        assert response.status_code == HTTP_200_OK

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("SignUp Failed" in str(m) for m in messages)


@pytest.mark.django_db
class TestAccountActivationView:
    """Tests for AccountActivationView."""

    @pytest.fixture
    def pending_registration(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> dict[str, str | int]:
        """Set up pending registration in session."""
        session = client.session
        pending = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"],
            "timestamp": int(time.time()),
        }
        session["pending_registration"] = pending
        session.save()
        return pending

    @staticmethod
    def account_email_activation(
        email: str,
        client: DjangoClient,
    ) -> _MonkeyPatchedWSGIResponse:
        uidb64 = urlsafe_base64_encode(force_bytes(email))
        token = hashlib.sha256(email.encode()).hexdigest()

        return client.get(
            reverse(
                "account:account_activation",
                kwargs={"uidb64": uidb64, "token": token},
            ),
        )

    @staticmethod
    def assert_activation_error_redirect(
        response: _MonkeyPatchedWSGIResponse,
        email: str,
        expected_message: str,
    ) -> None:
        """Assert common behavior for activation errors."""
        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("account:login")

        # Check user was not created
        assert not User.objects.filter(email=email).exists()

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any(expected_message in str(m) for m in messages)

    def test_activation_view_valid_token(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
        pending_registration: dict[str, str | int],
    ) -> None:
        """Test account activation with valid token."""
        email = user_data["email"]

        response = self.account_email_activation(email, client)

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("account:user_account")

        # Check user was created
        assert User.objects.filter(email=email).exists()
        user = User.objects.get(email=email)
        assert user.username == user_data["username"]
        assert user.is_active

        # Check client profile was created
        assert Client.objects.filter(user=user).exists()

        # Check pending registration was removed from session
        assert "pending_registration" not in client.session

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any("Account activated successfully!" in str(m) for m in messages)

    def test_activation_view_invalid_token_no_pending_data(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test account activation with invalid token without pending data"""
        email = user_data["email"]
        response = self.account_email_activation(email, client)

        self.assert_activation_error_redirect(
            response,
            email,
            "Pending Registration Not Found",
        )

    def test_activation_view_invalid_token_mismatch(
        self,
        client: DjangoClient,
        pending_registration: dict[str, str | int],
    ) -> None:
        """Test account activation with invalid token. Email mismatch."""
        email = "invalid_email@gmail.com"
        response = self.account_email_activation(email, client)

        self.assert_activation_error_redirect(
            response,
            email,
            "Pending Registration Email Mismatch",
        )

    def test_activation_view_invalid_token_no_timestamp(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test account activation with invalid token. Pending data has no timestamp."""
        email = user_data["email"]

        # Set up no timestamp pending registration
        session = client.session
        pending = {
            "username": user_data["username"],
            "email": email,
            "password": user_data["password"],
        }
        session["pending_registration"] = pending
        session.save()

        response = self.account_email_activation(email, client)

        self.assert_activation_error_redirect(
            response,
            email,
            "Pending Registration Timestamp Not Found",
        )

    def test_activation_view_invalid_token_expired(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test account activation with invalid token. Token is expired."""
        # Set up expired pending registration
        session = client.session
        expired_timestamp = int(time.time()) - (25 * 60 * 60)  # 25 hours ago
        pending = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"],
            "timestamp": expired_timestamp,
        }
        session["pending_registration"] = pending
        session.save()

        email = user_data["email"]
        response = self.account_email_activation(email, client)

        self.assert_activation_error_redirect(
            response,
            email,
            "Activation link is invalid",
        )

    def test_activation_view_token_mismatch_specific(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
        pending_registration: dict[str, str | int],
    ) -> None:
        """Test specific line: Token Mismatch validation."""
        email = user_data["email"]

        # Create activation request with WRONG token (triggers the specific line)
        uidb64 = urlsafe_base64_encode(force_bytes(email))
        wrong_token = "wrong_token_that_wont_match_sha256_hash"
        response = client.get(
            reverse(
                "account:account_activation",
                kwargs={"uidb64": uidb64, "token": wrong_token},
            ),
        )

        self.assert_activation_error_redirect(
            response, email, "Token Mismatch",
        )


class TestUserLoginView:
    """Tests for UserLoginView."""

    def test_login_view_get(self, client: DjangoClient) -> None:
        """Test GET request to log in view."""
        response = client.get(reverse("account:login"))

        assert response.status_code == HTTP_200_OK
        assert "account/login.html" in [t.name for t in response.templates]
        assert response.context["form"]

    def test_login_view_authenticated_user_redirected(
        self,
        authenticated_client: DjangoClient,
    ) -> None:
        """Test that authenticated users are redirected from login."""
        response = authenticated_client.get(reverse("account:login"))

        assert response.status_code == HTTP_302_REDIRECT

    def test_login_view_post_valid_credentials(
        self,
        client: DjangoClient,
        authenticated_user: User,
        user_data: dict[str, str],
    ) -> None:
        """Test POST request with valid login credentials."""
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"],
        }

        response = client.post(reverse("account:login"), login_data)

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("account:user_account")

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any("Login successfully" in str(m) for m in messages)

    def test_login_view_post_invalid_credentials(
        self,
        client: DjangoClient,
        authenticated_user: User,
    ) -> None:
        """Test POST request with invalid login credentials."""
        invalid_data = {
            "email": "wrong@example.com",
            "password": "wrongpassword",
        }

        response = client.post(reverse("account:login"), invalid_data)

        assert response.status_code == HTTP_200_OK

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("Login failed" in str(m) for m in messages)


@pytest.mark.django_db
class TestEmailActivationView:
    """Tests for EmailActivationView."""

    def test_email_activation_view_get(self, client: DjangoClient) -> None:
        """Test GET request to email activation view."""
        response = client.get(reverse("account:email_validation"))

        assert response.status_code == HTTP_200_OK
        assert "account/activation/account_activation.html" in [
            t.name for t in response.templates
        ]

    @patch("account.views.send_account_activation_email")
    def test_email_activation_view_post_with_pending_registration(
        self,
        mock_send_email: MagicMock,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test POST request to resend activation email."""
        # Set up pending registration
        session = client.session
        session["pending_registration"] = {
            "email": user_data["email"],
            "timestamp": int(time.time()),
        }
        session.save()

        response = client.post(reverse("account:email_validation"))

        assert response.status_code == HTTP_200_OK

        # Check that email sending was called
        mock_send_email.assert_called_once_with(
            response.wsgi_request,
            user_data["email"],
        )

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any("re-sent successfully" in str(m) for m in messages)

    def test_email_activation_view_post_without_pending_registration(
        self,
        client: DjangoClient,
    ) -> None:
        """Test POST request without pending registration."""
        response = client.post(reverse("account:email_validation"))

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("account:signup")

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("start the registration" in str(m) for m in messages)


@pytest.mark.django_db
class TestPasswordResetViews:
    """Tests for password reset views."""

    def test_password_reset_view_get(self, client: DjangoClient) -> None:
        """Test GET request to password reset view."""
        response = client.get(reverse("account:password_reset"))

        assert response.status_code == HTTP_200_OK
        assert "account/password/reset.html" in [t.name for t in response.templates]

    def test_password_reset_view_post_valid_email(
        self,
        client: DjangoClient,
        authenticated_user: User,
        user_data: dict[str, str],
    ) -> None:
        """Test POST request with valid email."""
        response = client.post(
            reverse("account:password_reset"),
            {"email": user_data["email"]},
        )

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == "/account/password-reset/done/"

        # Check that email was stored in session
        assert client.session["password_reset_email"] == user_data["email"]

    def test_password_reset_view_post_invalid_email(
        self,
        client: DjangoClient,
    ) -> None:
        """Test POST request with non-existent email."""
        response = client.post(
            reverse("account:password_reset"),
            {"email": "nonexistent@example.com"},
        )

        assert response.status_code == HTTP_200_OK

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("No user found" in str(m) for m in messages)

    @patch("account.views.send_password_reset_email")
    def test_password_reset_done_view_post(
        self,
        mock_send_email: MagicMock,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test password reset done view POST request."""
        # Set up session
        session = client.session
        session["password_reset_email"] = user_data["email"]
        session.save()

        response = client.post(reverse("account:password_reset_done"))

        assert response.status_code == HTTP_200_OK

        # Check that email sending was called
        mock_send_email.assert_called_once_with(
            response.wsgi_request,
            email=user_data["email"],
        )

    def test_password_reset_done_view_post_no_session(
        self,
        client: DjangoClient,
    ) -> None:
        """Test password reset done view without session data."""
        response = client.post(reverse("account:password_reset_done"))

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("account:password_reset")

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("initiate the password reset" in str(m) for m in messages)
