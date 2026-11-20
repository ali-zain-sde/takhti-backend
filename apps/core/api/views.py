from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.serializers import HealthSerializer
from apps.core.selectors import database_is_available


class HealthView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(
        operation_id="health_retrieve",
        responses={200: HealthSerializer, 503: HealthSerializer},
        tags=["health"],
    )
    def get(self, request: Request) -> Response:
        database_ok = database_is_available()
        payload = HealthSerializer(
            {
                "status": "ok" if database_ok else "degraded",
                "database": "ok" if database_ok else "unavailable",
            }
        ).data
        return Response(
            payload,
            status=status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
