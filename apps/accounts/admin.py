from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.forms import UserChangeForm, UserCreationForm
from apps.accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin[User]):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ("full_name", "phone", "email", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("full_name", "phone", "email")
    ordering = ("full_name",)
    readonly_fields = ("last_login", "created_at", "updated_at")
    filter_horizontal = ("groups", "user_permissions")
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (_("Profile"), {"fields": ("full_name", "email")}),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Activity"), {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "full_name", "usable_password", "password1", "password2"),
            },
        ),
    )
