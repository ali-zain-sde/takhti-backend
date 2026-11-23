from django.contrib.auth import forms as auth_forms

from apps.accounts.models import User


class UserCreationForm(auth_forms.AdminUserCreationForm[User]):
    class Meta:
        model = User
        fields = ("phone", "full_name")


class UserChangeForm(auth_forms.UserChangeForm[User]):
    class Meta:
        model = User
        fields = (
            "phone",
            "password",
            "full_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
