from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Membership, Role, User
from apps.tenancy.models import Campus, Organisation


@transaction.atomic
def grant_membership(
    *,
    user: User,
    organisation: Organisation,
    role: Role,
    campus: Campus | None = None,
) -> Membership:
    _ensure_scope_is_active(organisation=organisation, campus=campus)
    existing = (
        Membership.unscoped.select_for_update()
        .filter(user=user, organisation=organisation, campus=campus)
        .first()
    )
    if existing is not None and existing.is_active:
        raise ValidationError(
            _("This person already has access to this organisation or campus."),
            code="membership_exists",
        )
    membership = existing or Membership(user=user, organisation=organisation, campus=campus)
    membership.role = role
    membership.is_active = True
    membership.full_clean()
    membership.save()
    return membership


@transaction.atomic
def revoke_membership(*, membership: Membership) -> Membership:
    membership.is_active = False
    membership.save(update_fields=("is_active", "updated_at"))
    return membership


def _ensure_scope_is_active(*, organisation: Organisation, campus: Campus | None) -> None:
    if not organisation.is_active:
        raise ValidationError(
            _("Access cannot be granted to an inactive organisation."),
            code="organisation_inactive",
        )
    if campus is not None and not campus.is_active:
        raise ValidationError(
            _("Access cannot be granted to an inactive campus."),
            code="campus_inactive",
        )
