from typing import ClassVar

from django.utils.translation import gettext_lazy as _
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.tenancy.permissions import RequiresTenant, require_tenant


class HasRole(RequiresTenant):
    allowed_roles: ClassVar[frozenset[Role]] = frozenset()
    message = _("Your role does not allow this action.")
    code = "role_required"

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not super().has_permission(request, view):
            return False
        return bool(require_tenant(request).roles & self.allowed_roles)


class IsMember(HasRole):
    allowed_roles = frozenset(Role)


class IsOwner(HasRole):
    allowed_roles = frozenset({Role.OWNER})


class CanManageSchool(HasRole):
    allowed_roles = frozenset({Role.OWNER, Role.ADMIN})


class CanManageFinance(HasRole):
    allowed_roles = frozenset({Role.OWNER, Role.ADMIN, Role.ACCOUNTANT})


class CanRecordAcademics(HasRole):
    allowed_roles = frozenset({Role.OWNER, Role.ADMIN, Role.TEACHER})
