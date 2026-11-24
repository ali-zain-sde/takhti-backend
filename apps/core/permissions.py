from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.authentication import SessionAuthentication


class RequiresCsrfToken(BasePermission):
    message = _("Your session form expired. Refresh the page and try again.")
    code = "csrf_failed"

    def has_permission(self, request: Request, view: APIView) -> bool:
        try:
            SessionAuthentication().enforce_csrf(request)
        except exceptions.PermissionDenied as error:
            raise exceptions.PermissionDenied(self.message, code=self.code) from error
        return True
