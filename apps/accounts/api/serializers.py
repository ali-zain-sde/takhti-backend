from rest_framework import serializers

from apps.accounts.models import Membership, User
from apps.tenancy.models import Campus, Organisation


class LoginSerializer(serializers.Serializer[dict[str, str]]):
    phone = serializers.CharField(max_length=32)
    password = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
        style={"input_type": "password"},
    )


class OrganisationSummarySerializer(serializers.ModelSerializer[Organisation]):
    class Meta:
        model = Organisation
        fields = ("id", "name", "slug")
        read_only_fields = fields


class CampusSummarySerializer(serializers.ModelSerializer[Campus]):
    class Meta:
        model = Campus
        fields = ("id", "name", "slug")
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer[Membership]):
    organisation = OrganisationSummarySerializer(read_only=True)
    campus = CampusSummarySerializer(read_only=True, allow_null=True)

    class Meta:
        model = Membership
        fields = ("id", "role", "organisation", "campus")
        read_only_fields = fields


class SessionUserSerializer(serializers.ModelSerializer[User]):
    memberships = MembershipSerializer(many=True, read_only=True, source="active_memberships")

    class Meta:
        model = User
        fields = ("id", "phone", "full_name", "email", "memberships")
        read_only_fields = fields
