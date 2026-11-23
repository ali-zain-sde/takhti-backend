from typing import ClassVar

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager
from apps.core.fields import PakistaniMobileField
from apps.core.models import BaseModel
from apps.core.phone import PAKISTANI_MOBILE_PATTERN


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    phone = PakistaniMobileField(_("phone"), unique=True)
    full_name = models.CharField(_("full name"), max_length=150)
    email = models.EmailField(_("email"), blank=True)
    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = ["full_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("full_name",)
        constraints = (
            models.CheckConstraint(
                condition=models.Q(phone__regex=PAKISTANI_MOBILE_PATTERN),
                name="accounts_user_phone_format",
            ),
            models.CheckConstraint(
                condition=~models.Q(full_name=""),
                name="accounts_user_full_name_not_blank",
            ),
        )

    def __str__(self) -> str:
        return self.full_name
