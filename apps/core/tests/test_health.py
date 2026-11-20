from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

HEALTH_URL = reverse("core:health")


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
def test_health_reports_ok_when_database_is_reachable(api_client: APIClient) -> None:
    response = api_client.get(HEALTH_URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.django_db
def test_health_reports_degraded_when_database_is_unreachable(api_client: APIClient) -> None:
    with patch("apps.core.api.views.database_is_available", return_value=False):
        response = api_client.get(HEALTH_URL)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"status": "degraded", "database": "unavailable"}


def test_health_does_not_require_authentication(api_client: APIClient) -> None:
    with patch("apps.core.api.views.database_is_available", return_value=True):
        response = api_client.get(HEALTH_URL)

    assert response.status_code == status.HTTP_200_OK
