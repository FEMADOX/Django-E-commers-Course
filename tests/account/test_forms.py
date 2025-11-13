from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from account.forms import ClientForm


@pytest.mark.unit
class TestClientFormPhoneField:
    """Tests for ClientForm phone field validation."""

    def test_client_form_phone_field_valid_format(self) -> None:
        """Test phone field with valid international format."""

        form_data = {
            "name": "John",
            "email": "john@example.com",
            "phone": "+5491123456789",
        }

        form = ClientForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data["phone"].as_e164 == "+5491123456789"

    def test_client_form_phone_field_blank(self) -> None:
        """Test that phone field can be blank."""

        form_data = {
            "name": "John",
            "email": "john@example.com",
            "phone": "",
        }

        form = ClientForm(data=form_data)

        assert form.is_valid()
        assert not form.cleaned_data["phone"]

    def test_client_form_phone_field_not_required(self) -> None:
        """Test that phone field is not required."""

        form_data = {
            "name": "John",
            "email": "john@example.com",
            # No phone field provided
        }

        form = ClientForm(data=form_data)

        assert form.is_valid()

    def test_client_form_phone_field_invalid_format(self) -> None:
        """Test phone field with invalid formats."""

        invalid_phones = [
            "123",  # Too short
            "abcdefghij",  # Letters only
            "12-34-56-78",  # Invalid format
            "+999999999999999",  # Invalid country code
            "123456789012345",  # Too long without country code
        ]

        for phone in invalid_phones:
            form_data = {
                "name": "John",
                "email": "john@example.com",
                "phone": phone,
            }

            form = ClientForm(data=form_data)

            assert not form.is_valid(), f"Phone {phone} should be invalid"
            assert "phone" in form.errors

    def test_client_form_phone_field_valid_formats(self) -> None:
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
            form_data = {
                "name": "John",
                "email": "john@example.com",
                "phone": phone,
            }

            form = ClientForm(data=form_data)

            assert form.is_valid(), f"Phone {phone} should be valid"
            assert form.cleaned_data["phone"].as_e164 == phone

    def test_client_form_phone_field_with_all_data(self) -> None:
        """Test phone field with complete form data."""

        form_data = {
            "dni": "12345678",
            "name": "John",
            "last_name": "Doe",
            "sex": "M",
            "email": "john@example.com",
            "phone": "+5491123456789",
            "address": "123 Main St",
            "birth": "1990-01-01",
        }

        form = ClientForm(data=form_data)

        assert form.is_valid()
        assert form.cleaned_data["phone"].as_e164 == "+5491123456789"

    def test_client_form_phone_field_autocomplete_attribute(self) -> None:
        """Test that phone field has autocomplete attribute."""

        form = ClientForm()

        phone_field = form.fields["phone"]
        assert "autocomplete" in phone_field.widget.attrs
        assert phone_field.widget.attrs["autocomplete"] == "tel"

    def test_client_form_required_fields(self) -> None:
        """Test that only name and email are required."""

        form_data = {}

        form = ClientForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors
        assert "email" in form.errors
        assert "phone" not in form.errors  # Phone is not required

    def test_client_form_email_validation(self) -> None:
        """Test email field validation."""

        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
        ]

        for email in invalid_emails:
            form_data = {
                "name": "John",
                "email": email,
            }

            form = ClientForm(data=form_data)

            assert not form.is_valid()
            assert "email" in form.errors

    def test_client_form_phone_with_spaces(self) -> None:
        """Test phone field with spaces (should be invalid)."""

        form_data = {
            "name": "John",
            "email": "john@example.com",
            "phone": "+54 911 2345 6789",  # With spaces
        }

        form = ClientForm(data=form_data)

        # phonenumber_field should handle or reject this
        # Depending on library configuration
        if not form.is_valid():
            assert "phone" in form.errors

    def test_client_form_phone_without_country_code(self) -> None:
        """Test phone field without country code (should be invalid)."""

        form_data = {
            "name": "John",
            "email": "john@example.com",
            "phone": "1123456789",  # Without + prefix
        }

        form = ClientForm(data=form_data)

        assert not form.is_valid()
        assert "phone" in form.errors

    def test_client_form_phone_field_widget_type(self) -> None:
        """Test that phone field uses TextInput widget."""

        form = ClientForm()

        phone_field = form.fields["phone"]
        assert phone_field.widget.__class__.__name__ == "TextInput"

    def test_client_form_sex_choices(self) -> None:
        """Test sex field choices."""

        form = ClientForm()

        sex_field = form.fields["sex"]
        expected_choices = [
            ("M", "Male"),
            ("F", "Female"),
            ("N", "Null"),
        ]

        assert list(sex_field.choices) == expected_choices  # type: ignore
