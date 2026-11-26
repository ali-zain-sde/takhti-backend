from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from django.db import connection, transaction

_SCOPE_SQL = (
    "SELECT set_config('app.organisation_id', %s, %s),"
    " set_config('app.user_id', %s, %s),"
    " set_config('app.is_system', %s, %s)"
)


def apply_database_scope(
    *, user_id: UUID | None, organisation_id: UUID | None = None, is_system: bool = False
) -> None:
    _set_scope(user_id, organisation_id, is_system=is_system, local=False)


@contextmanager
def transaction_database_scope(
    *, user_id: UUID | None, organisation_id: UUID | None = None
) -> Iterator[None]:
    with transaction.atomic():
        _set_scope(user_id, organisation_id, is_system=False, local=True)
        yield


def clear_database_scope() -> None:
    if connection.connection is not None:
        apply_database_scope(user_id=None)


def _set_scope(
    user_id: UUID | None, organisation_id: UUID | None, *, is_system: bool, local: bool
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            _SCOPE_SQL,
            [
                _as_setting(organisation_id),
                local,
                _as_setting(user_id),
                local,
                "on" if is_system else "off",
                local,
            ],
        )


def _as_setting(value: UUID | None) -> str:
    return "" if value is None else str(value)
