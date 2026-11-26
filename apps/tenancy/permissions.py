from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.tenancy.context import Tenant
from apps.tenancy.exceptions import TenantRequired
from apps.tenancy.resolution import request_resolution


def require_tenant(request: Request) -> Tenant:
    resolution = request_resolution(request)
    if resolution.error is not None:
        raise resolution.error
    if resolution.tenant is None:
        raise TenantRequired
    return resolution.tenant


class RequiresTenant(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user.is_authenticated:
            return False
        require_tenant(request)
        return True
