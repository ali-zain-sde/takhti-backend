from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status


class TenantRequired(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Choose an organisation to continue.")
    default_code = "organisation_required"


class TenantForbidden(exceptions.PermissionDenied):
    default_detail = _("You do not have access to this organisation.")
    default_code = "organisation_forbidden"
