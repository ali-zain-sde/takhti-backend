import pytest
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status

from apps.core.api.exceptions import api_exception_handler


def handle(exc: Exception) -> tuple[int, object]:
    response = api_exception_handler(exc, {})
    assert response is not None
    return response.status_code, response.data


def test_serializer_validation_errors_are_reported_per_field() -> None:
    status_code, body = handle(
        exceptions.ValidationError(
            {"phone": ["Enter a valid number."], "non_field_errors": ["Mismatch."]}
        )
    )

    assert status_code == status.HTTP_400_BAD_REQUEST
    assert body == {
        "error": {
            "code": "validation_error",
            "message": "Some fields need attention.",
            "field_errors": {"phone": ["Enter a valid number."], "non_field_errors": ["Mismatch."]},
        }
    }


def test_nested_validation_errors_use_dotted_paths() -> None:
    _, body = handle(exceptions.ValidationError({"guardians": [{"phone": ["Required."]}, {}]}))

    assert body == {
        "error": {
            "code": "validation_error",
            "message": "Some fields need attention.",
            "field_errors": {"guardians.0.phone": ["Required."]},
        }
    }


def test_django_validation_errors_from_services_become_bad_requests() -> None:
    status_code, body = handle(
        DjangoValidationError({"slug": ["Already taken."]}, code="duplicate")
    )

    assert status_code == status.HTTP_400_BAD_REQUEST
    assert body == {
        "error": {
            "code": "validation_error",
            "message": "Some fields need attention.",
            "field_errors": {"slug": ["Already taken."]},
        }
    }


def test_django_validation_errors_without_fields_are_non_field_errors() -> None:
    _, body = handle(DjangoValidationError("Organisation is inactive."))

    assert body == {
        "error": {
            "code": "validation_error",
            "message": "Some fields need attention.",
            "field_errors": {"non_field_errors": ["Organisation is inactive."]},
        }
    }


@pytest.mark.parametrize(
    ("exc", "expected_status", "expected_code"),
    [
        (exceptions.NotAuthenticated(), status.HTTP_401_UNAUTHORIZED, "not_authenticated"),
        (exceptions.PermissionDenied(), status.HTTP_403_FORBIDDEN, "permission_denied"),
        (Http404(), status.HTTP_404_NOT_FOUND, "not_found"),
        (DjangoPermissionDenied(), status.HTTP_403_FORBIDDEN, "permission_denied"),
        (exceptions.Throttled(wait=30), status.HTTP_429_TOO_MANY_REQUESTS, "throttled"),
    ],
)
def test_api_exceptions_share_one_envelope(
    exc: Exception, expected_status: int, expected_code: str
) -> None:
    status_code, body = handle(exc)

    assert status_code == expected_status
    assert isinstance(body, dict)
    assert body["error"]["code"] == expected_code
    assert body["error"]["message"]


def test_custom_codes_on_api_exceptions_are_preserved() -> None:
    _, body = handle(exceptions.AuthenticationFailed("Wrong password.", code="invalid_credentials"))

    assert body == {"error": {"code": "invalid_credentials", "message": "Wrong password."}}


def test_unhandled_exceptions_are_left_to_django() -> None:
    assert api_exception_handler(RuntimeError("boom"), {}) is None
