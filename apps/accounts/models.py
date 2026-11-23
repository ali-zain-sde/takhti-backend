from typing import ClassVar

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager
from apps.core.fields import PakistaniMobileField
from apps.core.models import BaseModel
from apps.core.phone import PAKISTANI_MOBILE_PATTERN
from apps.tenancy.models import Campus, Organisation


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


class Role(models.TextChoices):
    OWNER = "owner", _("Owner")
    ADMIN = "admin", _("Admin")
    ACCOUNTANT = "accountant", _("Accountant")
    TEACHER = "teacher", _("Teacher")


class Membership(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="memberships", verbose_name=_("user")
    )
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name="memberships",
        verbose_name=_("organisation"),
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.PROTECT,
        related_name="memberships",
        null=True,
        blank=True,
        verbose_name=_("campus"),
    )
    role = models.CharField(_("role"), max_length=16, choices=Role.choices)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("membership")
        verbose_name_plural = _("memberships")
        ordering = ("created_at",)
        constraints = (
            models.UniqueConstraint(
                fields=("user", "organisation", "campus"),
                nulls_distinct=False,
                name="accounts_membership_unique_scope",
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=Role.values),
                name="accounts_membership_role_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(role=Role.OWNER) | models.Q(campus__isnull=True),
                name="accounts_membership_owner_is_organisation_wide",
            ),
        )

    def __str__(self) -> str:
        return f"{self.user} · {self.get_role_display()}"

    def clean(self) -> None:
        if self.campus is not None and self.campus.organisation_id != self.organisation_id:
            raise ValidationError(
                {"campus": _("The campus must belong to the membership's organisation.")},
                code="campus_outside_organisation",
            )
        if self.role == Role.OWNER and self.campus is not None:
            raise ValidationError(
                {"campus": _("Owners have access to the whole organisation.")},
                code="owner_scoped_to_campus",
            )
