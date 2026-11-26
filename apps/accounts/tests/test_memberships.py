import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.accounts.models import Membership, Role
from apps.accounts.services import grant_membership, revoke_membership
from apps.accounts.tests.factories import MembershipFactory, UserFactory
from apps.tenancy.tests.factories import CampusFactory, OrganisationFactory

pytestmark = pytest.mark.django_db


def test_grant_owner_membership_covers_the_whole_organisation() -> None:
    user = UserFactory.create()
    organisation = OrganisationFactory.create()

    membership = grant_membership(user=user, organisation=organisation, role=Role.OWNER)

    membership.refresh_from_db()
    assert membership.role == Role.OWNER
    assert membership.campus is None
    assert membership.is_active


def test_grant_campus_scoped_membership() -> None:
    user = UserFactory.create()
    campus = CampusFactory.create()

    membership = grant_membership(
        user=user, organisation=campus.organisation, campus=campus, role=Role.ACCOUNTANT
    )

    assert membership.campus == campus
    assert membership.role == Role.ACCOUNTANT


def test_one_person_may_hold_roles_in_different_scopes() -> None:
    user = UserFactory.create()
    campus = CampusFactory.create()

    grant_membership(user=user, organisation=campus.organisation, role=Role.OWNER)
    grant_membership(user=user, organisation=campus.organisation, campus=campus, role=Role.TEACHER)

    assert user.memberships.count() == 2


def test_owner_cannot_be_scoped_to_a_campus() -> None:
    campus = CampusFactory.create()

    with pytest.raises(ValidationError) as error:
        grant_membership(
            user=UserFactory.create(),
            organisation=campus.organisation,
            campus=campus,
            role=Role.OWNER,
        )

    assert "campus" in error.value.message_dict


def test_campus_must_belong_to_the_organisation() -> None:
    campus = CampusFactory.create()

    with pytest.raises(ValidationError) as error:
        grant_membership(
            user=UserFactory.create(),
            organisation=OrganisationFactory.create(),
            campus=campus,
            role=Role.TEACHER,
        )

    assert "campus" in error.value.message_dict


def test_grant_rejects_inactive_organisation() -> None:
    with pytest.raises(ValidationError) as error:
        grant_membership(
            user=UserFactory.create(),
            organisation=OrganisationFactory.create(is_active=False),
            role=Role.ADMIN,
        )

    assert error.value.code == "organisation_inactive"


def test_grant_rejects_inactive_campus() -> None:
    campus = CampusFactory.create(is_active=False)

    with pytest.raises(ValidationError) as error:
        grant_membership(
            user=UserFactory.create(),
            organisation=campus.organisation,
            campus=campus,
            role=Role.TEACHER,
        )

    assert error.value.code == "campus_inactive"


def test_grant_rejects_a_second_active_membership_in_the_same_scope() -> None:
    existing = MembershipFactory.create(role=Role.TEACHER)

    with pytest.raises(ValidationError) as error:
        grant_membership(user=existing.user, organisation=existing.organisation, role=Role.ADMIN)

    assert error.value.code == "membership_exists"


def test_regranting_a_revoked_scope_reactivates_it_with_the_new_role() -> None:
    existing = MembershipFactory.create(role=Role.TEACHER, is_active=False)

    membership = grant_membership(
        user=existing.user, organisation=existing.organisation, role=Role.ADMIN
    )

    assert membership.pk == existing.pk
    assert membership.role == Role.ADMIN
    assert membership.is_active
    assert Membership.unscoped.count() == 1


def test_revoke_membership_keeps_the_row_but_deactivates_it() -> None:
    membership = MembershipFactory.create()

    revoke_membership(membership=membership)

    membership.refresh_from_db()
    assert not membership.is_active


def test_database_treats_organisation_wide_scopes_as_unique() -> None:
    existing = MembershipFactory.create()

    with pytest.raises(IntegrityError):
        MembershipFactory.create(user=existing.user, organisation=existing.organisation)


def test_database_rejects_campus_scoped_owner() -> None:
    campus = CampusFactory.create()

    with pytest.raises(IntegrityError):
        MembershipFactory.create(organisation=campus.organisation, campus=campus, role=Role.OWNER)
