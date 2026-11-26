from collections.abc import Callable
from dataclasses import dataclass, field

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from apps.accounts.models import Role, User
from apps.accounts.tests.factories import MembershipFactory, UserFactory
from apps.tenancy.context import current_tenant
from apps.tenancy.middleware import TenantMiddleware
from apps.tenancy.resolution import TenantResolution, request_resolution
from apps.tenancy.tests.factories import OrganisationFactory

pytestmark = pytest.mark.django_db


@dataclass
class Observed:
    tenant: object = None
    resolution: TenantResolution = field(default_factory=TenantResolution)
    scope: tuple[str, str, str] = ("", "", "")


def database_scope() -> tuple[str, str, str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_setting('app.organisation_id', true),"
            " current_setting('app.user_id', true),"
            " current_setting('app.is_system', true)"
        )
        row = cursor.fetchone()
    assert row is not None
    return (row[0] or "", row[1] or "", row[2] or "")


def observer(observed: Observed) -> Callable[[HttpRequest], HttpResponse]:
    def view(request: HttpRequest) -> HttpResponse:
        observed.tenant = current_tenant()
        observed.resolution = request_resolution(request)
        observed.scope = database_scope()
        return HttpResponse()

    return view


def run(user: User | AnonymousUser, path: str = "/api/v1/", **headers: str) -> Observed:
    observed = Observed()
    request = RequestFactory().get(path, headers=headers)
    request.user = user
    TenantMiddleware(observer(observed))(request)
    return observed


def test_anonymous_requests_get_no_tenant_or_database_scope() -> None:
    observed = run(AnonymousUser())

    assert observed.tenant is None
    assert observed.scope == ("", "", "")


def test_member_requests_run_inside_their_tenant() -> None:
    user = UserFactory.create()
    membership = MembershipFactory.create(user=user, role=Role.OWNER)

    observed = run(user)

    assert observed.tenant == observed.resolution.tenant
    assert observed.scope == (str(membership.organisation_id), str(user.pk), "off")


def test_scope_and_context_are_cleared_after_the_request() -> None:
    user = UserFactory.create()
    MembershipFactory.create(user=user, role=Role.OWNER)

    run(user)

    assert current_tenant() is None
    assert database_scope() == ("", "", "off")


def test_resolution_errors_are_kept_for_the_view() -> None:
    user = UserFactory.create()
    MembershipFactory.create(user=user, role=Role.OWNER)

    observed = run(user, **{"X-Organisation": str(OrganisationFactory.create().pk)})

    resolution = observed.resolution
    assert resolution.tenant is None
    assert resolution.error is not None
    assert resolution.error.get_codes() == "organisation_forbidden"
    assert observed.scope == ("", str(user.pk), "off")


def test_staff_on_the_admin_site_get_system_scope() -> None:
    staff = UserFactory.create(is_staff=True)

    observed = run(staff, "/admin/")

    assert observed.tenant is None
    assert observed.scope == ("", str(staff.pk), "on")


def test_non_staff_never_get_system_scope() -> None:
    user = UserFactory.create()

    observed = run(user, "/admin/")

    assert observed.scope[2] == "off"
