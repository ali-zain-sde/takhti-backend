import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

PAKISTANI_MOBILE_PATTERN = r"^\+923[0-9]{9}$"

_SEPARATORS = re.compile(r"[\s\-().]")
_NATIONAL_PREFIXES = ("+92", "0092", "92", "0")


def normalize_pakistani_mobile(value: str) -> str:
    digits = _SEPARATORS.sub("", value)
    for prefix in _NATIONAL_PREFIXES:
        if digits.startswith(prefix):
            candidate = f"+92{digits.removeprefix(prefix)}"
            if re.fullmatch(PAKISTANI_MOBILE_PATTERN, candidate):
                return candidate
    raise ValidationError(
        _("Enter a valid Pakistani mobile number, for example 0300 1234567."),
        code="invalid_phone",
    )
