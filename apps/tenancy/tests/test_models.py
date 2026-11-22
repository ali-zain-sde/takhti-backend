import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from apps.tenancy.models import Campus, Organisation
from apps.tenancy.tests.factories import CampusFactory, OrganisationFactory

pytestmark = pytest.mark.django_db


def test_organisation_slug_is_globally_unique() -> None:
    OrganisationFactory.create(slug="city-grammar")

    with pytest.raises(IntegrityError):
        OrganisationFactory.create(slug="city-grammar")


@pytest.mark.parametrize("slug", ["City-Grammar", "city_grammar", "-city", "city--grammar"])
def test_organisation_rejects_malformed_slug_at_database_level(slug: str) -> None:
    with pytest.raises(IntegrityError):
        Organisation.objects.create(name="City Grammar", slug=slug)


def test_organisation_rejects_blank_name_at_database_level() -> None:
    with pytest.raises(IntegrityError):
        Organisation.objects.create(name="", slug="blank")


def test_campus_slug_is_unique_within_an_organisation() -> None:
    campus = CampusFactory.create(slug="main")

    with pytest.raises(IntegrityError):
        CampusFactory.create(organisation=campus.organisation, slug="main")


def test_campus_slug_may_repeat_across_organisations() -> None:
    CampusFactory.create(slug="main")

    CampusFactory.create(slug="main")

    assert Campus.objects.filter(slug="main").count() == 2


def test_campus_rejects_unknown_province_at_database_level() -> None:
    organisation = OrganisationFactory.create()

    with pytest.raises(IntegrityError):
        Campus.objects.create(
            organisation=organisation,
            name="Main",
            slug="main",
            province="atlantis",
            city="Lahore",
        )


def test_organisation_with_campuses_cannot_be_deleted() -> None:
    campus = CampusFactory.create()

    with pytest.raises(ProtectedError):
        campus.organisation.delete()


def test_string_representations_are_human_readable() -> None:
    campus = CampusFactory.create(organisation__name="City Grammar", name="Model Town")

    assert str(campus.organisation) == "City Grammar"
    assert str(campus) == "City Grammar · Model Town"
