import factory
from factory.django import DjangoModelFactory, Password

from apps.accounts.models import Membership, Role, User
from apps.tenancy.tests.factories import OrganisationFactory

DEFAULT_PASSWORD = "correct-horse-battery"


class UserFactory(DjangoModelFactory[User]):
    class Meta:
        model = User
        django_get_or_create = ("phone",)

    phone = factory.Sequence(lambda number: f"+92300{number:07d}")
    full_name = factory.Sequence(lambda number: f"Staff Member {number}")
    password = Password(DEFAULT_PASSWORD)


class MembershipFactory(DjangoModelFactory[Membership]):
    class Meta:
        model = Membership

    user = factory.SubFactory(UserFactory)
    organisation = factory.SubFactory(OrganisationFactory)
    role = Role.TEACHER
