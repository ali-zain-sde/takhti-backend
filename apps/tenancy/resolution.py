from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.request import Request

from apps.accounts.models import Membership
from apps.accounts.selectors import active_memberships
from apps.tenancy.context import Tenant
from apps.tenancy.exceptions import TenantForbidden, TenantRequired
from apps.tenancy.models import Campus

ORGANISATION_HEADER = "X-Organisation"
CAMPUS_HEADER = "X-Campus"
_REQUEST_ATTRIBUTE = "tenancy"


@dataclass(frozen=True, slots=True)
class TenantResolution:
    tenant: Tenant | None = None
    error: APIException | None = None


UNRESOLVED = TenantResolution()


def resolve_tenant(
    *, user_id: UUID, organisation_header: str | None, campus_header: str | None
) -> Tenant:
    requested_organisation = _parse_identifier(organisation_header)
    requested_campus = _parse_identifier(campus_header)
    memberships = list(active_memberships().filter(user_id=user_id))
    organisation_id = _choose_organisation(memberships, requested_organisation)
    in_organisation = [m for m in memberships if m.organisation_id == organisation_id]
    campus_id = _choose_campus(organisation_id, in_organisation, requested_campus)
    return Tenant(
        organisation_id=organisation_id,
        campus_id=campus_id,
        roles=frozenset(
            m.role for m in in_organisation if m.campus_id is None or m.campus_id == campus_id
        ),
    )


def attach_resolution(request: HttpRequest, resolution: TenantResolution) -> None:
    setattr(request, _REQUEST_ATTRIBUTE, resolution)


def request_resolution(request: HttpRequest | Request) -> TenantResolution:
    resolution = getattr(request, _REQUEST_ATTRIBUTE, UNRESOLVED)
    return resolution if isinstance(resolution, TenantResolution) else UNRESOLVED


def _parse_identifier(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError as error:
        raise TenantRequired(
            _("The organisation or campus header is not a valid identifier."),
            code="invalid_tenant_header",
        ) from error


def _choose_organisation(memberships: Sequence[Membership], requested: UUID | None) -> UUID:
    organisation_ids = {membership.organisation_id for membership in memberships}
    if requested is not None:
        if requested not in organisation_ids:
            raise TenantForbidden
        return requested
    if len(organisation_ids) != 1:
        raise TenantRequired
    return organisation_ids.pop()


def _choose_campus(
    organisation_id: UUID, memberships: Sequence[Membership], requested: UUID | None
) -> UUID | None:
    organisation_wide = any(m.campus_id is None for m in memberships)
    campus_ids = {m.campus_id for m in memberships if m.campus_id is not None}
    if requested is None:
        if organisation_wide:
            return None
        if len(campus_ids) == 1:
            return campus_ids.pop()
        raise TenantRequired(_("Choose a campus to continue."), code="campus_required")
    if requested in campus_ids or (
        organisation_wide and _campus_is_open(organisation_id, requested)
    ):
        return requested
    raise TenantForbidden(_("You do not have access to this campus."), code="campus_forbidden")


def _campus_is_open(organisation_id: UUID, campus_id: UUID) -> bool:
    return Campus.unscoped.filter(
        pk=campus_id, organisation_id=organisation_id, is_active=True
    ).exists()
