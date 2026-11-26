import pytest

from apps.accounts.models import Membership
from apps.accounts.tests.factories import MembershipFactory
from apps.tenancy.context import Tenant, current_tenant, tenant_context
from apps.tenancy.models import Campus, Organisation
from apps.tenancy.tests.factories import CampusFactory

pytestmark = pytest.mark.django_db


def test_tenant_context_is_restored_after_use() -> None:
    tenant = Tenant(organisation_id=CampusFactory.create().organisation_id)

    with tenant_context(tenant):
        assert current_tenant() == tenant

    assert current_tenant() is None


def test_tenant_context_nests_and_unwinds() -> None:
    outer = Tenant(organisation_id=CampusFactory.create().organisation_id)
    inner = Tenant(organisation_id=CampusFactory.create().organisation_id)

    with tenant_context(outer), tenant_context(inner):
        assert current_tenant() == inner

    assert current_tenant() is None


def test_scoped_managers_return_nothing_without_a_tenant() -> None:
    MembershipFactory.create(organisation=CampusFactory.create().organisation)

    assert not Organisation.objects.exists()
    assert not Campus.objects.exists()
    assert not Membership.objects.exists()


def test_scoped_managers_only_see_the_current_organisation() -> None:
    own = CampusFactory.create()
    other = CampusFactory.create()
    own_membership = MembershipFactory.create(organisation=own.organisation)
    MembershipFactory.create(organisation=other.organisation)

    with tenant_context(Tenant(organisation_id=own.organisation_id)):
        assert list(Organisation.objects.all()) == [own.organisation]
        assert list(Campus.objects.all()) == [own]
        assert list(Membership.objects.all()) == [own_membership]
        assert not Campus.objects.filter(pk=other.pk).exists()


def test_unscoped_managers_see_every_organisation() -> None:
    CampusFactory.create_batch(2)

    with tenant_context(Tenant(organisation_id=CampusFactory.create().organisation_id)):
        assert Campus.unscoped.count() == 3
        assert Organisation.unscoped.count() == 3


def test_related_lookups_are_not_scoped_away() -> None:
    campus = CampusFactory.create()

    assert list(campus.organisation.campuses.all()) == [campus]
