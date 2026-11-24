from django.urls import path

from apps.accounts.api.views import CsrfTokenView, LoginView, LogoutView, MeView

app_name = "auth"

urlpatterns = [
    path("auth/csrf/", CsrfTokenView.as_view(), name="csrf"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
]
