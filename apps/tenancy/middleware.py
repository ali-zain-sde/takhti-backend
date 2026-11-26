from collections.abc import Callable
from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from rest_framework.exceptions import APIException

from apps.tenancy.context import tenant_context
from apps.tenancy.database import apply_database_scope, clear_database_scope
from apps.tenancy.resolution import (
    CAMPUS_HEADER,
    ORGANISATION_HEADER,
    UNRESOLVED,
    TenantResolution,
    attach_resolution,
    resolve_tenant,
)


class TenantMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        attach_resolution(request, UNRESOLVED)
        user = request.user
        if not user.is_authenticated:
            return self.get_response(request)
        is_system = user.is_staff and request.path.startswith(reverse("admin:index"))
        apply_database_scope(user_id=user.pk, is_system=is_system)
        try:
            resolution = UNRESOLVED if is_system else self._resolve(request, user.pk)
            attach_resolution(request, resolution)
            if resolution.tenant is not None:
                apply_database_scope(
                    user_id=user.pk, organisation_id=resolution.tenant.organisation_id
                )
            with tenant_context(resolution.tenant):
                return self.get_response(request)
        finally:
            clear_database_scope()

    def _resolve(self, request: HttpRequest, user_id: UUID) -> TenantResolution:
        try:
            tenant = resolve_tenant(
                user_id=user_id,
                organisation_header=request.headers.get(ORGANISATION_HEADER),
                campus_header=request.headers.get(CAMPUS_HEADER),
            )
        except APIException as error:
            return TenantResolution(error=error)
        return TenantResolution(tenant=tenant)
