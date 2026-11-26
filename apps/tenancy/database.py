from uuid import UUID

from django.db import connection

_SCOPE_SQL = (
    "SELECT set_config('app.organisation_id', %s, false),"
    " set_config('app.user_id', %s, false),"
    " set_config('app.is_system', %s, false)"
)


def apply_database_scope(
    *, user_id: UUID | None, organisation_id: UUID | None = None, is_system: bool = False
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            _SCOPE_SQL,
            [_as_setting(organisation_id), _as_setting(user_id), "on" if is_system else "off"],
        )


def clear_database_scope() -> None:
    if connection.connection is not None:
        apply_database_scope(user_id=None)


def _as_setting(value: UUID | None) -> str:
    return "" if value is None else str(value)
