from collections.abc import Mapping, Sequence
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler

FieldErrors = dict[str, list[str]]


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(_as_api_exception(exc), context)
    if response is None:
        return None
    response.data = {"error": _error_body(_as_api_exception(exc))}
    return response


def _as_api_exception(exc: Exception) -> Exception:
    if isinstance(exc, DjangoValidationError):
        return exceptions.ValidationError(as_serializer_error(exc))
    if isinstance(exc, Http404):
        return exceptions.NotFound()
    if isinstance(exc, DjangoPermissionDenied):
        return exceptions.PermissionDenied()
    return exc


def _error_body(exc: Exception) -> dict[str, object]:
    if isinstance(exc, exceptions.ValidationError):
        return {
            "code": "validation_error",
            "message": str(_("Some fields need attention.")),
            "field_errors": _flatten(exc.detail),
        }
    if isinstance(exc, exceptions.APIException):
        detail = exc.detail
        return {
            "code": getattr(detail, "code", None) or exc.default_code,
            "message": str(detail),
        }
    return {"code": "error", "message": str(exc)}


def _flatten(detail: object, prefix: str = "") -> FieldErrors:
    key = prefix or "non_field_errors"
    if isinstance(detail, Mapping):
        errors: FieldErrors = {}
        for field, nested in detail.items():
            errors.update(_flatten(nested, f"{prefix}.{field}" if prefix else str(field)))
        return errors
    if isinstance(detail, Sequence) and not isinstance(detail, str):
        if all(isinstance(item, str) for item in detail):
            return {key: [str(item) for item in detail]}
        errors = {}
        for index, nested in enumerate(detail):
            errors.update(_flatten(nested, f"{prefix}.{index}" if prefix else str(index)))
        return errors
    return {key: [str(detail)]}
