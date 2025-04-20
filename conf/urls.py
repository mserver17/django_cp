# conf/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from django.conf import settings
from beauty_salon.views import router   # Импорт роутера из приложения
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('beauty_salon/', include('beauty_salon.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/v1/', include(router.urls)),  # API-маршруты
    # path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', RedirectView.as_view(url='beauty_salon/')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)