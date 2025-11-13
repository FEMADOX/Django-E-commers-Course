from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.contrib.auth.models import User

from account.models import Client

if TYPE_CHECKING:
    from django.test.client import Client as DjangoClient


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
def client_data(user_data: dict[str, str | int]) -> dict[str, str | int]:
    """Sample client data for testing."""

    return {
        "name": user_data["username"],
        "last_name": "User",
        "email": user_data["email"],
        "dni": 12345678,
        "sex": "M",
        "phone": "+12125552368",
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
        dni=12345678,
        sex="M",
        phone="+12125552368",
        address="123 Test Street",
    )
