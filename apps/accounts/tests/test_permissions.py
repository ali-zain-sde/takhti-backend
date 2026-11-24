import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.accounts.models import Role, User
from apps.accounts.permissions import (
    CanManageFinance,
    CanManageSchool,
    CanRecordAcademics,
    HasRole,
    IsMember,
    IsOwner,
)
from apps.accounts.tests.factories import MembershipFactory, UserFactory
from apps.tenancy.tests.factories import OrganisationFactory

pytestmark = pytest.mark.django_db

EXPECTED_ACCESS: dict[type[HasRole], set[Role]] = {
    IsMember: {Role.OWNER, Role.ADMIN, Role.ACCOUNTANT, Role.TEACHER},
    IsOwner: {Role.OWNER},
    CanManageSchool: {Role.OWNER, Role.ADMIN},
    CanManageFinance: {Role.OWNER, Role.ADMIN, Role.ACCOUNTANT},
    CanRecordAcademics: {Role.OWNER, Role.ADMIN, Role.TEACHER},
}


def is_allowed(permission: type[HasRole], user: User | AnonymousUser) -> bool:
    request = Request(APIRequestFactory().get("/"))
    request.user = user
    return permission().has_permission(request, APIView())


@pytest.mark.parametrize("permission", EXPECTED_ACCESS)
@pytest.mark.parametrize("role", Role)
def test_permission_matches_the_role_matrix(permission: type[HasRole], role: Role) -> None:
    membership = MembershipFactory.create(role=role)

    assert is_allowed(permission, membership.user) is (role in EXPECTED_ACCESS[permission])


@pytest.mark.parametrize("permission", EXPECTED_ACCESS)
def test_anonymous_users_are_denied(permission: type[HasRole]) -> None:
    assert not is_allowed(permission, AnonymousUser())


def test_users_without_memberships_are_denied() -> None:
    assert not is_allowed(IsMember, UserFactory.create())


def test_revoked_memberships_grant_nothing() -> None:
    membership = MembershipFactory.create(role=Role.OWNER, is_active=False)

    assert not is_allowed(IsOwner, membership.user)


def test_memberships_in_inactive_organisations_grant_nothing() -> None:
    membership = MembershipFactory.create(
        role=Role.OWNER, organisation=OrganisationFactory.create(is_active=False)
    )

    assert not is_allowed(IsOwner, membership.user)


def test_base_permission_without_roles_denies_everyone() -> None:
    membership = MembershipFactory.create(role=Role.OWNER)

    assert not is_allowed(HasRole, membership.user)
