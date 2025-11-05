from __future__ import annotations

import hashlib
import time
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from account.forms import CustomPasswordResetForm, SmartAuthenticationForm
from account.models import Client
from account.views import AccountActivationView, CustomPasswordResetConfirmView
from tests.common.parametrizes import (
    PARAM_EMPTY_SPACES,
    PARAM_INVALID_EMAIL,
    PARAM_INVALID_PASSWORD_V1,
    PARAM_INVALID_PASSWORD_V2,
    PARAM_PASSWORD_NOT_MATCH,
    PARAM_PASSWORD_TOO_SHORT,
)
from tests.common.status import (
    HTTP_200_OK,
    HTTP_302_REDIRECT,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from django.forms import Form
    from django.test.client import Client as DjangoClient
    from django.test.client import _MonkeyPatchedWSGIResponse


@pytest.mark.unit
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
@pytest.mark.unit
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
@pytest.mark.unit
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

    @pytest.mark.parametrize(
        ("test_case", "data", "expected_message"),
        [
            PARAM_INVALID_EMAIL,
            PARAM_PASSWORD_NOT_MATCH,
            PARAM_PASSWORD_TOO_SHORT,
            PARAM_EMPTY_SPACES,
            PARAM_INVALID_PASSWORD_V1,
            PARAM_INVALID_PASSWORD_V2,
        ],
    )
    def test_signup_view_post_invalid_data(
        self,
        client: DjangoClient,
        test_case: str,
        data: dict[str, str],
        expected_message: str | list[str],
    ) -> None:
        """Test POST request with invalid signup data."""

        response = client.post(reverse("account:signup"), data)

        assert response.status_code == HTTP_200_OK

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        form: Form = response.context["form"]

        message_found = False
        all_error_text = []

        if messages:
            all_error_text.append(" ".join(str(m) for m in messages))

        if form.errors:
            # Add all form errors to list for easier debugging
            for field_errors in form.errors.values():
                all_error_text.extend(str(error) for error in field_errors)
            # Also check non-field errors
            if form.non_field_errors():
                all_error_text.append(
                    " ".join(str(error) for error in form.non_field_errors()),
                )
        if isinstance(expected_message, str):
            message_found = any(expected_message in text for text in all_error_text)
        elif isinstance(expected_message, list):
            message_found = all(
                any(expected in text for text in all_error_text)
                for expected in expected_message
            )

        assert message_found, (
            f"Expected message '{expected_message}' not found in case '{test_case}'\n"
            f"All error texts: {all_error_text}\n"
            f"Form errors: {dict(form.errors) if form.errors else 'No form errors'}\n"
            f"Django messages: {[str(message) for message in messages]}"
        )

        assert any("SignUp Failed" in str(m) for m in messages)


class TestUserLogoutView:
    """Tests for UserLogoutView."""

    def test_logout_view_requires_post(
        self,
        authenticated_client: DjangoClient,
    ) -> None:
        """Test that logout view only allows POST requests."""

        response = authenticated_client.get(reverse("account:logout"))

        assert response.status_code == HTTP_405_METHOD_NOT_ALLOWED

    def test_logout_view_post_requires_authentication(
        self,
        client: DjangoClient,
    ) -> None:
        """Test that logout view requires authentication."""

        response = client.post(reverse("account:logout"))

        assert response.status_code == HTTP_302_REDIRECT
        assert "login" in response["Location"]

    def test_logout_view_post(
        self,
        authenticated_client: DjangoClient,
    ) -> None:
        """Test POST request to logout view."""

        response = authenticated_client.post(reverse("account:logout"))

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("account:login")

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any("logged out successfully" in str(m) for m in messages)


@pytest.mark.django_db
@pytest.mark.unit
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
            response,
            email,
            "Token Mismatch",
        )


@pytest.mark.unit
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
@pytest.mark.unit
class TestEmailActivationView:
    """Tests for EmailActivationView."""

    @pytest.fixture
    def mock_time(self) -> int:
        return 1_000_000

    @pytest.fixture
    def pending_registration(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
        mock_time: int,
    ) -> None:
        # Set up pending registration
        session = client.session
        session["pending_registration"] = {
            "email": user_data["email"],
            "timestamp": mock_time,
        }
        session.save()

    def test_email_activation_view_get(
        self,
        client: DjangoClient,
        mock_time: int,
    ) -> None:
        """Test GET request to email activation view."""

        with patch("time.time", return_value=mock_time):
            response = client.get(reverse("account:email_validation"))
            assert response.status_code == HTTP_200_OK

        assert "account/activation/account_activation.html" in [
            t.name for t in response.templates
        ]

    @patch("account.views.send_account_activation_email")
    def test_email_activation_view_post(
        self,
        mock_send_email: MagicMock,
        client: DjangoClient,
        user_data: dict[str, str],
        mock_time: int,
        pending_registration: None,
    ) -> None:
        """Test POST request to resend activation email."""

        with patch("time.time", return_value=mock_time + 60):
            response = client.post(reverse("account:email_validation"))
            assert response.status_code == HTTP_200_OK

        # Check that email sending was called
        mock_send_email.assert_called_once_with(
            response.wsgi_request,
            user_data["email"],
        )

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any(
            "Email re-sent successfully. Please check your inbox." in str(m)
            for m in messages
        )

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
        assert any("Please start the registration process." in str(m) for m in messages)

    def test_email_activation_view_post_no_waiting_time(
        self,
        client: DjangoClient,
        mock_time: int,
        pending_registration: None,
    ) -> None:
        """Test POST request to resend activation email without waiting time."""

        with patch("time.time", return_value=mock_time + 30):
            response = client.post(reverse("account:email_validation"))
            assert response.status_code == HTTP_200_OK

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any(
            "Please wait before requesting another email." in str(m) for m in messages
        )


@pytest.mark.django_db
@pytest.mark.unit
class TestPasswordResetViews:
    """Tests for password reset views."""

    def test_password_reset_view_get(self, client: DjangoClient) -> None:
        """Test GET request to password reset view."""

        response = client.get(reverse("account:password_reset"))

        assert response.status_code == HTTP_200_OK
        assert "account/password/reset.html" in [t.name for t in response.templates]
        assert response.context["form"]

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

    def test_password_reset_view_form_class(
        self,
        client: DjangoClient,
    ) -> None:
        """Test that CustomPasswordResetForm is used."""

        response = client.get(reverse("account:password_reset"))

        assert isinstance(response.context["form"], CustomPasswordResetForm)

    def test_password_reset_view_template_name(
        self,
        client: DjangoClient,
    ) -> None:
        """Test that correct template is used."""

        response = client.get(reverse("account:password_reset"))

        assert "account/password/reset.html" in [t.name for t in response.templates]

    def test_password_reset_view_success_url(
        self,
        client: DjangoClient,
        authenticated_user: User,
        user_data: dict[str, str],
    ) -> None:
        """Test that success URL is correct."""

        response = client.post(
            reverse("account:password_reset"),
            {"email": user_data["email"]},
        )

        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == "/account/password-reset/done/"


@pytest.mark.django_db
@pytest.mark.unit
class TestPasswordResetDoneView:
    """Tests for CustomPasswordResetDoneView."""

    def test_password_reset_done_view_get(self, client: DjangoClient) -> None:
        """Test GET request to password reset done view."""

        response = client.get(reverse("account:password_reset_done"))

        assert response.status_code == HTTP_200_OK
        template_names = [t.name for t in response.templates]
        assert "account/password/reset_done.html" in template_names

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

    def test_password_reset_done_view_template_name(
        self,
        client: DjangoClient,
    ) -> None:
        """Test that correct template is used."""

        response = client.get(reverse("account:password_reset_done"))

        template_names = [t.name for t in response.templates]
        assert "account/password/reset_done.html" in template_names

    @patch("account.views.send_password_reset_email")
    def test_password_reset_done_view_post_email_sent_message(
        self,
        mock_send_email: MagicMock,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test that email sending function is called with correct parameters."""

        # Set up session
        session = client.session
        session["password_reset_email"] = user_data["email"]
        session.save()

        response = client.post(reverse("account:password_reset_done"))

        # Verify the email sending function was called with correct request and email
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        # first positional arg (request)
        assert call_args[0][0] == response.wsgi_request
        # keyword arg (email)
        assert call_args[1]["email"] == user_data["email"]


@pytest.mark.django_db
@pytest.mark.unit
class TestUserAccountViewAdditional:
    """Additional unit tests for UserAccountView."""

    def test_account_view_context_data(
        self,
        authenticated_client: DjangoClient,
    ) -> None:
        """Test that get_context_data includes form."""

        response = authenticated_client.get(reverse("account:user_account"))

        assert response.status_code == HTTP_200_OK
        assert "form" in response.context
        assert response.context["form"] is not None

    def test_account_view_user_query(
        self,
        authenticated_client: DjangoClient,
        authenticated_user: User,
    ) -> None:
        """Test that the view queries the correct user."""

        response = authenticated_client.get(reverse("account:user_account"))

        assert response.status_code == HTTP_200_OK
        # The view should get the user from request.user.pk
        form = response.context["form"]
        assert form.data.get("email") == authenticated_user.email


@pytest.mark.django_db
@pytest.mark.unit
class TestUserSignupViewAdditional:
    """Additional unit tests for UserSignupView."""

    def test_signup_view_get_form_kwargs(
        self,
        client: DjangoClient,
    ) -> None:
        """Test that get_form_kwargs includes is_signup=True."""

        response = client.get(reverse("account:signup"))

        assert response.status_code == HTTP_200_OK
        # The form should be initialized with is_signup=True
        form = response.context["form"]
        assert hasattr(form, "is_signup")

    def test_signup_view_model_and_success_url(
        self,
        client: DjangoClient,
    ) -> None:
        """Test model and success_url configuration."""

        response = client.get(reverse("account:signup"))

        assert response.status_code == HTTP_200_OK
        # Just verify the view is accessible and uses correct template
        assert "account/signup.html" in [t.name for t in response.templates]

    def test_signup_view_session_timestamp(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test that session includes timestamp."""
        with patch("account.views.send_account_activation_email"):
            signup_data = {
                "email": user_data["email"],
                "password": user_data["password"],
                "password_confirm": user_data["password"],
            }

            response = client.post(reverse("account:signup"), signup_data)

            assert response.status_code == HTTP_302_REDIRECT
            pending = client.session["pending_registration"]
            assert "timestamp" in pending
            assert isinstance(pending["timestamp"], int)


@pytest.mark.django_db
@pytest.mark.unit
class TestAccountActivationViewAdditional:
    """Additional unit tests for AccountActivationView."""

    def test_activation_view_http_methods(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test that only GET method is allowed."""

        uidb64 = urlsafe_base64_encode(force_bytes(user_data["email"]))
        token = hashlib.sha256(user_data["email"].encode()).hexdigest()
        url = reverse(
            "account:account_activation",
            kwargs={"uidb64": uidb64, "token": token},
        )

        # GET should work (even if it fails due to no pending registration)
        response = client.get(url)
        assert response.status_code == HTTP_302_REDIRECT

        # POST should not be allowed
        response = client.post(url)
        assert response.status_code == HTTP_405_METHOD_NOT_ALLOWED

    def test_activation_view_success_url_and_failed_url(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test success_url and failed_url attributes."""

        # Test failed_url (when no pending registration)
        uidb64 = urlsafe_base64_encode(force_bytes(user_data["email"]))
        token = hashlib.sha256(user_data["email"].encode()).hexdigest()
        url = reverse(
            "account:account_activation",
            kwargs={"uidb64": uidb64, "token": token},
        )

        response = client.get(url)
        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == reverse("account:login")

    def test_activation_view_token_expiration_constant(
        self,
        client: DjangoClient,
        user_data: dict[str, str],
    ) -> None:
        """Test token expiration is set correctly."""

        view = AccountActivationView()
        # Should be 24 hours in seconds
        assert view.token_expiration == 24 * 60 * 60

    def test_activation_view_backend_attribute(
        self,
        client: DjangoClient,
    ) -> None:
        """Test authentication backend is set correctly."""

        view = AccountActivationView()
        expected_backend = "django.contrib.auth.backends.ModelBackend"
        assert view.backend == expected_backend


@pytest.mark.django_db
@pytest.mark.unit
class TestUserLoginViewAdditional:
    """Additional unit tests for UserLoginView."""

    def test_login_view_redirect_authenticated_user(
        self,
        authenticated_client: DjangoClient,
    ) -> None:
        """Test redirect_authenticated_user attribute."""

        response = authenticated_client.get(reverse("account:login"))

        assert response.status_code == HTTP_302_REDIRECT

    def test_login_view_form_class(
        self,
        client: DjangoClient,
    ) -> None:
        """Test that correct form class is used."""

        response = client.get(reverse("account:login"))

        assert isinstance(response.context["form"], SmartAuthenticationForm)

    def test_login_view_get_form_kwargs(
        self,
        client: DjangoClient,
    ) -> None:
        """Test that get_form_kwargs includes is_signup=False."""

        response = client.get(reverse("account:login"))

        assert response.status_code == HTTP_200_OK
        # The form should be initialized with is_signup=False
        form = response.context["form"]
        assert hasattr(form, "is_signup")


@pytest.mark.django_db
@pytest.mark.unit
class TestEmailActivationViewAdditional:
    """Additional unit tests for EmailActivationView."""

    def test_email_activation_view_csrf_protection(
        self,
        client: DjangoClient,
    ) -> None:
        """Test that view has CSRF protection."""

        response = client.get(reverse("account:email_validation"))

        assert response.status_code == HTTP_200_OK
        # CSRF token should be in the response
        assert "csrfmiddlewaretoken" in response.content.decode()

    def test_email_activation_view_template_name(
        self,
        client: DjangoClient,
    ) -> None:
        """Test correct template is used."""

        response = client.get(reverse("account:email_validation"))

        template_name = "account/activation/account_activation.html"
        assert template_name in [t.name for t in response.templates]


@pytest.mark.django_db
@pytest.mark.unit
class TestCustomPasswordResetConfirmView:
    """Tests for CustomPasswordResetConfirmView."""

    @pytest.fixture
    def password_reset_data(self, authenticated_user: User) -> dict[str, str]:
        """Create password reset data for testing."""

        return {
            "new_password1": "NewTestPassword123!",
            "new_password2": "NewTestPassword123!",
        }

    @pytest.fixture
    def uidb64_token_data(self, authenticated_user: User) -> dict[str, str]:
        """Create uidb64 and token for password reset confirmation."""

        uidb64 = urlsafe_base64_encode(force_bytes(authenticated_user.email))
        token = default_token_generator.make_token(authenticated_user)

        return {
            "uidb64": uidb64,
            "token": token,
        }

    @pytest.fixture
    def confirm_set_password_url(
        self,
        client: DjangoClient,
        uidb64_token_data: dict[str, str],
    ) -> str:
        """Helper to generate password reset confirm URL."""

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64_token_data["uidb64"],
                    "token": uidb64_token_data["token"],
                },
            ),
            follow=True,
        )
        return response.wsgi_request.path

    def test_password_reset_confirm_view_get_valid_token(
        self,
        client: DjangoClient,
        authenticated_user: User,
        uidb64_token_data: dict[str, str],
    ) -> None:
        """Test GET request to password reset confirm view with valid token."""

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64_token_data["uidb64"],
                    "token": uidb64_token_data["token"],
                },
            ),
            follow=True,
        )

        assert response.status_code == HTTP_200_OK
        assert "account/password/reset_confirm.html" in [
            t.name for t in response.templates
        ]
        assert response.context["form"]

    def test_password_reset_confirm_view_get_invalid_token(
        self,
        client: DjangoClient,
        authenticated_user: User,
        uidb64_token_data: dict[str, str],
    ) -> None:
        """Test GET request with invalid token."""

        # Test with invalid uidb64
        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": "invalid-uidb64",
                    "token": uidb64_token_data["token"],
                },
            ),
            follow=True,
        )

        assert response.status_code == HTTP_200_OK

        # Should show error form or redirect to log in
        assert "account/login.html" in [t.name for t in response.templates]

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("link is invalid (uidb64 invalid!)" in str(m) for m in messages)

        # =============================================================================

        # Test with invalid token
        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64_token_data["uidb64"],
                    "token": "invalid-token",
                },
            ),
            follow=True,
        )

        assert response.status_code == HTTP_200_OK

        # Should show error form or redirect to log in
        assert "account/login.html" in [t.name for t in response.templates]

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("link is invalid (token invalid!)" in str(m) for m in messages)

    def test_password_reset_confirm_view_post_valid_data(
        self,
        client: DjangoClient,
        authenticated_user: User,
        password_reset_data: dict[str, str],
        confirm_set_password_url: str,
    ) -> None:
        """Test POST request with valid password reset data."""

        # Set up session data
        session = client.session
        session["password_reset_email"] = authenticated_user.email
        session.save()

        response = client.post(confirm_set_password_url, password_reset_data)

        # Verify redirect to login page
        assert response.status_code == HTTP_302_REDIRECT
        assert response["Location"] == "/account/login/"

        # Verify password was changed
        authenticated_user.refresh_from_db()
        assert authenticated_user.check_password(password_reset_data["new_password1"])

        # Verify session was cleared
        assert "password_reset_email" not in client.session

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        assert any("Password has been reset successfully" in str(m) for m in messages)

    def test_password_reset_confirm_view_post_invalid_passwords_mismatch(
        self,
        client: DjangoClient,
        authenticated_user: User,
        confirm_set_password_url: str,
    ) -> None:
        """Test POST request with mismatched passwords."""

        invalid_data = {
            "new_password1": "NewTestPassword123!",
            "new_password2": "DifferentPassword123!",  # Mismatch
        }

        response = client.post(confirm_set_password_url, invalid_data)

        assert response.status_code == HTTP_200_OK

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("Error resetting password" in str(m) for m in messages)

        # Check password mismatch error in form
        form: Form = response.context["form"]
        assert form.errors
        assert not form.is_valid()
        assert any(
            "The two password fields didn\u2019t match." in str(error)
            for field_errors in form.errors.values()
            for error in field_errors
        )

    def test_password_reset_confirm_view_post_weak_password(
        self,
        client: DjangoClient,
        authenticated_user: User,
        uidb64_token_data: dict[str, str],
        confirm_set_password_url: str,
    ) -> None:
        """Test POST request with weak password."""

        weak_password_data = {
            "new_password1": "123",  # Too weak
            "new_password2": "123",
        }

        response = client.post(confirm_set_password_url, weak_password_data)

        assert response.status_code == HTTP_200_OK

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        assert any("Error resetting password" in str(m) for m in messages)

        # Check password mismatch error in form
        form: Form = response.context["form"]
        assert form.errors
        assert not form.is_valid()

        assert any(
            "Ensure this value has at least 8 characters" in str(error)
            for field_errors in form.errors.values()
            for error in field_errors
        )

    def test_get_user_method_valid_email(
        self,
        client: DjangoClient,
        authenticated_user: User,
    ) -> None:
        """Test get_user method with valid email."""

        uidb64 = urlsafe_base64_encode(force_bytes(authenticated_user.email))
        view = CustomPasswordResetConfirmView()

        user = view.get_user(uidb64)

        assert user == authenticated_user
        assert user is not None
        assert hasattr(user, "email")
        # Type ignore needed because AbstractBaseUser doesn't have email attribute
        assert user.email == authenticated_user.email  # type: ignore[attr-defined]

    def test_get_user_method_invalid_email(
        self,
        client: DjangoClient,
    ) -> None:
        """Test get_user method with invalid email."""

        uidb64 = urlsafe_base64_encode(force_bytes("nonexistent@example.com"))
        view = CustomPasswordResetConfirmView()

        user = view.get_user(uidb64)

        assert user is None
