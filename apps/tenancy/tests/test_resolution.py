import uuid

import pytest
from rest_framework.exceptions import APIException

from apps.accounts.models import Membership, Role, User
from apps.accounts.tests.factories import MembershipFactory, UserFactory
from apps.tenancy.context import Tenant
from apps.tenancy.models import Campus, Organisation
from apps.tenancy.resolution import resolve_tenant
from apps.tenancy.tests.factories import CampusFactory, OrganisationFactory

pytestmark = pytest.mark.django_db


def resolve(user: User, organisation: object = None, campus: object = None) -> Tenant:
    return resolve_tenant(
        user_id=user.pk,
        organisation_header=None if organisation is None else str(organisation),
        campus_header=None if campus is None else str(campus),
    )


def error_code(user: User, organisation: object = None, campus: object = None) -> object:
    with pytest.raises(APIException) as error:
        resolve(user, organisation, campus)
    return error.value.get_codes()


def grant(
    user: User,
    campus: Campus | None = None,
    role: Role = Role.TEACHER,
    *,
    organisation: Organisation | None = None,
    is_active: bool = True,
) -> Membership:
    return MembershipFactory.create(
        user=user,
        organisation=campus.organisation if campus else organisation,
        campus=campus,
        role=role,
        is_active=is_active,
    )


def test_single_organisation_is_chosen_without_a_header() -> None:
    user = UserFactory.create()
    membership = grant(user, organisation=OrganisationFactory.create(), role=Role.OWNER)

    assert resolve(user) == Tenant(
        organisation_id=membership.organisation_id, roles=frozenset({Role.OWNER})
    )


def test_several_organisations_need_a_header() -> None:
    user = UserFactory.create()
    first = grant(user, organisation=OrganisationFactory.create(), role=Role.OWNER)
    grant(user, organisation=OrganisationFactory.create(), role=Role.ADMIN)

    assert error_code(user) == "organisation_required"
    assert resolve(user, first.organisation_id).organisation_id == first.organisation_id


def test_foreign_organisation_header_is_forbidden() -> None:
    user = UserFactory.create()
    grant(user, organisation=OrganisationFactory.create(), role=Role.OWNER)

    assert error_code(user, OrganisationFactory.create().pk) == "organisation_forbidden"


def test_malformed_header_is_rejected() -> None:
    user = UserFactory.create()
    grant(user, organisation=OrganisationFactory.create(), role=Role.OWNER)

    assert error_code(user, "not-a-uuid") == "invalid_tenant_header"


def test_users_without_memberships_have_no_tenant() -> None:
    assert error_code(UserFactory.create()) == "organisation_required"


def test_revoked_memberships_are_ignored() -> None:
    user = UserFactory.create()
    revoked = grant(user, organisation=OrganisationFactory.create(), is_active=False)

    assert error_code(user, revoked.organisation_id) == "organisation_forbidden"


def test_a_single_campus_is_chosen_for_campus_staff() -> None:
    user = UserFactory.create()
    campus = CampusFactory.create()
    grant(user, campus)

    assert resolve(user) == Tenant(
        organisation_id=campus.organisation_id,
        campus_id=campus.pk,
        roles=frozenset({Role.TEACHER}),
    )


def test_campus_staff_on_several_campuses_must_choose_one() -> None:
    user = UserFactory.create()
    organisation = OrganisationFactory.create()
    first, second = CampusFactory.create_batch(2, organisation=organisation)
    grant(user, first)
    grant(user, second, role=Role.ACCOUNTANT)

    assert error_code(user) == "campus_required"
    assert resolve(user, campus=second.pk).roles == {Role.ACCOUNTANT}


def test_campus_staff_cannot_enter_another_campus() -> None:
    user = UserFactory.create()
    campus = CampusFactory.create()
    other = CampusFactory.create(organisation=campus.organisation)
    grant(user, campus)

    assert error_code(user, campus=other.pk) == "campus_forbidden"


def test_organisation_staff_may_enter_any_open_campus() -> None:
    user = UserFactory.create()
    campus = CampusFactory.create()
    grant(user, organisation=campus.organisation, role=Role.ADMIN)

    tenant = resolve(user, campus=campus.pk)

    assert tenant.campus_id == campus.pk
    assert tenant.roles == {Role.ADMIN}


@pytest.mark.parametrize("closed", [True, False])
def test_organisation_staff_cannot_enter_closed_or_foreign_campuses(closed: bool) -> None:
    user = UserFactory.create()
    organisation = OrganisationFactory.create()
    grant(user, organisation=organisation, role=Role.ADMIN)
    campus = (
        CampusFactory.create(organisation=organisation, is_active=False)
        if closed
        else CampusFactory.create()
    )

    assert error_code(user, campus=campus.pk) == "campus_forbidden"


def test_unknown_campus_is_forbidden() -> None:
    user = UserFactory.create()
    grant(user, organisation=OrganisationFactory.create(), role=Role.OWNER)

    assert error_code(user, campus=uuid.uuid7()) == "campus_forbidden"


def test_roles_combine_organisation_and_campus_memberships() -> None:
    user = UserFactory.create()
    campus = CampusFactory.create()
    other = CampusFactory.create(organisation=campus.organisation)
    grant(user, organisation=campus.organisation, role=Role.ACCOUNTANT)
    grant(user, campus, role=Role.TEACHER)
    grant(user, other, role=Role.ADMIN)

    assert resolve(user).roles == {Role.ACCOUNTANT}
    assert resolve(user, campus=campus.pk).roles == {Role.ACCOUNTANT, Role.TEACHER}
