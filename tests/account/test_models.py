from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from account.models import Client

if TYPE_CHECKING:
    from django.contrib.auth.models import User


@pytest.mark.django_db
@pytest.mark.unit
class TestClientModelPhoneField:
    """Tests for Client model phone field validation."""

    def test_client_phone_field_valid_format(
        self,
        authenticated_user: User,
    ) -> None:
        """Test phone field with valid international format."""

        client = Client.objects.create(
            user=authenticated_user,
            dni=12345678,
            phone="+5491123456789",
        )

        assert str(client.phone) == "+5491123456789"

    def test_client_phone_field_blank(
        self,
        authenticated_user: User,
    ) -> None:
        """Test that phone field can be blank."""

        client = Client.objects.create(
            user=authenticated_user,
            dni=12345678,
            phone="",
        )

        assert not client.phone

    def test_client_phone_field_default_value(
        self,
        authenticated_user: User,
    ) -> None:
        """Test that phone field has correct default value."""

        client = Client.objects.create(user=authenticated_user)

        assert not client.phone

    def test_client_phone_field_multiple_valid_formats(
        self,
        authenticated_user: User,
    ) -> None:
        """Test various valid phone number formats from different countries."""

        valid_phones = [
            "+5491123456789",  # Argentina
            "+12025551234",  # USA
            "+442071234567",  # UK
            "+861012345678",  # China
            "+33123456789",  # France
            "+34912345678",  # Spain
            "+390612345678",  # Italy
        ]

        for phone in valid_phones:
            client = Client.objects.create(
                user=authenticated_user,
                dni=12345678,
                phone=phone,
            )
            assert str(client.phone) == phone
            client.delete()  # Clean up for next iteration

    def test_client_phone_field_update(
        self,
        authenticated_user: User,
    ) -> None:
        """Test updating phone field value."""

        client = Client.objects.create(
            user=authenticated_user,
            phone="+5491123456789",
        )

        # Update phone
        client.phone = "+12025551234"
        client.save()

        client.refresh_from_db()
        assert str(client.phone) == "+12025551234"

    def test_client_phone_field_not_null(
        self,
        authenticated_user: User,
    ) -> None:
        """Test that phone field is not null (null=False)."""

        client = Client.objects.create(
            user=authenticated_user,
            phone="",
        )

        # Phone should be empty string, not None
        assert not client.phone
        assert client.phone is not None

    def test_client_creation_with_all_fields(
        self,
        authenticated_user: User,
    ) -> None:
        """Test client creation with all fields including phone."""

        dni_number = 12345678
        client = Client.objects.create(
            user=authenticated_user,
            dni=dni_number,
            sex="M",
            phone="+5491123456789",
            address="123 Test Street",
        )

        assert client.user == authenticated_user
        assert client.dni == dni_number
        assert client.sex == "M"
        assert str(client.phone) == "+5491123456789"
        assert client.address == "123 Test Street"

    def test_client_str_representation(
        self,
        authenticated_user: User,
    ) -> None:
        """Test string representation of Client."""

        client = Client.objects.create(
            user=authenticated_user,
            dni=12345678,
            phone="+5491123456789",
        )

        expected_str = f"DNI: {client.dni} - User: {authenticated_user}"
        assert str(client) == expected_str

    def test_client_default_values(
        self,
        authenticated_user: User,
    ) -> None:
        """Test default values for Client fields."""

        client = Client.objects.create(user=authenticated_user)

        assert client.dni == 0
        assert client.sex == "N"
        assert not client.phone
        assert not client.address
        assert client.birth is None
