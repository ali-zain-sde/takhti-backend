import pytest
from django.core.exceptions import ValidationError

from apps.core.fields import PakistaniMobileField
from apps.core.phone import normalize_pakistani_mobile


@pytest.mark.parametrize(
    "raw",
    [
        "03001234567",
        "0300 1234567",
        "0300-123-4567",
        "+92 300 1234567",
        "+923001234567",
        "923001234567",
        "00923001234567",
        "(0300) 1234567",
    ],
)
def test_normalizes_common_spellings_to_e164(raw: str) -> None:
    assert normalize_pakistani_mobile(raw) == "+923001234567"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "0300123456",
        "030012345678",
        "0423571234",
        "+14155550123",
        "0300abc4567",
        "+92 400 1234567",
    ],
)
def test_rejects_non_mobile_or_malformed_numbers(raw: str) -> None:
    with pytest.raises(ValidationError) as error:
        normalize_pakistani_mobile(raw)

    assert error.value.code == "invalid_phone"


def test_field_normalizes_during_cleaning() -> None:
    field = PakistaniMobileField()

    assert field.to_python(" 0321-7654321 ") == "+923217654321"


def test_field_leaves_empty_values_to_blank_validation() -> None:
    field = PakistaniMobileField(blank=True)

    assert field.to_python("") == ""
    assert field.to_python(None) is None
