from typing import ClassVar

from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.accounts.models import Role, User
from apps.accounts.selectors import active_memberships


class HasRole(BasePermission):
    allowed_roles: ClassVar[frozenset[Role]] = frozenset()
    message = _("Your role does not allow this action.")
    code = "role_required"

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not isinstance(user, User) or not self.allowed_roles:
            return False
        return active_memberships().filter(user=user, role__in=self.allowed_roles).exists()


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
