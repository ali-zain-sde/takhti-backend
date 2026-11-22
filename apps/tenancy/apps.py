from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TenancyConfig(AppConfig):
    name = "apps.tenancy"
    label = "tenancy"
    verbose_name = _("Tenancy")
