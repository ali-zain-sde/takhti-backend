from typing import Any

from django.db import models

from apps.core.phone import normalize_pakistani_mobile


class PakistaniMobileField(models.CharField[str, str]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("max_length", 13)
        super().__init__(*args, **kwargs)

    def to_python(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value)
        if not text:
            return text
        return normalize_pakistani_mobile(text)
