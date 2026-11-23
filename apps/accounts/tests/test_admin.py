import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.forms import UserCreationForm
from apps.accounts.models import User
from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client: Client) -> Client:
    client.force_login(UserFactory.create(is_staff=True, is_superuser=True))
    return client


def test_creation_form_normalizes_phone_and_sets_password() -> None:
    form = UserCreationForm(
        data={
            "phone": "0300 1234567",
            "full_name": "Ayesha Khan",
            "password1": DEFAULT_PASSWORD,
            "password2": DEFAULT_PASSWORD,
        }
    )

    assert form.is_valid(), form.errors
    user = form.save()
    assert user.phone == "+923001234567"
    assert user.check_password(DEFAULT_PASSWORD)


def test_creation_form_reports_invalid_phone() -> None:
    form = UserCreationForm(
        data={
            "phone": "12345",
            "full_name": "Ayesha Khan",
            "password1": DEFAULT_PASSWORD,
            "password2": DEFAULT_PASSWORD,
        }
    )

    assert not form.is_valid()
    assert "phone" in form.errors


@pytest.mark.parametrize("url_name", ["admin:accounts_user_changelist", "admin:accounts_user_add"])
def test_user_admin_pages_render(admin_client: Client, url_name: str) -> None:
    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200


def test_user_admin_change_page_renders(admin_client: Client) -> None:
    user = UserFactory.create()

    response = admin_client.get(reverse("admin:accounts_user_change", args=[user.pk]))

    assert response.status_code == 200
    assert User.objects.filter(pk=user.pk).exists()
