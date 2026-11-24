from rest_framework import serializers


class HealthSerializer(serializers.Serializer[dict[str, str]]):
    status = serializers.ChoiceField(choices=["ok", "degraded"])
    database = serializers.ChoiceField(choices=["ok", "unavailable"])


class ErrorSerializer(serializers.Serializer[dict[str, object]]):
    code = serializers.CharField()
    message = serializers.CharField()
    field_errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), required=False
    )


class ErrorResponseSerializer(serializers.Serializer[dict[str, object]]):
    error = ErrorSerializer()
