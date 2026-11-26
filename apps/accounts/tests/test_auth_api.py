from typing import TYPE_CHECKING

import pytest
from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.accounts.tests.factories import DEFAULT_PASSWORD, MembershipFactory, UserFactory
from apps.tenancy.tests.factories import CampusFactory, OrganisationFactory

if TYPE_CHECKING:
    from rest_framework.response import _MonkeyPatchedResponse

pytestmark = pytest.mark.django_db

CSRF_URL = reverse("auth:csrf")
LOGIN_URL = reverse("auth:login")
LOGOUT_URL = reverse("auth:logout")
ME_URL = reverse("auth:me")
PHONE = "+923001234567"


@pytest.fixture
def client() -> APIClient:
    return APIClient(enforce_csrf_checks=True)


def csrf_headers(client: APIClient) -> dict[str, str]:
    client.get(CSRF_URL)
    return {"X-CSRFToken": client.cookies[settings.CSRF_COOKIE_NAME].value}


def log_in(
    client: APIClient, phone: str = PHONE, password: str = DEFAULT_PASSWORD
) -> _MonkeyPatchedResponse:
    return client.post(
        LOGIN_URL, {"phone": phone, "password": password}, headers=csrf_headers(client)
    )


def test_csrf_endpoint_sets_the_csrf_cookie(client: APIClient) -> None:
    response = client.get(CSRF_URL)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert settings.CSRF_COOKIE_NAME in response.cookies


def test_login_starts_a_session_and_returns_the_user(client: APIClient) -> None:
    user = UserFactory.create(phone=PHONE, full_name="Ayesha Khan")
    membership = MembershipFactory.create(user=user, role=Role.OWNER)

    response = log_in(client, phone="0300 1234567")

    assert response.status_code == status.HTTP_200_OK
    assert settings.SESSION_COOKIE_NAME in response.cookies
    assert response.json() == {
        "id": str(user.id),
        "phone": PHONE,
        "full_name": "Ayesha Khan",
        "email": "",
        "memberships": [
            {
                "id": str(membership.id),
                "role": "owner",
                "organisation": {
                    "id": str(membership.organisation.id),
                    "name": membership.organisation.name,
                    "slug": membership.organisation.slug,
                },
                "campus": None,
            }
        ],
    }


def test_login_rotates_the_session_key(client: APIClient) -> None:
    UserFactory.create(phone=PHONE)
    client.get(CSRF_URL)
    session = client.session
    session["visited"] = True
    session.save()
    anonymous_key = session.session_key

    log_in(client)

    assert client.cookies[settings.SESSION_COOKIE_NAME].value != anonymous_key


@pytest.mark.parametrize(
    ("phone", "password"),
    [(PHONE, "wrong-password"), ("+923009999999", DEFAULT_PASSWORD), ("not-a-phone", "x")],
)
def test_login_rejects_bad_credentials_with_one_generic_error(
    client: APIClient, phone: str, password: str
) -> None:
    UserFactory.create(phone=PHONE)

    response = log_in(client, phone=phone, password=password)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "error": {"code": "invalid_credentials", "message": "Incorrect phone number or password."}
    }
    assert settings.SESSION_COOKIE_NAME not in response.cookies


def test_login_rejects_inactive_users(client: APIClient) -> None:
    UserFactory.create(phone=PHONE, is_active=False)

    response = log_in(client)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_reports_missing_fields(client: APIClient) -> None:
    response = client.post(LOGIN_URL, {}, headers=csrf_headers(client))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    assert set(body["field_errors"]) == {"phone", "password"}


def test_login_requires_a_csrf_token(client: APIClient) -> None:
    UserFactory.create(phone=PHONE)

    response = client.post(LOGIN_URL, {"phone": PHONE, "password": DEFAULT_PASSWORD})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["error"]["code"] == "csrf_failed"


def test_login_is_throttled_after_repeated_attempts(client: APIClient) -> None:
    headers = csrf_headers(client)
    payload = {"phone": PHONE, "password": "wrong-password"}
    for _ in range(10):
        client.post(LOGIN_URL, payload, headers=headers)

    response = client.post(LOGIN_URL, payload, headers=headers)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["error"]["code"] == "throttled"


def test_me_requires_a_session(client: APIClient) -> None:
    response = client.get(ME_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response["WWW-Authenticate"] == "Session"
    assert response.json()["error"]["code"] == "not_authenticated"


def test_me_lists_only_usable_memberships(client: APIClient) -> None:
    user = UserFactory.create()
    campus = CampusFactory.create(organisation__name="Beacon School", name="Gulberg")
    usable = MembershipFactory.create(
        user=user, organisation=campus.organisation, campus=campus, role=Role.ACCOUNTANT
    )
    MembershipFactory.create(user=user, is_active=False)
    MembershipFactory.create(user=user, organisation=OrganisationFactory.create(is_active=False))
    closed_campus = CampusFactory.create(is_active=False)
    MembershipFactory.create(
        user=user, organisation=closed_campus.organisation, campus=closed_campus
    )
    client.force_login(user)

    response = client.get(ME_URL)

    assert response.status_code == status.HTTP_200_OK
    memberships = response.json()["memberships"]
    assert [membership["id"] for membership in memberships] == [str(usable.id)]
    assert memberships[0]["campus"] == {
        "id": str(campus.id),
        "name": "Gulberg",
        "slug": campus.slug,
    }


def count_me_queries(client: APIClient, campuses: int) -> int:
    user = UserFactory.create()
    organisation = OrganisationFactory.create()
    MembershipFactory.create(user=user, organisation=organisation, role=Role.ADMIN)
    for campus in CampusFactory.create_batch(campuses, organisation=organisation):
        MembershipFactory.create(user=user, organisation=organisation, campus=campus)
    client.force_login(user)
    with CaptureQueriesContext(connection) as queries:
        response = client.get(ME_URL)
    assert len(response.json()["memberships"]) == campuses + 1
    return len(queries)


def test_me_query_count_does_not_grow_with_memberships(client: APIClient) -> None:
    assert count_me_queries(client, 1) == count_me_queries(client, 5)


def test_logout_ends_the_session(client: APIClient) -> None:
    UserFactory.create(phone=PHONE)
    log_in(client)

    response = client.post(LOGOUT_URL, headers=csrf_headers(client))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert client.get(ME_URL).status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_requires_a_csrf_token(client: APIClient) -> None:
    client.force_login(UserFactory.create())

    response = client.post(LOGOUT_URL)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_me_works_with_a_stale_organisation_header(client: APIClient) -> None:
    membership = MembershipFactory.create(role=Role.OWNER)
    client.force_login(membership.user)

    response = client.get(ME_URL, headers={"X-Organisation": str(OrganisationFactory.create().pk)})

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.json()["memberships"]] == [str(membership.id)]
