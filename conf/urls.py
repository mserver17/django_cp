from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView

from beauty_salon.views import (
    CurrentUserView,
    EmailTokenObtainPairView,
    RegisterAPIView,
    router,
)

schema_view = get_schema_view(
    openapi.Info(
        title="Beauty Salon API",
        default_version="v1",
        description="API documentation for Beauty Salon",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@salon.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("beauty_salon/", include("beauty_salon.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/v1/", include(router.urls)),  # API‑маршруты
    path(
        "api/v1/drf-auth/",
        include("rest_framework.urls"),
    ),
    path("", RedirectView.as_view(url="beauty_salon/")),
    path("api/v1/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/auth/register/", RegisterAPIView.as_view(), name="api_register"),
    path("api/v1/users/me/", CurrentUserView.as_view(), name="api_current_user"),
    # Swagger URLs
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
