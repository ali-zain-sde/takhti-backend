from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Tenant:
    organisation_id: UUID
    campus_id: UUID | None = None
    roles: frozenset[str] = frozenset()


_current_tenant: ContextVar[Tenant | None] = ContextVar("current_tenant", default=None)


def current_tenant() -> Tenant | None:
    return _current_tenant.get()


@contextmanager
def tenant_context(tenant: Tenant | None) -> Iterator[Tenant | None]:
    token = _current_tenant.set(tenant)
    try:
        yield tenant
    finally:
        _current_tenant.reset(token)
