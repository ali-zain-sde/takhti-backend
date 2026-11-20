from rest_framework import serializers


class HealthSerializer(serializers.Serializer[dict[str, str]]):
    status = serializers.ChoiceField(choices=["ok", "degraded"])
    database = serializers.ChoiceField(choices=["ok", "unavailable"])
