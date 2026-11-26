import uuid
from collections.abc import Callable

import pytest
from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.urls import reverse
from psycopg import sql
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Role
from apps.accounts.tests.factories import DEFAULT_PASSWORD, MembershipFactory, UserFactory
from apps.tenancy.database import apply_database_scope
from apps.tenancy.models import Campus, Organisation, Province
from apps.tenancy.tests.factories import CampusFactory

pytestmark = pytest.mark.django_db

SwitchRole = Callable[[], None]


@pytest.fixture
def as_application_role() -> SwitchRole:
    def switch() -> None:
        role = sql.Identifier(f"rls_probe_{uuid.uuid4().hex[:12]}")
        statements = (
            sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOBYPASSRLS").format(role),
            sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role),
            sql.SQL("GRANT ALL ON ALL TABLES IN SCHEMA public TO {}").format(role),
            sql.SQL("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {}").format(role),
            sql.SQL("SET LOCAL ROLE {}").format(role),
        )
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)

    return switch


@pytest.fixture
def two_schools() -> tuple[Campus, Campus]:
    return CampusFactory.create(), CampusFactory.create()


def visible() -> tuple[set[object], set[object], set[object]]:
    return (
        set(Organisation.unscoped.values_list("pk", flat=True)),
        set(Campus.unscoped.values_list("pk", flat=True)),
        set(Membership.unscoped.values_list("pk", flat=True)),
    )


def test_superuser_connection_bypasses_policies(two_schools: tuple[Campus, Campus]) -> None:
    organisations, campuses, _ = visible()

    assert len(organisations) == 2
    assert len(campuses) == 2


def test_application_role_sees_nothing_without_a_scope(
    two_schools: tuple[Campus, Campus], as_application_role: SwitchRole
) -> None:
    MembershipFactory.create(organisation=two_schools[0].organisation)
    as_application_role()

    assert visible() == (set(), set(), set())


def test_tenant_scope_reveals_only_its_own_rows(
    two_schools: tuple[Campus, Campus], as_application_role: SwitchRole
) -> None:
    own, other = two_schools
    membership = MembershipFactory.create(organisation=own.organisation)
    MembershipFactory.create(organisation=other.organisation)
    as_application_role()

    apply_database_scope(user_id=None, organisation_id=own.organisation_id)

    assert visible() == ({own.organisation_id}, {own.pk}, {membership.pk})


def test_user_scope_reveals_only_that_users_organisations(
    two_schools: tuple[Campus, Campus], as_application_role: SwitchRole
) -> None:
    own, other = two_schools
    user = UserFactory.create()
    membership = MembershipFactory.create(user=user, organisation=own.organisation)
    MembershipFactory.create(organisation=own.organisation)
    MembershipFactory.create(organisation=other.organisation)
    as_application_role()

    apply_database_scope(user_id=user.pk)

    assert visible() == ({own.organisation_id}, {own.pk}, {membership.pk})


def test_revoked_memberships_do_not_reveal_an_organisation(
    two_schools: tuple[Campus, Campus], as_application_role: SwitchRole
) -> None:
    own, _ = two_schools
    user = UserFactory.create()
    MembershipFactory.create(user=user, organisation=own.organisation, is_active=False)
    as_application_role()

    apply_database_scope(user_id=user.pk)

    organisations, campuses, _ = visible()
    assert organisations == set()
    assert campuses == set()


def test_system_scope_reveals_everything(
    two_schools: tuple[Campus, Campus], as_application_role: SwitchRole
) -> None:
    as_application_role()

    apply_database_scope(user_id=None, is_system=True)

    organisations, campuses, _ = visible()
    assert campuses == {campus.pk for campus in two_schools}
    assert len(organisations) == 2


def test_writes_into_another_organisation_are_rejected(
    two_schools: tuple[Campus, Campus], as_application_role: SwitchRole
) -> None:
    own, other = two_schools
    as_application_role()
    apply_database_scope(user_id=None, organisation_id=own.organisation_id)

    with pytest.raises(DatabaseError), transaction.atomic():
        Campus.unscoped.create(
            organisation_id=other.organisation_id,
            name="Intruder",
            slug="intruder",
            province=Province.PUNJAB,
            city="Lahore",
        )


def test_rows_cannot_be_moved_into_another_organisation(
    two_schools: tuple[Campus, Campus], as_application_role: SwitchRole
) -> None:
    own, other = two_schools
    as_application_role()
    apply_database_scope(user_id=None, organisation_id=own.organisation_id)

    with pytest.raises(DatabaseError), transaction.atomic():
        Campus.unscoped.filter(pk=own.pk).update(organisation_id=other.organisation_id)


def test_rows_of_another_organisation_cannot_be_changed(
    two_schools: tuple[Campus, Campus], as_application_role: SwitchRole
) -> None:
    own, other = two_schools
    as_application_role()
    apply_database_scope(user_id=None, organisation_id=own.organisation_id)

    assert Campus.unscoped.filter(pk=other.pk).update(name="Renamed") == 0
    assert Campus.unscoped.filter(pk=other.pk).delete()[0] == 0


def test_login_and_me_return_memberships_under_policies(
    two_schools: tuple[Campus, Campus], as_application_role: SwitchRole
) -> None:
    own, other = two_schools
    user = UserFactory.create(phone="+923001234567")
    membership = MembershipFactory.create(
        user=user, organisation=own.organisation, campus=own, role=Role.ACCOUNTANT
    )
    MembershipFactory.create(organisation=other.organisation, role=Role.OWNER)
    as_application_role()
    client = APIClient(enforce_csrf_checks=True)
    client.get(reverse("auth:csrf"))
    token = client.cookies[settings.CSRF_COOKIE_NAME].value

    login = client.post(
        reverse("auth:login"),
        {"phone": "03001234567", "password": DEFAULT_PASSWORD},
        headers={"X-CSRFToken": token},
    )
    me = client.get(reverse("auth:me"))

    for response in (login, me):
        assert response.status_code == status.HTTP_200_OK
        memberships = response.json()["memberships"]
        assert [item["id"] for item in memberships] == [str(membership.pk)]
        assert memberships[0]["campus"]["id"] == str(own.pk)
