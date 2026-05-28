from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from propylon_document_manager.file_versions.api.views import (
    DocumentRetrieveView,
    EmailObtainAuthToken,
    RegisterView,
)

urlpatterns = [
    # Auth
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", EmailObtainAuthToken.as_view(), name="login"),

    # File versions API
    path("api/", include("propylon_document_manager.site.api_router")),

    # Document retrieval
    path("api/documents/<path:file_url>", DocumentRetrieveView.as_view(), name="document-retrieve"),

    # DRF auth token
    path("api-auth/", include("rest_framework.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
