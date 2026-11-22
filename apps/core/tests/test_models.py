import uuid

from apps.core.models import BaseModel, TimeStampedModel, UUIDPrimaryKeyModel


def test_base_model_combines_uuid_primary_key_and_timestamps() -> None:
    assert issubclass(BaseModel, UUIDPrimaryKeyModel)
    assert issubclass(BaseModel, TimeStampedModel)
    assert BaseModel._meta.abstract


def test_primary_key_defaults_to_uuid_version_seven() -> None:
    primary_key = UUIDPrimaryKeyModel._meta.get_field("id")

    generated = primary_key.get_default()

    assert isinstance(generated, uuid.UUID)
    assert generated.version == 7
    assert not primary_key.editable


def test_primary_keys_are_time_ordered() -> None:
    primary_key = UUIDPrimaryKeyModel._meta.get_field("id")

    generated = [primary_key.get_default() for _ in range(50)]

    assert generated == sorted(generated)
