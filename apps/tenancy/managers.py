from django.db import models

from apps.tenancy.context import current_tenant


class TenantManager[ModelT: models.Model](models.Manager[ModelT]):
    def __init__(self, *, tenant_field: str) -> None:
        super().__init__()
        self.tenant_field = tenant_field

    def get_queryset(self) -> models.QuerySet[ModelT]:
        queryset = super().get_queryset()
        tenant = current_tenant()
        if tenant is None:
            return queryset.none()
        return queryset.filter(**{self.tenant_field: tenant.organisation_id})
