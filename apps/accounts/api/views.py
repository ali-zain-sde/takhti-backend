from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.api.request import current_user
from apps.accounts.api.serializers import LoginSerializer, SessionUserSerializer
from apps.accounts.selectors import session_user
from apps.core.api.serializers import ErrorResponseSerializer
from apps.core.permissions import RequiresCsrfToken
from apps.tenancy.database import transaction_database_scope


class CsrfTokenView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(operation_id="auth_csrf", responses={204: None}, tags=["auth"])
    def get(self, request: Request) -> Response:
        get_token(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    permission_classes = (RequiresCsrfToken,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "login"

    @extend_schema(
        operation_id="auth_login",
        request=LoginSerializer,
        responses={
            200: SessionUserSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
        },
        tags=["auth"],
    )
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request._request,
            phone=serializer.validated_data["phone"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            raise AuthenticationFailed(
                _("Incorrect phone number or password."), code="invalid_credentials"
            )
        login(request._request, user)
        with transaction_database_scope(user_id=user.pk):
            payload = SessionUserSerializer(session_user(user_id=user.pk)).data
        return Response(payload)


class LogoutView(APIView):
    @extend_schema(
        operation_id="auth_logout",
        request=None,
        responses={204: None, 401: ErrorResponseSerializer, 403: ErrorResponseSerializer},
        tags=["auth"],
    )
    def post(self, request: Request) -> Response:
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    @extend_schema(
        operation_id="auth_me",
        responses={200: SessionUserSerializer, 401: ErrorResponseSerializer},
        tags=["auth"],
    )
    def get(self, request: Request) -> Response:
        return Response(SessionUserSerializer(session_user(user_id=current_user(request).pk)).data)
