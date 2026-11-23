import uuid

import pytest
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection

from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


def test_create_user_normalizes_phone_and_hashes_password() -> None:
    user = User.objects.create_user(
        phone="0300 1234567", password=DEFAULT_PASSWORD, full_name="Ayesha Khan"
    )

    user.refresh_from_db()
    assert user.phone == "+923001234567"
    assert user.password != DEFAULT_PASSWORD
    assert user.check_password(DEFAULT_PASSWORD)
    assert user.id.version == 7
    assert not user.is_staff
    assert not user.is_superuser


def test_create_user_without_password_cannot_log_in_with_one() -> None:
    user = User.objects.create_user(phone="03001234567", full_name="Ayesha Khan")

    assert not user.has_usable_password()


def test_create_superuser_grants_admin_flags() -> None:
    user = User.objects.create_superuser(
        phone="03001234567", password=DEFAULT_PASSWORD, full_name="Ali Zain"
    )

    assert user.is_staff
    assert user.is_superuser


def test_create_user_rejects_invalid_phone() -> None:
    with pytest.raises(ValidationError) as error:
        User.objects.create_user(phone="042 35761234", full_name="Ayesha Khan")

    assert "phone" in error.value.message_dict


def test_create_user_rejects_phone_already_registered_in_another_spelling() -> None:
    UserFactory.create(phone="+923001234567")

    with pytest.raises(ValidationError) as error:
        User.objects.create_user(phone="0300-1234567", full_name="Ayesha Khan")

    assert "phone" in error.value.message_dict


def test_database_rejects_unnormalized_phone() -> None:
    with pytest.raises(IntegrityError), connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO accounts_user (id, phone, full_name, email, password, is_active,"
            " is_staff, is_superuser, created_at, updated_at)"
            " VALUES (%s, %s, %s, '', '', true, false, false, now(), now())",
            [uuid.uuid7(), "03001234567", "Ayesha Khan"],
        )


def test_phone_lookups_accept_any_common_spelling() -> None:
    user = UserFactory.create(phone="+923001234567")

    assert User.objects.get(phone="0300 1234567") == user


@pytest.mark.parametrize("spelling", ["03001234567", "0300 1234567", "+92 300 1234567"])
def test_authenticates_with_any_common_phone_spelling(spelling: str) -> None:
    user = UserFactory.create(phone="+923001234567")

    assert authenticate(phone=spelling, password=DEFAULT_PASSWORD) == user


def test_authentication_rejects_wrong_password() -> None:
    UserFactory.create(phone="+923001234567")

    assert authenticate(phone="03001234567", password="wrong-password") is None


def test_authentication_rejects_malformed_phone() -> None:
    UserFactory.create(phone="+923001234567")

    assert authenticate(phone="not-a-phone", password=DEFAULT_PASSWORD) is None


def test_authentication_rejects_inactive_user() -> None:
    UserFactory.create(phone="+923001234567", is_active=False)

    assert authenticate(phone="03001234567", password=DEFAULT_PASSWORD) is None
