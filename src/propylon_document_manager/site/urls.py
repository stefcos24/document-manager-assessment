from django.conf import settings
from django.urls import include, path

from propylon_document_manager.file_versions.api.views import (
    EmailObtainAuthToken,
    RegisterView,
)

# API URLS
urlpatterns = [
    # Auth
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", EmailObtainAuthToken.as_view(), name="login"),

    # API base url
    path("api/", include("propylon_document_manager.site.api_router")),

    # DRF auth token
    path("api-auth/", include("rest_framework.urls")),
]

if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
