import factory
from factory.django import DjangoModelFactory

from apps.tenancy.models import Campus, Organisation, Province


class OrganisationFactory(DjangoModelFactory[Organisation]):
    class Meta:
        model = Organisation

    name = factory.Sequence(lambda number: f"School Network {number}")
    slug = factory.Sequence(lambda number: f"school-network-{number}")


class CampusFactory(DjangoModelFactory[Campus]):
    class Meta:
        model = Campus

    organisation = factory.SubFactory(OrganisationFactory)
    name = factory.Sequence(lambda number: f"Campus {number}")
    slug = factory.Sequence(lambda number: f"campus-{number}")
    province = Province.PUNJAB
    city = "Lahore"
