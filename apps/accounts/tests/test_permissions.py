import uuid

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.accounts.permissions import (
    CanManageFinance,
    CanManageSchool,
    CanRecordAcademics,
    HasRole,
    IsMember,
    IsOwner,
)
from apps.accounts.tests.factories import UserFactory
from apps.tenancy.context import Tenant
from apps.tenancy.exceptions import TenantForbidden
from apps.tenancy.resolution import TenantResolution, attach_resolution

EXPECTED_ACCESS: dict[type[HasRole], set[Role]] = {
    IsMember: {Role.OWNER, Role.ADMIN, Role.ACCOUNTANT, Role.TEACHER},
    IsOwner: {Role.OWNER},
    CanManageSchool: {Role.OWNER, Role.ADMIN},
    CanManageFinance: {Role.OWNER, Role.ADMIN, Role.ACCOUNTANT},
    CanRecordAcademics: {Role.OWNER, Role.ADMIN, Role.TEACHER},
}


def build_request(resolution: TenantResolution, *, authenticated: bool = True) -> Request:
    django_request = APIRequestFactory().get("/")
    attach_resolution(django_request, resolution)
    request = Request(django_request)
    request.user = UserFactory.build() if authenticated else AnonymousUser()
    return request


def tenant_with(*roles: Role) -> TenantResolution:
    return TenantResolution(tenant=Tenant(organisation_id=uuid.uuid7(), roles=frozenset(roles)))


def is_allowed(permission: type[HasRole], request: Request) -> bool:
    return permission().has_permission(request, APIView())


@pytest.mark.parametrize("permission", EXPECTED_ACCESS)
@pytest.mark.parametrize("role", Role)
def test_permission_matches_the_role_matrix(permission: type[HasRole], role: Role) -> None:
    allowed = is_allowed(permission, build_request(tenant_with(role)))

    assert allowed is (role in EXPECTED_ACCESS[permission])


def test_any_matching_role_in_the_tenant_is_enough() -> None:
    assert is_allowed(CanManageFinance, build_request(tenant_with(Role.TEACHER, Role.ACCOUNTANT)))


@pytest.mark.parametrize("permission", EXPECTED_ACCESS)
def test_anonymous_users_are_denied(permission: type[HasRole]) -> None:
    request = build_request(tenant_with(Role.OWNER), authenticated=False)

    assert not is_allowed(permission, request)


def test_requests_without_a_tenant_are_rejected() -> None:
    with pytest.raises(exceptions.APIException) as error:
        is_allowed(IsMember, build_request(TenantResolution()))

    assert error.value.get_codes() == "organisation_required"


def test_tenant_resolution_errors_are_raised() -> None:
    with pytest.raises(TenantForbidden):
        is_allowed(IsMember, build_request(TenantResolution(error=TenantForbidden())))


def test_base_permission_without_roles_denies_everyone() -> None:
    assert not is_allowed(HasRole, build_request(tenant_with(*Role)))
