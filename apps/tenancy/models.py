from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"

slug_validator = RegexValidator(
    regex=SLUG_PATTERN,
    message=_("Use lowercase letters, numbers and single hyphens only."),
)


class Province(models.TextChoices):
    PUNJAB = "punjab", _("Punjab")
    SINDH = "sindh", _("Sindh")
    KHYBER_PAKHTUNKHWA = "khyber_pakhtunkhwa", _("Khyber Pakhtunkhwa")
    BALOCHISTAN = "balochistan", _("Balochistan")
    ISLAMABAD = "islamabad", _("Islamabad Capital Territory")
    GILGIT_BALTISTAN = "gilgit_baltistan", _("Gilgit-Baltistan")
    AZAD_KASHMIR = "azad_kashmir", _("Azad Jammu and Kashmir")


class Organisation(BaseModel):
    name = models.CharField(_("name"), max_length=150)
    slug = models.SlugField(_("slug"), max_length=60, unique=True, validators=[slug_validator])
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("organisation")
        verbose_name_plural = _("organisations")
        ordering = ("name",)
        constraints = (
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="tenancy_organisation_name_not_blank",
            ),
            models.CheckConstraint(
                condition=models.Q(slug__regex=SLUG_PATTERN),
                name="tenancy_organisation_slug_format",
            ),
        )

    def __str__(self) -> str:
        return self.name


class Campus(BaseModel):
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name="campuses",
        verbose_name=_("organisation"),
    )
    name = models.CharField(_("name"), max_length=150)
    slug = models.SlugField(_("slug"), max_length=60, validators=[slug_validator])
    province = models.CharField(_("province"), max_length=32, choices=Province.choices)
    city = models.CharField(_("city"), max_length=80)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("campus")
        verbose_name_plural = _("campuses")
        ordering = ("organisation", "name")
        constraints = (
            models.UniqueConstraint(
                fields=("organisation", "slug"),
                name="tenancy_campus_unique_slug_per_organisation",
            ),
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="tenancy_campus_name_not_blank",
            ),
            models.CheckConstraint(
                condition=models.Q(slug__regex=SLUG_PATTERN),
                name="tenancy_campus_slug_format",
            ),
            models.CheckConstraint(
                condition=models.Q(province__in=Province.values),
                name="tenancy_campus_province_valid",
            ),
        )

    def __str__(self) -> str:
        return f"{self.organisation.name} · {self.name}"
