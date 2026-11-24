from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.openapi import AutoSchema


class SessionAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.core.authentication.SessionAuthentication"
    name = "sessionAuth"

    def get_security_definition(self, auto_schema: AutoSchema) -> dict[str, str]:
        return {"type": "apiKey", "in": "cookie", "name": settings.SESSION_COOKIE_NAME}
