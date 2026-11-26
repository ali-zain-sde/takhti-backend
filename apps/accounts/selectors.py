from uuid import UUID

from django.db.models import Prefetch, Q, QuerySet

from apps.accounts.models import Membership, User


def active_memberships() -> QuerySet[Membership]:
    return Membership.unscoped.filter(is_active=True, organisation__is_active=True).filter(
        Q(campus__isnull=True) | Q(campus__is_active=True)
    )


def session_user(*, user_id: UUID) -> User:
    memberships = (
        active_memberships()
        .select_related("organisation", "campus")
        .order_by("organisation__name", "campus__name")
    )
    return User.objects.prefetch_related(
        Prefetch("memberships", queryset=memberships, to_attr="active_memberships")
    ).get(pk=user_id)
