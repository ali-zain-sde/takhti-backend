from django.urls import include, path

urlpatterns = [
    path("", include("apps.core.api.urls")),
    path("", include("apps.accounts.api.urls")),
]
