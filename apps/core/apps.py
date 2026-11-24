from importlib import import_module

from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    label = "core"

    def ready(self) -> None:
        import_module("apps.core.api.schema")
