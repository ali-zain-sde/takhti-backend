from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError

from apps.core.phone import normalize_pakistani_mobile

if TYPE_CHECKING:
    from apps.accounts.models import User


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def get_by_natural_key(self, username: str | None) -> User:
        return self.get(phone=self._lookup_phone(username))

    async def aget_by_natural_key(self, username: str | None) -> User:
        return await self.aget(phone=self._lookup_phone(username))

    def create_user(self, phone: str, password: str | None = None, **extra_fields: Any) -> User:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone=phone, password=password, **extra_fields)

    def create_superuser(
        self, phone: str, password: str | None = None, **extra_fields: Any
    ) -> User:
        extra_fields.update(is_staff=True, is_superuser=True)
        return self._create_user(phone=phone, password=password, **extra_fields)

    def _create_user(self, *, phone: str, password: str | None, **extra_fields: Any) -> User:
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def _lookup_phone(self, username: str | None) -> str:
        try:
            return normalize_pakistani_mobile(username or "")
        except ValidationError as error:
            raise self.model.DoesNotExist from error
