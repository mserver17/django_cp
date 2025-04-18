# conf/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf.urls.static import static
from django.conf import settings
from beauty_salon.views import router   # Импорт роутера из приложения

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/beauty_salon/', include('beauty_salon.urls')),
    path('api/v1/accounts/', include('django.contrib.auth.urls')),
    path('api/v1', include(router.urls)),  # API-маршруты
    path('', RedirectView.as_view(url='beauty_salon/')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)