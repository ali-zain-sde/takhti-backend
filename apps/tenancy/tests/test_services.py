import pytest
from django.core.exceptions import ValidationError

from apps.tenancy.models import Province
from apps.tenancy.services import create_campus, create_organisation
from apps.tenancy.tests.factories import CampusFactory, OrganisationFactory

pytestmark = pytest.mark.django_db


def test_create_organisation_persists_a_trimmed_active_organisation() -> None:
    organisation = create_organisation(name="  City Grammar School  ", slug="city-grammar")

    organisation.refresh_from_db()
    assert organisation.name == "City Grammar School"
    assert organisation.slug == "city-grammar"
    assert organisation.is_active
    assert organisation.id.version == 7


def test_create_organisation_rejects_malformed_slug() -> None:
    with pytest.raises(ValidationError) as error:
        create_organisation(name="City Grammar", slug="City Grammar")

    assert "slug" in error.value.message_dict


def test_create_organisation_rejects_blank_name() -> None:
    with pytest.raises(ValidationError) as error:
        create_organisation(name="   ", slug="city-grammar")

    assert "name" in error.value.message_dict


def test_create_organisation_rejects_duplicate_slug() -> None:
    OrganisationFactory.create(slug="city-grammar")

    with pytest.raises(ValidationError) as error:
        create_organisation(name="City Grammar", slug="city-grammar")

    assert "slug" in error.value.message_dict


def test_create_campus_persists_a_campus_under_the_organisation() -> None:
    organisation = OrganisationFactory.create()

    campus = create_campus(
        organisation=organisation,
        name=" Model Town ",
        slug="model-town",
        province=Province.PUNJAB,
        city=" Lahore ",
    )

    campus.refresh_from_db()
    assert campus.organisation == organisation
    assert campus.name == "Model Town"
    assert campus.city == "Lahore"
    assert campus.province == Province.PUNJAB
    assert campus.is_active


def test_create_campus_rejects_duplicate_slug_within_organisation() -> None:
    existing = CampusFactory.create(slug="model-town")

    with pytest.raises(ValidationError):
        create_campus(
            organisation=existing.organisation,
            name="Model Town",
            slug="model-town",
            province=Province.PUNJAB,
            city="Lahore",
        )


def test_create_campus_rejects_inactive_organisation() -> None:
    organisation = OrganisationFactory.create(is_active=False)

    with pytest.raises(ValidationError) as error:
        create_campus(
            organisation=organisation,
            name="Model Town",
            slug="model-town",
            province=Province.PUNJAB,
            city="Lahore",
        )

    assert error.value.code == "organisation_inactive"
