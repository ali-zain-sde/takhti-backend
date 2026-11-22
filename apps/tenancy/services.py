from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.tenancy.models import Campus, Organisation, Province


@transaction.atomic
def create_organisation(*, name: str, slug: str) -> Organisation:
    organisation = Organisation(name=name.strip(), slug=slug)
    organisation.full_clean()
    organisation.save()
    return organisation


@transaction.atomic
def create_campus(
    *,
    organisation: Organisation,
    name: str,
    slug: str,
    province: Province,
    city: str,
) -> Campus:
    if not organisation.is_active:
        raise ValidationError(
            _("Campuses cannot be added to an inactive organisation."),
            code="organisation_inactive",
        )
    campus = Campus(
        organisation=organisation,
        name=name.strip(),
        slug=slug,
        province=province,
        city=city.strip(),
    )
    campus.full_clean()
    campus.save()
    return campus
